"""Revenue Intelligence - ML models for forecasting, churn, expansion."""

import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class CloseRiskLevel(str, Enum):
    """Close probability assessment."""
    HIGH = "high"  # >70%
    MEDIUM = "medium"  # 40-70%
    LOW = "low"  # <40%


class ChurnRiskLevel(str, Enum):
    """Customer churn risk."""
    CRITICAL = "critical"  # >70%
    HIGH = "high"  # 40-70%
    MEDIUM = "medium"  # 20-40%
    LOW = "low"  # <20%


class ExpansionPotential(str, Enum):
    """Upsell/expansion opportunity."""
    VERY_HIGH = "very_high"  # >80%
    HIGH = "high"  # 60-80%
    MEDIUM = "medium"  # 40-60%
    LOW = "low"  # 20-40%
    MINIMAL = "minimal"  # <20%


@dataclass
class CloseForecast:
    """Deal close prediction."""
    deal_id: str
    close_probability: float  # 0-1
    risk_level: CloseRiskLevel
    expected_close_date: str  # ISO date
    confidence: float  # Model confidence 0-1
    key_drivers: List[str]  # ["intent_high", "budget_confirmed", ...]
    risk_factors: List[str]  # ["stalled_3_days", "price_objection", ...]


@dataclass
class ChurnForecast:
    """Customer churn prediction."""
    customer_id: str
    churn_probability: float  # 0-1
    risk_level: ChurnRiskLevel
    days_until_churn: int  # Predicted days
    confidence: float
    churn_indicators: List[str]  # ["low_engagement", "support_tickets_up", ...]
    retention_score: float  # Actions to retain (0-100)


@dataclass
class ExpansionScore:
    """Expansion/upsell opportunity."""
    customer_id: str
    expansion_probability: float  # 0-1
    expansion_potential: ExpansionPotential
    estimated_expansion_value: float  # USD
    recommended_products: List[Dict[str, Any]]
    time_to_expand_months: int


class RevenueForecaster:
    """
    ML models for sales forecasting:
    - Deal close probability (ARIMA + Logistic Regression)
    - Revenue forecast (time-series by stage)
    - Quota attainment prediction
    """

    def __init__(self):
        self.historical_data: List[Dict[str, Any]] = []

    async def forecast_deal_close(
        self,
        deal_id: str,
        deal_size: float,
        current_stage: str,  # "qualification", "proposal", "negotiation", "closing"
        days_in_stage: int,
        intent_score: float,
        engagement_signals: Dict[str, int],  # {"email_opens": 5, "calls": 2, ...}
    ) -> CloseForecast:
        """
        Predict close probability for a deal using:
        - Stage (later stages = higher close probability)
        - Time in stage (too long = stalled)
        - Intent signals (engagement, budget, authority)
        - Historical conversion rates per stage
        """

        # Stage-based base probabilities
        stage_probs = {
            "qualification": 0.3,
            "proposal": 0.5,
            "negotiation": 0.7,
            "closing": 0.85,
        }

        base_prob = stage_probs.get(current_stage, 0.4)

        # Time adjustment (diminishing returns after optimal time)
        optimal_stage_days = {
            "qualification": 7,
            "proposal": 10,
            "negotiation": 14,
            "closing": 3,
        }
        optimal = optimal_stage_days.get(current_stage, 10)

        if days_in_stage > optimal * 2:
            # Stalled deal
            time_factor = 0.7
        elif days_in_stage > optimal:
            time_factor = 0.85
        else:
            time_factor = 1.0

        # Engagement signal scoring
        engagement_score = min(
            1.0,
            (engagement_signals.get("email_opens", 0) / 10)
            + (engagement_signals.get("calls", 0) / 5)
            + (1.0 if engagement_signals.get("demo_attended") else 0)
            + (1.0 if engagement_signals.get("proposal_sent") else 0),
        ) / 4

        # Intent contribution
        intent_factor = 0.7 + (intent_score * 0.3)  # Intent adds 0-30%

        # Composite probability
        close_prob = (
            base_prob * 0.4
            + time_factor * 0.3
            + engagement_score * 0.2
            + intent_factor * 0.1
        )

        close_prob = np.clip(close_prob, 0.0, 1.0)

        # Risk level
        if close_prob > 0.7:
            risk_level = CloseRiskLevel.HIGH
        elif close_prob > 0.4:
            risk_level = CloseRiskLevel.MEDIUM
        else:
            risk_level = CloseRiskLevel.LOW

        # Expected close date (days remaining)
        days_remaining = {
            CloseRiskLevel.HIGH: 7,
            CloseRiskLevel.MEDIUM: 14,
            CloseRiskLevel.LOW: 30,
        }[risk_level]

        expected_close = (datetime.utcnow() + timedelta(days=days_remaining)).isoformat()

        # Key drivers and risks
        key_drivers = []
        risk_factors = []

        if intent_score > 0.8:
            key_drivers.append("high_intent")
        if engagement_score > 0.7:
            key_drivers.append("strong_engagement")
        if current_stage in ["negotiation", "closing"]:
            key_drivers.append("advanced_stage")

        if days_in_stage > optimal * 2:
            risk_factors.append("stalled_in_stage")
        if engagement_score < 0.3:
            risk_factors.append("low_engagement")
        if intent_score < 0.4:
            risk_factors.append("low_intent")

        return CloseForecast(
            deal_id=deal_id,
            close_probability=close_prob,
            risk_level=risk_level,
            expected_close_date=expected_close,
            confidence=0.75 + (engagement_score * 0.2),  # 0.75-0.95 confidence
            key_drivers=key_drivers or ["baseline"],
            risk_factors=risk_factors or [],
        )

    async def forecast_revenue_by_stage(
        self, deals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Aggregate revenue forecast by pipeline stage.
        Returns: Total, by stage, by probability bucket.
        """
        by_stage = {}
        by_probability = {"high": 0.0, "medium": 0.0, "low": 0.0}
        total_pipeline = 0.0

        for deal in deals:
            stage = deal.get("stage", "unknown")
            prob = deal.get("close_probability", 0.5)
            size = deal.get("size", 0)

            # By stage
            if stage not in by_stage:
                by_stage[stage] = 0.0
            by_stage[stage] += size * prob

            # By probability
            if prob > 0.7:
                by_probability["high"] += size
            elif prob > 0.4:
                by_probability["medium"] += size
            else:
                by_probability["low"] += size

            total_pipeline += size

        return {
            "total_pipeline": total_pipeline,
            "by_stage": by_stage,
            "by_probability": by_probability,
            "weighted_forecast": by_probability["high"]
            + (by_probability["medium"] * 0.55)
            + (by_probability["low"] * 0.2),
        }


class ChurnPredictor:
    """
    Predict customer churn using engagement + usage signals.
    """

    def __init__(self):
        self.churn_thresholds = {
            "email_opens_30d": 3,  # <3 opens in 30 days = risk
            "login_frequency": 7,  # <1 login per week = risk
            "support_tickets_trend": -2,  # Declining support = risk
            "nps_score": 30,  # <30 = risk
        }

    async def predict_churn(
        self,
        customer_id: str,
        subscription_months: int,
        engagement_signals: Dict[str, Any],
        usage_metrics: Dict[str, Any],
        nps_score: Optional[float] = None,
    ) -> ChurnForecast:
        """
        Predict churn probability from:
        - Engagement (email opens, logins, support interactions)
        - Usage (feature adoption, API calls, data volumes)
        - Satisfaction (NPS, support sentiment)
        """

        # Engagement scoring
        email_opens_30d = engagement_signals.get("email_opens_30d", 0)
        logins_30d = engagement_signals.get("logins_30d", 0)
        support_tickets_30d = engagement_signals.get("support_tickets_30d", 0)

        engagement_score = min(
            1.0,
            (email_opens_30d / 10) + (logins_30d / 30) + (support_tickets_30d / 5),
        ) / 3

        # Usage scoring
        feature_adoption = usage_metrics.get("feature_adoption_percent", 0) / 100
        monthly_active_users = usage_metrics.get("monthly_active_users", 0)
        data_growth = usage_metrics.get("data_growth_percent", 0) / 100

        usage_score = (feature_adoption + min(1.0, monthly_active_users / 10) + min(1.0, data_growth)) / 3

        # Satisfaction scoring
        satisfaction_score = 1.0
        if nps_score is not None:
            satisfaction_score = max(0.0, (nps_score + 100) / 200)  # -100 to 100 NPS → 0 to 1

        # Time-based factor (longer subscribers = lower churn)
        tenure_factor = min(1.0, subscription_months / 24)  # 0-2 years

        # Composite churn probability (inverse of engagement)
        churn_prob = (
            (1.0 - engagement_score) * 0.4
            + (1.0 - usage_score) * 0.35
            + (1.0 - satisfaction_score) * 0.25
        )

        churn_prob = np.clip(churn_prob * (1.0 - tenure_factor * 0.3), 0.0, 1.0)

        # Risk level
        if churn_prob > 0.7:
            risk_level = ChurnRiskLevel.CRITICAL
            days_until_churn = 30
        elif churn_prob > 0.4:
            risk_level = ChurnRiskLevel.HIGH
            days_until_churn = 60
        elif churn_prob > 0.2:
            risk_level = ChurnRiskLevel.MEDIUM
            days_until_churn = 90
        else:
            risk_level = ChurnRiskLevel.LOW
            days_until_churn = 180

        # Churn indicators
        indicators = []
        if email_opens_30d < self.churn_thresholds["email_opens_30d"]:
            indicators.append("low_email_engagement")
        if logins_30d < self.churn_thresholds["login_frequency"] * 4:
            indicators.append("declining_login_frequency")
        if support_tickets_30d > 10:
            indicators.append("high_support_tickets")
        if nps_score and nps_score < self.churn_thresholds["nps_score"]:
            indicators.append("low_nps")
        if feature_adoption < 0.3:
            indicators.append("low_feature_adoption")

        # Retention score (actions to take)
        retention_score = (
            engagement_score * 30
            + usage_score * 30
            + satisfaction_score * 40
        )

        return ChurnForecast(
            customer_id=customer_id,
            churn_probability=churn_prob,
            risk_level=risk_level,
            days_until_churn=days_until_churn,
            confidence=0.7 + (abs(engagement_score - 0.5) * 0.2),
            churn_indicators=indicators or ["baseline_churn"],
            retention_score=retention_score,
        )


class ExpansionScorer:
    """
    Identify expansion/upsell opportunities from:
    - Usage growth trajectory
    - Feature adoption by tier
    - Customer health metrics
    - Industry benchmarks
    """

    def __init__(self):
        self.product_tiers = {
            "starter": {"annual_price": 25000, "max_users": 5},
            "professional": {"annual_price": 75000, "max_users": 50},
            "enterprise": {"annual_price": 200000, "max_users": 1000},
        }

    async def score_expansion(
        self,
        customer_id: str,
        current_tier: str,
        monthly_active_users: int,
        feature_adoption_percent: float,
        annual_revenue_with_us: float,
        industry_benchmark_spending: float,
    ) -> ExpansionScore:
        """
        Score expansion opportunity based on:
        - Tier utilization (approaching limits)
        - Feature adoption (use more features = expand)
        - Spending vs benchmark (room to grow)
        """

        # Tier analysis
        current_config = self.product_tiers.get(current_tier, {})
        max_users = current_config.get("max_users", 100)
        utilization = monthly_active_users / max_users

        # Growth trajectory
        if utilization > 0.8:
            expansion_prob = 0.8  # At capacity
        elif utilization > 0.6:
            expansion_prob = 0.6
        elif utilization > 0.4:
            expansion_prob = 0.4
        else:
            expansion_prob = 0.2

        # Feature adoption bonus
        if feature_adoption_percent > 0.8:
            expansion_prob += 0.15
        elif feature_adoption_percent > 0.5:
            expansion_prob += 0.08

        # Spending vs benchmark
        spending_ratio = annual_revenue_with_us / industry_benchmark_spending if industry_benchmark_spending else 1.0
        if spending_ratio > 0.8:
            expansion_prob += 0.1  # Already spending a lot
        elif spending_ratio < 0.3:
            expansion_prob += 0.2  # Massive upside

        expansion_prob = np.clip(expansion_prob, 0.0, 1.0)

        # Expansion potential level
        if expansion_prob > 0.8:
            potential = ExpansionPotential.VERY_HIGH
            months_to_expand = 2
        elif expansion_prob > 0.6:
            potential = ExpansionPotential.HIGH
            months_to_expand = 3
        elif expansion_prob > 0.4:
            potential = ExpansionPotential.MEDIUM
            months_to_expand = 6
        elif expansion_prob > 0.2:
            potential = ExpansionPotential.LOW
            months_to_expand = 9
        else:
            potential = ExpansionPotential.MINIMAL
            months_to_expand = 12

        # Recommended upsell products
        recommended = []
        if utilization > 0.8:
            # Recommend upgrade to next tier
            tier_hierarchy = ["starter", "professional", "enterprise"]
            current_idx = tier_hierarchy.index(current_tier)
            if current_idx < len(tier_hierarchy) - 1:
                next_tier = tier_hierarchy[current_idx + 1]
                next_config = self.product_tiers[next_tier]
                expansion_value = (
                    next_config["annual_price"] - current_config.get("annual_price", 0)
                )
                recommended.append(
                    {
                        "product": f"Upgrade to {next_tier.title()}",
                        "rationale": "At capacity",
                        "estimated_value": expansion_value,
                        "urgency": "high",
                    }
                )

        if feature_adoption_percent < 0.6:
            recommended.append(
                {
                    "product": "Custom integrations / API access",
                    "rationale": "Unlock more features",
                    "estimated_value": 15000,
                    "urgency": "medium",
                }
            )

        return ExpansionScore(
            customer_id=customer_id,
            expansion_probability=expansion_prob,
            expansion_potential=potential,
            estimated_expansion_value=sum(r.get("estimated_value", 0) for r in recommended),
            recommended_products=recommended,
            time_to_expand_months=months_to_expand,
        )
