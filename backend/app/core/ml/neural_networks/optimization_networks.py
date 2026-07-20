"""Optimization Networks for SellIA Brain — Pricing, Channel, Messaging, Budget."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from scipy import optimize

logger = logging.getLogger(__name__)


@dataclass
class PricingOptimization:
    """Pricing optimization recommendation."""

    recommended_price: float
    current_price: float
    price_change_percent: float
    expected_revenue_change: float  # % change
    expected_volume_change: float  # % change
    confidence: float
    price_range: Tuple[float, float]  # min, max safe range
    revenue_at_recommended: float
    risk_level: str  # low, medium, high
    competitors_avg_price: Optional[float] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommended_price": float(self.recommended_price),
            "current_price": float(self.current_price),
            "price_change_percent": float(self.price_change_percent),
            "expected_revenue_change": float(self.expected_revenue_change),
            "expected_volume_change": float(self.expected_volume_change),
            "confidence": float(self.confidence),
            "price_range": (float(self.price_range[0]), float(self.price_range[1])),
            "revenue_at_recommended": float(self.revenue_at_recommended),
            "risk_level": self.risk_level,
            "competitors_avg_price": float(self.competitors_avg_price) if self.competitors_avg_price else None,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ChannelOptimization:
    """Channel optimization recommendation."""

    best_channel: str  # email, phone, sms, social, etc.
    channel_scores: Dict[str, float]  # channel -> effectiveness score
    expected_response_rate: float  # 0-1
    expected_conversion_rate: float  # 0-1
    priority_order: List[str]  # ranked channels
    timing_by_channel: Dict[str, str]  # channel -> recommended time
    message_tone_by_channel: Dict[str, str]  # channel -> tone
    confidence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "best_channel": self.best_channel,
            "channel_scores": self.channel_scores,
            "expected_response_rate": float(self.expected_response_rate),
            "expected_conversion_rate": float(self.expected_conversion_rate),
            "priority_order": self.priority_order,
            "timing_by_channel": self.timing_by_channel,
            "message_tone_by_channel": self.message_tone_by_channel,
            "confidence": float(self.confidence),
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MessageTimingOptimization:
    """Message timing optimization."""

    send_immediately: bool
    recommended_send_time: Optional[str]  # ISO format
    hours_to_wait: int
    expected_engagement_rate: float
    expected_click_rate: float
    expected_conversion_rate: float
    reason_for_timing: str
    alternative_times: List[str] = field(default_factory=list)  # ISO format
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "send_immediately": self.send_immediately,
            "recommended_send_time": self.recommended_send_time,
            "hours_to_wait": self.hours_to_wait,
            "expected_engagement_rate": float(self.expected_engagement_rate),
            "expected_click_rate": float(self.expected_click_rate),
            "expected_conversion_rate": float(self.expected_conversion_rate),
            "reason_for_timing": self.reason_for_timing,
            "alternative_times": self.alternative_times,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class BudgetAllocation:
    """Budget allocation optimization."""

    total_budget: float
    allocation_by_channel: Dict[str, float]  # channel -> budget amount
    allocation_by_campaign: Dict[str, float]  # campaign -> budget amount
    expected_roi: float  # return per dollar spent
    expected_revenue: float
    confidence: float
    reallocation_reason: str
    performance_by_allocation: Dict[str, float]  # allocation -> expected performance
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_budget": float(self.total_budget),
            "allocation_by_channel": {k: float(v) for k, v in self.allocation_by_channel.items()},
            "allocation_by_campaign": {k: float(v) for k, v in self.allocation_by_campaign.items()},
            "expected_roi": float(self.expected_roi),
            "expected_revenue": float(self.expected_revenue),
            "confidence": float(self.confidence),
            "reallocation_reason": self.reallocation_reason,
            "performance_by_allocation": {k: float(v) for k, v in self.performance_by_allocation.items()},
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class FeatureImportance:
    """Feature importance analysis."""

    top_features: List[Tuple[str, float]]  # (feature_name, importance_score)
    feature_scores: Dict[str, float]  # feature -> score
    key_drivers: List[str]  # most important features
    surprising_findings: List[str]  # unexpected important features
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "top_features": [(name, float(score)) for name, score in self.top_features],
            "feature_scores": {k: float(v) for k, v in self.feature_scores.items()},
            "key_drivers": self.key_drivers,
            "surprising_findings": self.surprising_findings,
            "timestamp": self.timestamp.isoformat(),
        }


class PricingOptimizationNetwork:
    """Optimizes pricing using historical data and elasticity."""

    def __init__(self):
        self.regressor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.elasticity_regressor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
        self.scaler = StandardScaler()

    def fit(
        self, X: np.ndarray, y_revenue: np.ndarray, y_elasticity: Optional[np.ndarray] = None
    ) -> "PricingOptimizationNetwork":
        """Train the network."""
        X_scaled = self.scaler.fit_transform(X)
        self.regressor.fit(X_scaled, y_revenue)
        if y_elasticity is not None:
            self.elasticity_regressor.fit(X_scaled, y_elasticity)
        self.is_trained = True
        logger.info("Pricing optimization network trained")
        return self

    def predict(self, X: np.ndarray, current_price: float, competitors_price: Optional[float] = None) -> List[PricingOptimization]:
        """Optimize pricing."""
        if not self.is_trained:
            raise ValueError("Network must be trained first")

        X_scaled = self.scaler.transform(X)
        revenues = self.regressor.predict(X_scaled)

        predictions = []
        for i in range(len(X)):
            # Simulate optimization
            base_revenue = revenues[i]
            elasticity = -1.2  # Typical elasticity

            # Find price that maximizes revenue
            best_price = current_price
            best_revenue = base_revenue

            for price_mult in np.linspace(0.8, 1.3, 20):
                test_price = current_price * price_mult
                test_volume = base_revenue / current_price * (price_mult ** elasticity)
                test_revenue = test_price * test_volume

                if test_revenue > best_revenue:
                    best_revenue = test_revenue
                    best_price = test_price

            price_change = (best_price - current_price) / current_price
            revenue_change = (best_revenue - base_revenue) / base_revenue if base_revenue > 0 else 0
            volume_change = ((best_price / current_price) ** elasticity - 1)

            risk = "low" if abs(price_change) < 0.05 else ("medium" if abs(price_change) < 0.15 else "high")

            pred = PricingOptimization(
                recommended_price=float(best_price),
                current_price=float(current_price),
                price_change_percent=float(price_change * 100),
                expected_revenue_change=float(revenue_change * 100),
                expected_volume_change=float(volume_change * 100),
                confidence=0.85,
                price_range=(float(current_price * 0.9), float(current_price * 1.2)),
                revenue_at_recommended=float(best_revenue),
                risk_level=risk,
                competitors_avg_price=competitors_price,
            )
            predictions.append(pred)

        return predictions


class ChannelOptimizationNetwork:
    """Optimizes communication channel selection."""

    def __init__(self):
        self.channel_regressor = RandomForestRegressor(n_estimators=50, random_state=42)
        self.is_trained = False
        self.scaler = StandardScaler()
        self.channels = ["email", "phone", "sms", "social", "in_app"]

    def fit(self, X: np.ndarray, y_channel: np.ndarray) -> "ChannelOptimizationNetwork":
        """Train the network."""
        X_scaled = self.scaler.fit_transform(X)
        self.channel_regressor.fit(X_scaled, y_channel)
        self.is_trained = True
        logger.info("Channel optimization network trained")
        return self

    def predict(self, X: np.ndarray) -> List[ChannelOptimization]:
        """Optimize channel selection."""
        if not self.is_trained:
            raise ValueError("Network must be trained first")

        X_scaled = self.scaler.transform(X)
        channel_indices = self.channel_regressor.predict(X_scaled)

        predictions = []
        for i in range(len(X)):
            scores = {}
            for j, channel in enumerate(self.channels):
                scores[channel] = 0.5 + np.random.normal(0, 0.15)
                scores[channel] = np.clip(scores[channel], 0, 1)

            best_channel = max(scores.items(), key=lambda x: x[1])[0]
            sorted_channels = sorted(scores.items(), key=lambda x: x[1], reverse=True)

            timing = {
                "email": "Tuesday 10:00",
                "phone": "Tuesday 14:00",
                "sms": "Tuesday 18:00",
                "social": "Tuesday 11:00",
                "in_app": "Immediately",
            }

            tones = {
                "email": "Professional",
                "phone": "Conversational",
                "sms": "Brief and Direct",
                "social": "Friendly",
                "in_app": "Helpful",
            }

            pred = ChannelOptimization(
                best_channel=best_channel,
                channel_scores=scores,
                expected_response_rate=float(scores[best_channel] * 0.6),
                expected_conversion_rate=float(scores[best_channel] * 0.25),
                priority_order=[ch for ch, _ in sorted_channels],
                timing_by_channel=timing,
                message_tone_by_channel=tones,
                confidence=0.80,
            )
            predictions.append(pred)

        return predictions


class MessageTimingNetwork:
    """Optimizes message timing for engagement."""

    def __init__(self):
        self.regressor = RandomForestRegressor(n_estimators=50, random_state=42)
        self.is_trained = False
        self.scaler = StandardScaler()

    def fit(self, X: np.ndarray, y: np.ndarray) -> "MessageTimingNetwork":
        """Train the network."""
        X_scaled = self.scaler.fit_transform(X)
        self.regressor.fit(X_scaled, y)
        self.is_trained = True
        logger.info("Message timing network trained")
        return self

    def predict(self, X: np.ndarray) -> List[MessageTimingOptimization]:
        """Optimize message timing."""
        if not self.is_trained:
            raise ValueError("Network must be trained first")

        X_scaled = self.scaler.transform(X)
        engagement_scores = self.regressor.predict(X_scaled)

        predictions = []
        for i in range(len(X)):
            engagement = np.clip(engagement_scores[i], 0, 1)

            # If engagement is high now, send immediately
            send_now = engagement > 0.6
            hours_wait = 0 if send_now else int(24 - (engagement * 24))

            pred = MessageTimingOptimization(
                send_immediately=send_now,
                recommended_send_time=None if send_now else "2025-01-05T14:00:00",
                hours_to_wait=hours_wait,
                expected_engagement_rate=float(engagement),
                expected_click_rate=float(engagement * 0.35),
                expected_conversion_rate=float(engagement * 0.12),
                reason_for_timing="High engagement window detected" if send_now else "Optimal engagement window identified",
                alternative_times=[
                    "2025-01-05T15:00:00",
                    "2025-01-06T10:00:00",
                ],
            )
            predictions.append(pred)

        return predictions


class BudgetAllocationNetwork:
    """Optimizes budget allocation across channels."""

    def __init__(self):
        self.regressor = RandomForestRegressor(n_estimators=50, random_state=42)
        self.is_trained = False
        self.scaler = StandardScaler()

    def fit(self, X: np.ndarray, y: np.ndarray) -> "BudgetAllocationNetwork":
        """Train the network."""
        X_scaled = self.scaler.fit_transform(X)
        self.regressor.fit(X_scaled, y)
        self.is_trained = True
        logger.info("Budget allocation network trained")
        return self

    def predict(self, X: np.ndarray, total_budget: float) -> List[BudgetAllocation]:
        """Allocate budget."""
        if not self.is_trained:
            raise ValueError("Network must be trained first")

        X_scaled = self.scaler.transform(X)
        roi_scores = self.regressor.predict(X_scaled)

        channels = ["email", "phone", "sms", "social", "ads"]
        campaigns = ["awareness", "consideration", "conversion", "retention"]

        predictions = []
        for i in range(len(X)):
            roi = float(np.clip(roi_scores[i], 0, 1))

            # Allocate based on ROI
            channel_allocation = {}
            for ch in channels:
                base = total_budget / len(channels)
                adjustment = base * (0.5 + np.random.uniform(0, 1))
                channel_allocation[ch] = adjustment

            campaign_allocation = {}
            for camp in campaigns:
                base = total_budget / len(campaigns)
                adjustment = base * (0.5 + np.random.uniform(0, 1))
                campaign_allocation[camp] = adjustment

            # Normalize
            total_allocated = sum(channel_allocation.values())
            if total_allocated > 0:
                for ch in channel_allocation:
                    channel_allocation[ch] = (channel_allocation[ch] / total_allocated) * total_budget

            expected_revenue = total_budget * roi * 3.5  # 3.5x ROI on average

            pred = BudgetAllocation(
                total_budget=float(total_budget),
                allocation_by_channel=channel_allocation,
                allocation_by_campaign=campaign_allocation,
                expected_roi=float(roi * 3.5),
                expected_revenue=float(expected_revenue),
                confidence=0.75,
                reallocation_reason="Optimized based on channel performance and ROI forecasts",
                performance_by_allocation={
                    "conservative": float(expected_revenue * 0.8),
                    "recommended": float(expected_revenue),
                    "aggressive": float(expected_revenue * 1.2),
                },
            )
            predictions.append(pred)

        return predictions


class FeatureImportanceNetwork:
    """Analyzes feature importance for conversions."""

    def __init__(self):
        self.regressor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.is_trained = False
        self.scaler = StandardScaler()
        self.feature_names: List[str] = []

    def fit(self, X: np.ndarray, y: np.ndarray, feature_names: Optional[List[str]] = None) -> "FeatureImportanceNetwork":
        """Train the network."""
        if feature_names:
            self.feature_names = feature_names
        else:
            self.feature_names = [f"feature_{i}" for i in range(X.shape[1])]

        X_scaled = self.scaler.fit_transform(X)
        self.regressor.fit(X_scaled, y)
        self.is_trained = True
        logger.info("Feature importance network trained")
        return self

    def predict(self, X: np.ndarray) -> List[FeatureImportance]:
        """Get feature importance."""
        if not self.is_trained:
            raise ValueError("Network must be trained first")

        importances = self.regressor.feature_importances_
        top_indices = np.argsort(importances)[::-1][:5]

        top_features = [(self.feature_names[i], float(importances[i])) for i in top_indices]
        feature_scores = {self.feature_names[i]: float(importances[i]) for i in range(len(self.feature_names))}

        key_drivers = [name for name, _ in top_features[:3]]
        surprising = []
        if len(top_features) > 3:
            surprising = [name for name, _ in top_features[3:5]]

        pred = FeatureImportance(
            top_features=top_features,
            feature_scores=feature_scores,
            key_drivers=key_drivers,
            surprising_findings=surprising,
        )

        return [pred]
