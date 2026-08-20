"""Predictive analytics models — demand + churn + revenue forecasting."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Decimal, Enum as SQLEnum, Index, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class PredictionHorizon(str, Enum):
    """Prediction time horizon."""
    NEXT_7_DAYS = "next_7_days"
    NEXT_30_DAYS = "next_30_days"
    NEXT_90_DAYS = "next_90_days"
    NEXT_365_DAYS = "next_365_days"


class ChurnPrediction(Base):
    """Customer churn prediction."""
    __tablename__ = "churn_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Prediction
    churn_probability_7d = Column(Decimal(5, 2), default=0)  # % in next 7 days
    churn_probability_30d = Column(Decimal(5, 2), default=0)  # % in next 30 days
    churn_probability_90d = Column(Decimal(5, 2), default=0)  # % in next 90 days

    # Drivers (top churn signals)
    primary_churn_driver = Column(String(255), nullable=True)  # e.g., "no_purchase_60d", "low_engagement"
    churn_driver_score = Column(Decimal(5, 2), nullable=True)  # Contribution to churn risk

    # Intervention
    recommended_action = Column(String(255), nullable=True)  # e.g., "send_reactivation_email", "discount_offer"
    intervention_success_rate = Column(Decimal(5, 2), nullable=True)  # Historical % of intervention working

    # Confidence
    model_confidence = Column(Decimal(3, 1), default=Decimal("0.8"))  # 0-1 (0.8 = 80% confident)
    last_prediction_date = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer", foreign_keys=[customer_id])

    __table_args__ = (
        Index("idx_business_churn_7d", "business_id", "churn_probability_7d"),
        Index("idx_customer_date", "customer_id", "last_prediction_date"),
    )


class PurchaseTimingPrediction(Base):
    """Predict next purchase timing for customer."""
    __tablename__ = "purchase_timing_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Timing prediction
    days_until_next_purchase = Column(Integer, nullable=True)  # Predicted days
    predicted_purchase_date = Column(String(10), nullable=True)  # YYYY-MM-DD
    purchase_probability_7d = Column(Decimal(5, 2), default=0)  # % chance of purchase in 7d
    purchase_probability_30d = Column(Decimal(5, 2), default=0)  # % chance in 30d

    # Expected value
    predicted_order_value = Column(Decimal(10, 2), nullable=True)  # Expected $
    predicted_product_category = Column(String(100), nullable=True)  # Most likely category

    # Confidence
    model_confidence = Column(Decimal(3, 1), default=Decimal("0.7"))
    last_prediction_date = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer", foreign_keys=[customer_id])

    __table_args__ = (
        Index("idx_business_prob_7d", "business_id", "purchase_probability_7d"),
        Index("idx_predicted_date", "business_id", "predicted_purchase_date"),
    )


class DemandForecast(Base):
    """Product/category demand forecast."""
    __tablename__ = "demand_forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Forecast period
    product_category = Column(String(100), nullable=False)
    forecast_start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    forecast_end_date = Column(String(10), nullable=False)

    # Demand prediction
    forecasted_units = Column(Integer, default=0)
    forecasted_revenue = Column(Decimal(12, 2), default=0)
    confidence_interval_low = Column(Decimal(12, 2), nullable=True)  # 80% CI lower bound
    confidence_interval_high = Column(Decimal(12, 2), nullable=True)  # 80% CI upper bound

    # Comparison
    previous_period_units = Column(Integer, nullable=True)
    yoy_growth_rate = Column(Decimal(5, 2), nullable=True)  # % YoY growth
    mom_growth_rate = Column(Decimal(5, 2), nullable=True)  # % MoM growth

    # Seasonality
    is_seasonal_peak = Column(Boolean, default=False)
    seasonality_index = Column(Decimal(5, 2), nullable=True)  # 1.0 = baseline

    # Model info
    model_confidence = Column(Decimal(3, 1), default=Decimal("0.75"))
    prediction_date = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_category_date", "business_id", "product_category", "forecast_start_date"),
    )


class RevenueForecast(Base):
    """Business revenue forecast."""
    __tablename__ = "revenue_forecasts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Forecast period
    forecast_start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    forecast_end_date = Column(String(10), nullable=False)
    forecast_horizon = Column(SQLEnum(PredictionHorizon), default=PredictionHorizon.NEXT_30_DAYS)

    # Revenue prediction
    forecasted_revenue = Column(Decimal(12, 2), default=0)  # Total predicted revenue
    forecasted_orders = Column(Integer, default=0)  # Expected order count
    forecasted_aov = Column(Decimal(10, 2), default=0)  # Predicted average order value

    # Confidence intervals (80%)
    confidence_interval_low = Column(Decimal(12, 2), nullable=True)
    confidence_interval_high = Column(Decimal(12, 2), nullable=True)

    # Components
    new_customer_revenue = Column(Decimal(12, 2), default=0)  # From new customers
    repeat_customer_revenue = Column(Decimal(12, 2), default=0)  # From repeats

    # Comparison
    previous_period_revenue = Column(Decimal(12, 2), nullable=True)
    previous_period_orders = Column(Integer, nullable=True)
    growth_rate = Column(Decimal(5, 2), nullable=True)  # % growth vs last period

    # Factors
    trending_factors = Column(JSONB, default=list)  # ["summer_seasonality", "promo_campaign"]
    risk_factors = Column(JSONB, default=list)  # ["high_churn_rate", "new_competitor"]

    # Model
    model_confidence = Column(Decimal(3, 1), default=Decimal("0.8"))
    prediction_date = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", foreign_keys=[business_id])

    __table_args__ = (
        Index("idx_business_date", "business_id", "forecast_start_date"),
    )


class PredictionAccuracy(Base):
    """Track prediction model accuracy over time."""
    __tablename__ = "prediction_accuracy"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Prediction type
    prediction_type = Column(String(50), nullable=False)  # churn, purchase_timing, demand, revenue

    # Evaluation period
    evaluation_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    sample_size = Column(Integer, default=0)  # # predictions evaluated

    # Accuracy metrics
    mae = Column(Decimal(8, 2), nullable=True)  # Mean absolute error
    rmse = Column(Decimal(8, 2), nullable=True)  # Root mean squared error
    r_squared = Column(Decimal(3, 2), nullable=True)  # 0-1 (1 = perfect)
    accuracy_rate = Column(Decimal(5, 2), nullable=True)  # % correct predictions

    # Thresholds
    precision = Column(Decimal(3, 2), nullable=True)  # True positives / predicted positives
    recall = Column(Decimal(3, 2), nullable=True)  # True positives / actual positives
    f1_score = Column(Decimal(3, 2), nullable=True)  # Harmonic mean of precision/recall

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_type_date", "business_id", "prediction_type", "evaluation_date"),
    )
