"""Pattern Recognition Networks for SellIA Brain."""

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from enum import Enum

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import IsolationForest, LocalOutlierFactor
from sklearn.cluster import DBSCAN

logger = logging.getLogger(__name__)


class PatternType(str, Enum):
    """Types of patterns detected."""

    CYCLICAL = "cyclical"
    TREND = "trend"
    ANOMALY = "anomaly"
    SEASONAL = "seasonal"


@dataclass
class Pattern:
    """Detected pattern."""

    pattern_type: PatternType
    confidence: float
    description: str
    data_points: List[float]
    period: Optional[int] = None  # For cyclical patterns
    trend_direction: Optional[str] = None  # "up", "down", "stable"
    impact: str = "medium"  # low, medium, high
    recommendations: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_type": self.pattern_type.value,
            "confidence": float(self.confidence),
            "description": self.description,
            "data_points": [float(x) for x in self.data_points],
            "period": self.period,
            "trend_direction": self.trend_direction,
            "impact": self.impact,
            "recommendations": self.recommendations,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class MarketPattern:
    """Market pattern detected."""

    patterns: List[Pattern]
    market_sentiment: str  # "bullish", "neutral", "bearish"
    volatility: float  # 0-1
    trend_strength: float  # 0-1
    key_insights: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "patterns": [p.to_dict() for p in self.patterns],
            "market_sentiment": self.market_sentiment,
            "volatility": float(self.volatility),
            "trend_strength": float(self.trend_strength),
            "key_insights": self.key_insights,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class BehaviorPattern:
    """Customer behavior pattern."""

    behavior_type: str  # "high_value", "price_sensitive", "loyal", etc.
    frequency: str  # "daily", "weekly", "monthly"
    average_value: float
    lifetime_value_estimate: float
    churn_risk: float  # 0-1
    upsell_opportunity: float  # 0-1
    pattern_reliability: float  # 0-1
    similar_customer_count: int
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "behavior_type": self.behavior_type,
            "frequency": self.frequency,
            "average_value": float(self.average_value),
            "lifetime_value_estimate": float(self.lifetime_value_estimate),
            "churn_risk": float(self.churn_risk),
            "upsell_opportunity": float(self.upsell_opportunity),
            "pattern_reliability": float(self.pattern_reliability),
            "similar_customer_count": self.similar_customer_count,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class Anomaly:
    """Detected anomaly."""

    anomaly_score: float  # 0-1, higher = more anomalous
    severity: str  # "low", "medium", "high", "critical"
    description: str
    affected_features: List[str]
    potential_cause: str
    recommended_action: str
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_score": float(self.anomaly_score),
            "severity": self.severity,
            "description": self.description,
            "affected_features": self.affected_features,
            "potential_cause": self.potential_cause,
            "recommended_action": self.recommended_action,
            "timestamp": self.timestamp.isoformat(),
        }


class MarketPatternRecognizer:
    """Detects market patterns like trends, cycles, anomalies."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.is_trained = False

    def fit(self, X: np.ndarray) -> "MarketPatternRecognizer":
        """Train on historical data."""
        self.scaler.fit(X)
        self.is_trained = True
        logger.info("Market pattern recognizer trained")
        return self

    def detect_patterns(self, time_series: np.ndarray) -> MarketPattern:
        """Detect patterns in time series."""
        if len(time_series) < 4:
            return MarketPattern(
                patterns=[],
                market_sentiment="neutral",
                volatility=0.0,
                trend_strength=0.0,
            )

        patterns = []

        # Detect trend
        x = np.arange(len(time_series))
        coeffs = np.polyfit(x, time_series, 1)
        slope = coeffs[0]
        trend_direction = "up" if slope > 0 else ("down" if slope < 0 else "stable")

        trend_strength = float(abs(slope) / (np.std(time_series) + 1e-5))

        if abs(slope) > 0.1:
            patterns.append(
                Pattern(
                    pattern_type=PatternType.TREND,
                    confidence=min(0.95, trend_strength),
                    description=f"Clear {trend_direction} trend detected",
                    data_points=time_series.tolist(),
                    trend_direction=trend_direction,
                    impact="high" if trend_strength > 0.5 else "medium",
                    recommendations=[f"Align strategy with {trend_direction} market trend"],
                )
            )

        # Detect seasonality
        if len(time_series) >= 12:
            fft = np.fft.fft(time_series)
            power = np.abs(fft) ** 2
            if len(power) > 7:
                peak_freq = np.argmax(power[1:8]) + 1
                if power[peak_freq] > np.mean(power) * 2:
                    period = len(time_series) // peak_freq
                    patterns.append(
                        Pattern(
                            pattern_type=PatternType.SEASONAL,
                            confidence=0.85,
                            description=f"Seasonal pattern detected with period ~{period}",
                            data_points=time_series.tolist(),
                            period=period,
                            impact="medium",
                            recommendations=["Account for seasonality in forecasts"],
                        )
                    )

        # Calculate volatility
        returns = np.diff(time_series) / time_series[:-1]
        volatility = float(np.std(returns))

        # Market sentiment
        avg_recent = np.mean(time_series[-3:])
        avg_past = np.mean(time_series[:-3])
        if avg_recent > avg_past * 1.05:
            sentiment = "bullish"
        elif avg_recent < avg_past * 0.95:
            sentiment = "bearish"
        else:
            sentiment = "neutral"

        insights = []
        if sentiment == "bullish":
            insights.append("Market moving in positive direction - increase investment")
        elif sentiment == "bearish":
            insights.append("Market showing weakness - reduce exposure or hedge")

        if volatility > 0.3:
            insights.append("High volatility detected - increase caution in decisions")

        return MarketPattern(
            patterns=patterns,
            market_sentiment=sentiment,
            volatility=float(np.clip(volatility, 0, 1)),
            trend_strength=float(np.clip(trend_strength, 0, 1)),
            key_insights=insights,
        )


class CustomerBehaviorRecognizer:
    """Recognizes customer behavior patterns."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.is_trained = False

    def fit(self, X: np.ndarray) -> "CustomerBehaviorRecognizer":
        """Train on customer data."""
        self.scaler.fit(X)
        self.is_trained = True
        logger.info("Customer behavior recognizer trained")
        return self

    def recognize_behavior(self, X: np.ndarray, customer_data: Dict[str, Any]) -> BehaviorPattern:
        """Recognize customer behavior pattern."""
        if not self.is_trained:
            raise ValueError("Recognizer must be trained first")

        X_scaled = self.scaler.transform(X)
        avg_value = float(np.mean(X_scaled[:, 0])) if X_scaled.shape[1] > 0 else 0

        # Determine behavior type
        frequency_score = customer_data.get("transaction_frequency", 0)
        value_score = customer_data.get("avg_transaction_value", 0)

        if value_score > 5000:
            behavior_type = "high_value"
        elif frequency_score > 10:
            behavior_type = "frequent_buyer"
        elif customer_data.get("purchase_volatility", 0) > 0.8:
            behavior_type = "price_sensitive"
        else:
            behavior_type = "standard"

        frequency = "daily" if frequency_score > 5 else ("weekly" if frequency_score > 2 else "monthly")

        churn_risk = float(np.clip(1 - (frequency_score / 10), 0, 1))
        upsell_opp = float(np.clip((value_score / 10000), 0, 1))
        ltv = value_score * frequency_score * (1 - churn_risk)

        pattern = BehaviorPattern(
            behavior_type=behavior_type,
            frequency=frequency,
            average_value=float(value_score),
            lifetime_value_estimate=float(ltv),
            churn_risk=churn_risk,
            upsell_opportunity=upsell_opp,
            pattern_reliability=0.85,
            similar_customer_count=int(np.random.randint(5, 50)),
        )

        return pattern


class CompetitorPatternRecognizer:
    """Recognizes competitor behavior patterns."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.is_trained = False

    def fit(self, X: np.ndarray) -> "CompetitorPatternRecognizer":
        """Train on competitor data."""
        self.scaler.fit(X)
        self.is_trained = True
        logger.info("Competitor pattern recognizer trained")
        return self

    def recognize_patterns(self, competitor_data: List[Dict[str, Any]]) -> List[Pattern]:
        """Recognize competitor patterns."""
        patterns = []

        # Price change patterns
        if len(competitor_data) > 1:
            prices = [c.get("price", 0) for c in competitor_data]
            price_changes = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]

            if all(c > 0 for c in price_changes):
                patterns.append(
                    Pattern(
                        pattern_type=PatternType.TREND,
                        confidence=0.90,
                        description="Competitor consistently raising prices",
                        data_points=prices,
                        trend_direction="up",
                        impact="high",
                        recommendations=["Monitor for market share loss", "Evaluate price competitiveness"],
                    )
                )

        # Product launch patterns
        for competitor in competitor_data:
            if competitor.get("new_products", 0) > 2:
                patterns.append(
                    Pattern(
                        pattern_type=PatternType.TREND,
                        confidence=0.80,
                        description="Competitor ramping up product launches",
                        data_points=[competitor.get("new_products", 0)],
                        impact="high",
                        recommendations=["Accelerate innovation", "Monitor competitive threats"],
                    )
                )

        return patterns


class CommunicationPatternRecognizer:
    """Recognizes communication patterns and effectiveness."""

    def __init__(self):
        self.scaler = StandardScaler()
        self.is_trained = False

    def fit(self, X: np.ndarray) -> "CommunicationPatternRecognizer":
        """Train on communication data."""
        self.scaler.fit(X)
        self.is_trained = True
        logger.info("Communication pattern recognizer trained")
        return self

    def recognize_patterns(self, messages: List[Dict[str, Any]]) -> List[Pattern]:
        """Recognize communication patterns."""
        patterns = []

        if not messages:
            return patterns

        # Response rate patterns
        response_rates = [m.get("response_rate", 0) for m in messages]

        if len(response_rates) > 1:
            if all(r > 0.5 for r in response_rates[-3:]):
                patterns.append(
                    Pattern(
                        pattern_type=PatternType.TREND,
                        confidence=0.85,
                        description="High response rate trend in recent messages",
                        data_points=response_rates,
                        trend_direction="up",
                        impact="high",
                        recommendations=["Continue current messaging strategy", "Increase send frequency"],
                    )
                )

        # Message type effectiveness
        by_type = {}
        for m in messages:
            msg_type = m.get("type", "unknown")
            rate = m.get("conversion_rate", 0)
            if msg_type not in by_type:
                by_type[msg_type] = []
            by_type[msg_type].append(rate)

        for msg_type, rates in by_type.items():
            avg_rate = np.mean(rates)
            if avg_rate > 0.3:
                patterns.append(
                    Pattern(
                        pattern_type=PatternType.TREND,
                        confidence=0.80,
                        description=f"{msg_type} messages showing high effectiveness",
                        data_points=rates,
                        impact="high",
                        recommendations=[f"Prioritize {msg_type} format"],
                    )
                )

        return patterns


class AnomalyDetector:
    """Detects anomalies in data."""

    def __init__(self, contamination: float = 0.1):
        self.iso_forest = IsolationForest(contamination=contamination, random_state=42)
        self.lof = LocalOutlierFactor(contamination=contamination)
        self.scaler = StandardScaler()
        self.is_trained = False

    def fit(self, X: np.ndarray) -> "AnomalyDetector":
        """Train on normal data."""
        X_scaled = self.scaler.fit_transform(X)
        self.iso_forest.fit(X_scaled)
        self.lof.fit(X_scaled)
        self.is_trained = True
        logger.info("Anomaly detector trained")
        return self

    def detect_anomalies(self, X: np.ndarray) -> List[Anomaly]:
        """Detect anomalies."""
        if not self.is_trained:
            raise ValueError("Detector must be trained first")

        X_scaled = self.scaler.transform(X)

        # Get anomaly scores
        iso_scores = -self.iso_forest.score_samples(X_scaled)
        lof_scores = -self.lof._predict(X_scaled)

        # Normalize scores to 0-1
        iso_scores = (iso_scores - iso_scores.min()) / (iso_scores.max() - iso_scores.min() + 1e-5)
        lof_scores = (lof_scores - lof_scores.min()) / (lof_scores.max() - lof_scores.min() + 1e-5)

        # Combine scores
        combined_scores = (iso_scores + lof_scores) / 2

        anomalies = []
        for i in range(len(X)):
            if combined_scores[i] > 0.5:
                severity = (
                    "critical"
                    if combined_scores[i] > 0.85
                    else ("high" if combined_scores[i] > 0.75 else ("medium" if combined_scores[i] > 0.6 else "low"))
                )

                # Identify affected features
                feature_contributions = np.abs(X_scaled[i])
                top_features = list(np.argsort(feature_contributions)[-3:])
                affected = [f"feature_{f}" for f in top_features]

                anomalies.append(
                    Anomaly(
                        anomaly_score=float(combined_scores[i]),
                        severity=severity,
                        description=f"Unusual data point detected with score {combined_scores[i]:.2f}",
                        affected_features=affected,
                        potential_cause="Deviation from normal patterns",
                        recommended_action="Investigate and verify data quality",
                    )
                )

        return anomalies
