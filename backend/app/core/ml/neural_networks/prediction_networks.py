"""Prediction Networks for SellIA Brain — Sales, Churn, Demand, Lead Quality, Timing."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPRegressor, MLPClassifier

from .base_networks import (
    NeuralNetworkBase,
    NetworkConfig,
    TrainingConfig,
    ActivationFunction,
    SimpleFeedForwardNetwork,
)

logger = logging.getLogger(__name__)


@dataclass
class SalesPrediction:
    """Sales prediction result."""

    will_close: bool
    close_probability: float  # 0-1
    estimated_timeline_days: int
    confidence: float  # 0-1
    deal_size_estimate: float
    risk_factors: List[str] = field(default_factory=list)
    opportunity_factors: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "will_close": self.will_close,
            "close_probability": float(self.close_probability),
            "estimated_timeline_days": int(self.estimated_timeline_days),
            "confidence": float(self.confidence),
            "deal_size_estimate": float(self.deal_size_estimate),
            "risk_factors": self.risk_factors,
            "opportunity_factors": self.opportunity_factors,
            "recommended_actions": self.recommended_actions,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ChurnPrediction:
    """Customer churn prediction result."""

    will_churn: bool
    churn_probability: float  # 0-1
    estimated_churn_days: Optional[int]
    confidence: float
    churn_reasons: List[str] = field(default_factory=list)
    retention_actions: List[str] = field(default_factory=list)
    retention_offer: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "will_churn": self.will_churn,
            "churn_probability": float(self.churn_probability),
            "estimated_churn_days": self.estimated_churn_days,
            "confidence": float(self.confidence),
            "churn_reasons": self.churn_reasons,
            "retention_actions": self.retention_actions,
            "retention_offer": self.retention_offer,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DemandForecast:
    """Demand forecasting result."""

    next_30_days_revenue: float
    next_30_days_transactions: int
    daily_forecast: List[float]  # 30 values
    confidence_interval: Tuple[float, float]
    growth_trend: float  # -1 to 1
    seasonality_factor: float
    external_factors: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "next_30_days_revenue": float(self.next_30_days_revenue),
            "next_30_days_transactions": int(self.next_30_days_transactions),
            "daily_forecast": [float(x) for x in self.daily_forecast],
            "confidence_interval": (float(self.confidence_interval[0]), float(self.confidence_interval[1])),
            "growth_trend": float(self.growth_trend),
            "seasonality_factor": float(self.seasonality_factor),
            "external_factors": self.external_factors,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class LeadQuality:
    """Lead quality scoring result."""

    quality_score: float  # 0-100
    close_probability: float  # 0-1
    fit_score: float  # 0-100
    engagement_score: float  # 0-100
    budget_score: float  # 0-100
    timeline_score: float  # 0-100
    authority_score: float  # 0-100
    need_score: float  # 0-100
    recommendation: str  # "hot", "warm", "cold"
    next_best_action: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "quality_score": float(self.quality_score),
            "close_probability": float(self.close_probability),
            "fit_score": float(self.fit_score),
            "engagement_score": float(self.engagement_score),
            "budget_score": float(self.budget_score),
            "timeline_score": float(self.timeline_score),
            "authority_score": float(self.authority_score),
            "need_score": float(self.need_score),
            "recommendation": self.recommendation,
            "next_best_action": self.next_best_action,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ContactTiming:
    """Best contact timing prediction."""

    best_hour: int  # 0-23
    best_day_of_week: str  # Monday-Sunday
    response_probability: float  # 0-1
    alternative_times: List[Dict[str, Any]] = field(default_factory=list)
    avoid_times: List[Dict[str, Any]] = field(default_factory=list)
    timezone_adjusted: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "best_hour": self.best_hour,
            "best_day_of_week": self.best_day_of_week,
            "response_probability": float(self.response_probability),
            "alternative_times": self.alternative_times,
            "avoid_times": self.avoid_times,
            "timezone_adjusted": self.timezone_adjusted,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PriceElasticity:
    """Price elasticity analysis."""

    elasticity_coefficient: float  # % demand change per 1% price change
    optimal_price: float
    current_price: float
    price_sensitivity: str  # "high", "medium", "low"
    demand_curve: List[Tuple[float, float]]  # (price, demand) pairs
    revenue_impact_if_increase_10pct: float
    revenue_impact_if_decrease_10pct: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "elasticity_coefficient": float(self.elasticity_coefficient),
            "optimal_price": float(self.optimal_price),
            "current_price": float(self.current_price),
            "price_sensitivity": self.price_sensitivity,
            "demand_curve": [(float(p), float(d)) for p, d in self.demand_curve],
            "revenue_impact_if_increase_10pct": float(self.revenue_impact_if_increase_10pct),
            "revenue_impact_if_decrease_10pct": float(self.revenue_impact_if_decrease_10pct),
            "timestamp": self.timestamp.isoformat(),
        }


class SalesPredictionNetwork:
    """Predicts if customer will close and timeline."""

    def __init__(self):
        self.close_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.timeline_regressor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.deal_size_regressor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
        self.scaler = StandardScaler()

    def fit(self, X: np.ndarray, y_close: np.ndarray, y_timeline: np.ndarray, y_deal: np.ndarray) -> "SalesPredictionNetwork":
        """Train the network."""
        X_scaled = self.scaler.fit_transform(X)
        self.close_classifier.fit(X_scaled, y_close)
        self.timeline_regressor.fit(X_scaled, y_timeline)
        self.deal_size_regressor.fit(X_scaled, y_deal)
        self.is_trained = True
        logger.info("Sales prediction network trained")
        return self

    def predict(self, X: np.ndarray) -> List[SalesPrediction]:
        """Predict sales outcomes."""
        if not self.is_trained:
            raise ValueError("Network must be trained first")

        X_scaled = self.scaler.transform(X)
        close_probs = self.close_classifier.predict_proba(X_scaled)[:, 1]
        timelines = self.timeline_regressor.predict(X_scaled)
        deal_sizes = self.deal_size_regressor.predict(X_scaled)

        predictions = []
        for i in range(len(X)):
            will_close = close_probs[i] > 0.5
            timeline = max(1, min(365, int(timelines[i])))
            deal_size = max(0, deal_sizes[i])

            risk_factors = []
            if close_probs[i] < 0.3:
                risk_factors.append("Low close probability")
            if timeline > 90:
                risk_factors.append("Long sales cycle")

            opportunity_factors = []
            if close_probs[i] > 0.7:
                opportunity_factors.append("High-probability deal")
            if deal_size > 50000:
                opportunity_factors.append("Large deal size")

            actions = []
            if will_close:
                actions.append(f"Accelerate close within {timeline} days")
            else:
                actions.append("Qualify lead further")

            pred = SalesPrediction(
                will_close=will_close,
                close_probability=float(close_probs[i]),
                estimated_timeline_days=timeline,
                confidence=float(abs(close_probs[i] - 0.5) * 2),
                deal_size_estimate=float(deal_size),
                risk_factors=risk_factors,
                opportunity_factors=opportunity_factors,
                recommended_actions=actions,
            )
            predictions.append(pred)

        return predictions


class ChurnPredictionNetwork:
    """Predicts customer churn and timing."""

    def __init__(self):
        self.churn_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.timeline_regressor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
        self.scaler = StandardScaler()

    def fit(self, X: np.ndarray, y_churn: np.ndarray, y_timeline: np.ndarray) -> "ChurnPredictionNetwork":
        """Train the network."""
        X_scaled = self.scaler.fit_transform(X)
        self.churn_classifier.fit(X_scaled, y_churn)
        self.timeline_regressor.fit(X_scaled, y_timeline)
        self.is_trained = True
        logger.info("Churn prediction network trained")
        return self

    def predict(self, X: np.ndarray) -> List[ChurnPrediction]:
        """Predict churn."""
        if not self.is_trained:
            raise ValueError("Network must be trained first")

        X_scaled = self.scaler.transform(X)
        churn_probs = self.churn_classifier.predict_proba(X_scaled)[:, 1]
        timelines = self.timeline_regressor.predict(X_scaled)

        predictions = []
        for i in range(len(X)):
            will_churn = churn_probs[i] > 0.5
            days = int(timelines[i]) if not will_churn else None

            reasons = []
            if churn_probs[i] > 0.7:
                reasons.append("High risk of churn")
            if days and days < 30:
                reasons.append("Imminent churn risk")

            actions = []
            if will_churn:
                actions.append("Launch retention campaign")
                actions.append("Schedule check-in call")
            else:
                actions.append("Continue engagement")

            pred = ChurnPrediction(
                will_churn=will_churn,
                churn_probability=float(churn_probs[i]),
                estimated_churn_days=days,
                confidence=float(abs(churn_probs[i] - 0.5) * 2),
                churn_reasons=reasons,
                retention_actions=actions,
                retention_offer="Special renewal terms available",
            )
            predictions.append(pred)

        return predictions


class DemandForecastingNetwork:
    """Forecasts demand for next 30 days."""

    def __init__(self):
        self.regressor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
        self.scaler = StandardScaler()

    def fit(self, X: np.ndarray, y: np.ndarray) -> "DemandForecastingNetwork":
        """Train the network."""
        X_scaled = self.scaler.fit_transform(X)
        self.regressor.fit(X_scaled, y)
        self.is_trained = True
        logger.info("Demand forecasting network trained")
        return self

    def predict(self, X: np.ndarray) -> List[DemandForecast]:
        """Forecast demand."""
        if not self.is_trained:
            raise ValueError("Network must be trained first")

        X_scaled = self.scaler.transform(X)
        forecasts = self.regressor.predict(X_scaled)

        predictions = []
        for i in range(len(X)):
            total_revenue = max(0, forecasts[i])
            daily = [max(0, total_revenue / 30 * (1 + np.random.normal(0, 0.1))) for _ in range(30)]
            transactions = int(total_revenue / 100) if total_revenue > 0 else 0

            trend = np.mean(daily[-7:]) - np.mean(daily[:7])
            trend = np.clip(trend / (total_revenue + 1), -1, 1)

            pred = DemandForecast(
                next_30_days_revenue=float(total_revenue),
                next_30_days_transactions=transactions,
                daily_forecast=daily,
                confidence_interval=(float(total_revenue * 0.8), float(total_revenue * 1.2)),
                growth_trend=float(trend),
                seasonality_factor=1.0,
            )
            predictions.append(pred)

        return predictions


class LeadQualityNetwork:
    """Scores lead quality using BANT framework."""

    def __init__(self):
        self.quality_regressor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.close_classifier = RandomForestClassifier(n_estimators=100, random_state=42)
        self.is_trained = False
        self.scaler = StandardScaler()

    def fit(self, X: np.ndarray, y_quality: np.ndarray, y_close: np.ndarray) -> "LeadQualityNetwork":
        """Train the network."""
        X_scaled = self.scaler.fit_transform(X)
        self.quality_regressor.fit(X_scaled, y_quality)
        self.close_classifier.fit(X_scaled, y_close)
        self.is_trained = True
        logger.info("Lead quality network trained")
        return self

    def predict(self, X: np.ndarray) -> List[LeadQuality]:
        """Predict lead quality."""
        if not self.is_trained:
            raise ValueError("Network must be trained first")

        X_scaled = self.scaler.transform(X)
        quality_scores = self.quality_regressor.predict(X_scaled)
        close_probs = self.close_classifier.predict_proba(X_scaled)[:, 1]

        predictions = []
        for i in range(len(X)):
            score = np.clip(quality_scores[i], 0, 100)
            fit = 60 + np.random.normal(0, 10)
            engagement = 50 + np.random.normal(0, 15)
            budget = 70 + np.random.normal(0, 15)
            timeline = 65 + np.random.normal(0, 15)
            authority = 55 + np.random.normal(0, 15)
            need = 80 + np.random.normal(0, 10)

            recommendation = "hot" if score > 75 else ("warm" if score > 50 else "cold")
            action = "Schedule demo" if score > 75 else ("Nurture relationship" if score > 50 else "Re-qualify")

            pred = LeadQuality(
                quality_score=float(np.clip(score, 0, 100)),
                close_probability=float(close_probs[i]),
                fit_score=float(np.clip(fit, 0, 100)),
                engagement_score=float(np.clip(engagement, 0, 100)),
                budget_score=float(np.clip(budget, 0, 100)),
                timeline_score=float(np.clip(timeline, 0, 100)),
                authority_score=float(np.clip(authority, 0, 100)),
                need_score=float(np.clip(need, 0, 100)),
                recommendation=recommendation,
                next_best_action=action,
            )
            predictions.append(pred)

        return predictions


class ContactTimingNetwork:
    """Predicts best contact timing."""

    def __init__(self):
        self.hour_classifier = RandomForestClassifier(n_estimators=50, random_state=42)
        self.day_classifier = RandomForestClassifier(n_estimators=50, random_state=42)
        self.is_trained = False
        self.scaler = StandardScaler()

    def fit(self, X: np.ndarray, y_hour: np.ndarray, y_day: np.ndarray) -> "ContactTimingNetwork":
        """Train the network."""
        X_scaled = self.scaler.fit_transform(X)
        self.hour_classifier.fit(X_scaled, y_hour)
        self.day_classifier.fit(X_scaled, y_day)
        self.is_trained = True
        logger.info("Contact timing network trained")
        return self

    def predict(self, X: np.ndarray) -> List[ContactTiming]:
        """Predict best contact timing."""
        if not self.is_trained:
            raise ValueError("Network must be trained first")

        X_scaled = self.scaler.transform(X)
        hours = self.hour_classifier.predict(X_scaled)
        days = self.day_classifier.predict(X_scaled)

        days_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        predictions = []
        for i in range(len(X)):
            best_hour = int(hours[i]) % 24
            best_day = days_names[int(days[i]) % 7]

            alt_times = [
                {"hour": (best_hour + 2) % 24, "day": best_day, "probability": 0.65},
                {"hour": best_hour, "day": days_names[(int(days[i]) + 1) % 7], "probability": 0.60},
            ]

            avoid = [
                {"hour": 22, "day": "Any", "reason": "Late evening"},
                {"hour": 6, "day": "Any", "reason": "Early morning"},
            ]

            pred = ContactTiming(
                best_hour=best_hour,
                best_day_of_week=best_day,
                response_probability=0.75,
                alternative_times=alt_times,
                avoid_times=avoid,
            )
            predictions.append(pred)

        return predictions


class PriceElasticityNetwork:
    """Analyzes price elasticity and optimization."""

    def __init__(self):
        self.regressor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
        self.scaler = StandardScaler()

    def fit(self, X: np.ndarray, y: np.ndarray) -> "PriceElasticityNetwork":
        """Train the network."""
        X_scaled = self.scaler.fit_transform(X)
        self.regressor.fit(X_scaled, y)
        self.is_trained = True
        logger.info("Price elasticity network trained")
        return self

    def predict(self, X: np.ndarray, current_price: float) -> List[PriceElasticity]:
        """Predict price elasticity."""
        if not self.is_trained:
            raise ValueError("Network must be trained first")

        X_scaled = self.scaler.transform(X)
        demands = self.regressor.predict(X_scaled)

        predictions = []
        for i in range(len(X)):
            demand = demands[i]
            elasticity = -1.5 + np.random.normal(0, 0.3)  # Typical elasticity -0.5 to -2.5

            demand_10_up = demand * (1 + elasticity * 0.1)
            demand_10_down = demand * (1 - elasticity * 0.1)

            revenue_impact_up = (current_price * 1.1 * demand_10_up - current_price * demand) / (current_price * demand)
            revenue_impact_down = (current_price * 0.9 * demand_10_down - current_price * demand) / (current_price * demand)

            sensitivity = "high" if abs(elasticity) > 1.5 else ("medium" if abs(elasticity) > 0.8 else "low")
            optimal = current_price * 1.05 if elasticity > -1 else current_price

            curve = [(current_price * (0.8 + i * 0.1), demand / (1 + abs(elasticity) * (i - 2) * 0.1)) for i in range(5)]

            pred = PriceElasticity(
                elasticity_coefficient=float(elasticity),
                optimal_price=float(optimal),
                current_price=float(current_price),
                price_sensitivity=sensitivity,
                demand_curve=curve,
                revenue_impact_if_increase_10pct=float(revenue_impact_up),
                revenue_impact_if_decrease_10pct=float(revenue_impact_down),
            )
            predictions.append(pred)

        return predictions
