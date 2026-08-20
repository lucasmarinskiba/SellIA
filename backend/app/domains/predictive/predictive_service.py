"""Predictive analytics service — forecasting + demand + churn prediction."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional
from decimal import Decimal
from statistics import mean, stdev

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.predictive.predictive_models import (
    ChurnPrediction, PurchaseTimingPrediction, DemandForecast,
    RevenueForecast, PredictionAccuracy, PredictionHorizon
)

logger = logging.getLogger(__name__)


class PredictiveAnalyticsService:
    """Forecast demand, churn, revenue, purchase timing."""

    @staticmethod
    def predict_churn(
        business_id: UUID,
        customer_id: UUID,
        days_since_purchase: int,
        purchase_frequency: Decimal,
        engagement_score: Decimal,
        db: Session = None
    ) -> dict:
        """Predict customer churn probability."""
        if not db:
            raise ValueError("Database session required")

        from app.domains.customers.models import Customer

        customer = db.query(Customer).filter(Customer.id == customer_id).first()
        if not customer:
            raise ValueError(f"Customer {customer_id} not found")

        # Churn model (simplified logistic)
        churn_7d = Decimal("0")
        churn_30d = Decimal("0")
        churn_90d = Decimal("0")

        # Days since purchase contributes to churn risk
        if days_since_purchase > 180:
            churn_7d += Decimal("25")
            churn_30d += Decimal("45")
            churn_90d += Decimal("65")
        elif days_since_purchase > 90:
            churn_7d += Decimal("15")
            churn_30d += Decimal("30")
            churn_90d += Decimal("50")
        elif days_since_purchase > 30:
            churn_7d += Decimal("5")
            churn_30d += Decimal("15")
            churn_90d += Decimal("25")

        # Engagement score (inverse relationship)
        engagement_factor = float(engagement_score or 5) / 10
        churn_7d -= Decimal(str(engagement_factor * 15))
        churn_30d -= Decimal(str(engagement_factor * 25))
        churn_90d -= Decimal(str(engagement_factor * 35))

        # Purchase frequency (higher = lower churn)
        if float(purchase_frequency) > 2:
            churn_7d -= Decimal("20")
            churn_30d -= Decimal("30")
            churn_90d -= Decimal("40")
        elif float(purchase_frequency) < 0.5:
            churn_7d += Decimal("15")
            churn_30d += Decimal("25")
            churn_90d += Decimal("35")

        # Clamp to 0-100
        churn_7d = max(Decimal("0"), min(Decimal("100"), churn_7d))
        churn_30d = max(Decimal("0"), min(Decimal("100"), churn_30d))
        churn_90d = max(Decimal("0"), min(Decimal("100"), churn_90d))

        # Determine primary driver
        if days_since_purchase > 180:
            primary_driver = "no_purchase_180d"
        elif float(engagement_score or 0) < 3:
            primary_driver = "low_engagement"
        else:
            primary_driver = "declining_frequency"

        # Create or update prediction
        prediction = db.query(ChurnPrediction).filter(
            ChurnPrediction.customer_id == customer_id
        ).first()

        if prediction:
            prediction.churn_probability_7d = churn_7d
            prediction.churn_probability_30d = churn_30d
            prediction.churn_probability_90d = churn_90d
            prediction.primary_churn_driver = primary_driver
            prediction.last_prediction_date = datetime.now(timezone.utc)
        else:
            prediction = ChurnPrediction(
                business_id=business_id,
                customer_id=customer_id,
                churn_probability_7d=churn_7d,
                churn_probability_30d=churn_30d,
                churn_probability_90d=churn_90d,
                primary_churn_driver=primary_driver
            )
            db.add(prediction)

        db.commit()

        logger.info(f"Churn predicted: {customer_id} - 30d={churn_30d}%")

        return {
            "customer_id": str(customer_id),
            "churn_probability_7d": float(churn_7d),
            "churn_probability_30d": float(churn_30d),
            "churn_probability_90d": float(churn_90d),
            "primary_driver": primary_driver
        }

    @staticmethod
    def predict_purchase_timing(
        business_id: UUID,
        customer_id: UUID,
        avg_purchase_interval: int,
        last_purchase_date: datetime,
        db: Session = None
    ) -> dict:
        """Predict next purchase timing."""
        if not db:
            raise ValueError("Database session required")

        # Simple model: next purchase = last_purchase + avg_interval
        # Add normal distribution around average

        # Base prediction
        days_until = max(1, avg_purchase_interval)
        predicted_date = (last_purchase_date + timedelta(days=days_until)).strftime("%Y-%m-%d")

        # Purchase probability (sigmoid)
        prob_7d = Decimal(str(min(95, max(5, days_until / 5))))  # Scale to 5-95%
        prob_30d = Decimal(str(min(99, max(20, days_until / 2))))

        # Expected order value (use historical average or segment average)
        predicted_aov = Decimal("100")  # Placeholder

        prediction = db.query(PurchaseTimingPrediction).filter(
            PurchaseTimingPrediction.customer_id == customer_id
        ).first()

        if prediction:
            prediction.days_until_next_purchase = days_until
            prediction.predicted_purchase_date = predicted_date
            prediction.purchase_probability_7d = prob_7d
            prediction.purchase_probability_30d = prob_30d
            prediction.predicted_order_value = predicted_aov
            prediction.last_prediction_date = datetime.now(timezone.utc)
        else:
            prediction = PurchaseTimingPrediction(
                business_id=business_id,
                customer_id=customer_id,
                days_until_next_purchase=days_until,
                predicted_purchase_date=predicted_date,
                purchase_probability_7d=prob_7d,
                purchase_probability_30d=prob_30d,
                predicted_order_value=predicted_aov
            )
            db.add(prediction)

        db.commit()

        logger.info(f"Purchase timing predicted: {customer_id} - {days_until} days")

        return {
            "customer_id": str(customer_id),
            "days_until_next_purchase": days_until,
            "predicted_purchase_date": predicted_date,
            "purchase_probability_7d": float(prob_7d),
            "purchase_probability_30d": float(prob_30d),
            "predicted_order_value": float(predicted_aov)
        }

    @staticmethod
    def forecast_demand(
        business_id: UUID,
        product_category: str,
        historical_units: list,
        forecast_days: int = 30,
        db: Session = None
    ) -> dict:
        """Forecast product demand."""
        if not db:
            raise ValueError("Database session required")

        # Simple moving average + trend
        if not historical_units or len(historical_units) < 2:
            return {"forecast_available": False}

        avg_units = Decimal(str(mean(historical_units)))
        trend = (historical_units[-1] - historical_units[0]) / max(len(historical_units), 1)

        # Forecast = average + (trend * days_ahead)
        forecasted_units = int(avg_units + (trend * forecast_days / 30))
        forecasted_units = max(0, forecasted_units)

        start_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        end_date = (datetime.now(timezone.utc) + timedelta(days=forecast_days)).strftime("%Y-%m-%d")

        # Confidence interval (±20%)
        ci_low = Decimal(str(round(forecasted_units * 0.8, 2)))
        ci_high = Decimal(str(round(forecasted_units * 1.2, 2)))

        forecast = DemandForecast(
            business_id=business_id,
            product_category=product_category,
            forecast_start_date=start_date,
            forecast_end_date=end_date,
            forecasted_units=forecasted_units,
            forecasted_revenue=Decimal(str(forecasted_units * 100)),  # Placeholder $100/unit
            confidence_interval_low=ci_low * 100,
            confidence_interval_high=ci_high * 100
        )

        db.add(forecast)
        db.commit()

        logger.info(f"Demand forecasted: {product_category} - {forecasted_units} units")

        return {
            "forecast_available": True,
            "product_category": product_category,
            "forecast_period": f"{start_date} to {end_date}",
            "forecasted_units": forecasted_units,
            "forecasted_revenue": float(forecasted_units * 100),
            "confidence_low": float(ci_low * 100),
            "confidence_high": float(ci_high * 100)
        }

    @staticmethod
    def forecast_revenue(
        business_id: UUID,
        historical_revenue: list,
        new_customer_ratio: Decimal = Decimal("0.3"),
        forecast_horizon: str = "next_30_days",
        db: Session = None
    ) -> dict:
        """Forecast business revenue."""
        if not db:
            raise ValueError("Database session required")

        if not historical_revenue or len(historical_revenue) < 2:
            return {"forecast_available": False}

        avg_revenue = Decimal(str(mean(historical_revenue)))
        trend = (Decimal(str(historical_revenue[-1])) - Decimal(str(historical_revenue[0]))) / max(len(historical_revenue), 1)

        # Forecast = average + (trend component)
        forecasted_revenue = avg_revenue + (trend * Decimal("0.5"))

        # Split new vs repeat
        new_customer_revenue = forecasted_revenue * new_customer_ratio
        repeat_customer_revenue = forecasted_revenue * (Decimal("1") - new_customer_ratio)

        start_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        horizon_days = {"next_7_days": 7, "next_30_days": 30, "next_90_days": 90, "next_365_days": 365}.get(forecast_horizon, 30)
        end_date = (datetime.now(timezone.utc) + timedelta(days=horizon_days)).strftime("%Y-%m-%d")

        # Confidence intervals
        ci_low = forecasted_revenue * Decimal("0.85")
        ci_high = forecasted_revenue * Decimal("1.15")

        forecast = RevenueForecast(
            business_id=business_id,
            forecast_start_date=start_date,
            forecast_end_date=end_date,
            forecast_horizon=PredictionHorizon[forecast_horizon.upper()],
            forecasted_revenue=forecasted_revenue,
            new_customer_revenue=new_customer_revenue,
            repeat_customer_revenue=repeat_customer_revenue,
            confidence_interval_low=ci_low,
            confidence_interval_high=ci_high
        )

        db.add(forecast)
        db.commit()

        logger.info(f"Revenue forecasted: {business_id} - ${forecasted_revenue}")

        return {
            "forecast_available": True,
            "forecast_period": f"{start_date} to {end_date}",
            "forecasted_revenue": float(forecasted_revenue),
            "new_customer_revenue": float(new_customer_revenue),
            "repeat_customer_revenue": float(repeat_customer_revenue),
            "confidence_low": float(ci_low),
            "confidence_high": float(ci_high)
        }

    @staticmethod
    def evaluate_prediction_accuracy(
        business_id: UUID,
        prediction_type: str,
        predictions: list,
        actuals: list,
        db: Session = None
    ) -> dict:
        """Evaluate model accuracy (MAE, RMSE, R²)."""
        if not db:
            raise ValueError("Database session required")

        if len(predictions) != len(actuals):
            return {"evaluation_available": False}

        # MAE
        mae = Decimal(str(mean(abs(p - a) for p, a in zip(predictions, actuals))))

        # RMSE
        rmse = Decimal(str((sum((p - a) ** 2 for p, a in zip(predictions, actuals)) / len(predictions)) ** 0.5))

        # R²
        ss_res = sum((p - a) ** 2 for p, a in zip(predictions, actuals))
        ss_tot = sum((a - mean(actuals)) ** 2 for a in actuals)
        r_squared = Decimal(str(1 - (ss_res / ss_tot))) if ss_tot > 0 else Decimal("0")

        accuracy = PredictionAccuracy(
            business_id=business_id,
            prediction_type=prediction_type,
            evaluation_date=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            sample_size=len(predictions),
            mae=mae,
            rmse=rmse,
            r_squared=r_squared
        )

        db.add(accuracy)
        db.commit()

        logger.info(f"Accuracy evaluated: {prediction_type} - R²={r_squared}")

        return {
            "evaluation_available": True,
            "prediction_type": prediction_type,
            "sample_size": len(predictions),
            "mae": float(mae),
            "rmse": float(rmse),
            "r_squared": float(r_squared)
        }
