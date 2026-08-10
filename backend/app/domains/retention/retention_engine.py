"""Phase 17: Customer retention and expansion automation."""

from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class RetentionAction(str, Enum):
    PROACTIVE_OUTREACH = "proactive_outreach"
    SPECIAL_OFFER = "special_offer"
    ACCOUNT_REVIEW = "account_review"
    SUCCESS_TRAINING = "success_training"
    LOYALTY_REWARD = "loyalty_reward"
    ESCALATION = "escalation"


@dataclass
class ChurnSignal:
    signal: str
    severity: str  # low, medium, high, critical
    score: float  # 0-1
    description: str


@dataclass
class RetentionPlan:
    customer_id: str
    churn_risk_score: float
    churn_probability: str  # low, medium, high, critical
    days_until_churn: int
    recommended_actions: List[RetentionAction]
    upsell_opportunity: str
    upsell_amount: float
    suggested_discount: float
    next_step: str


class RetentionEngine:
    """Automate customer retention and growth"""

    def detect_churn_signals(self, customer_data: Dict[str, Any]) -> List[ChurnSignal]:
        """Detect customer churn signals"""

        signals = []

        # Check engagement
        if customer_data.get("days_since_last_login", 999) > 30:
            signals.append(ChurnSignal(
                signal="low_engagement",
                severity="high",
                score=0.8,
                description="No login in 30+ days"
            ))

        # Check usage
        if customer_data.get("usage_percentage", 100) < 20:
            signals.append(ChurnSignal(
                signal="low_usage",
                severity="medium",
                score=0.6,
                description="Using <20% of available features"
            ))

        # Check support tickets
        if customer_data.get("open_support_tickets", 0) > 3:
            signals.append(ChurnSignal(
                signal="support_issues",
                severity="critical",
                score=0.9,
                description="3+ unresolved support tickets"
            ))

        # Check payment
        if customer_data.get("failed_payment_attempts", 0) > 0:
            signals.append(ChurnSignal(
                signal="payment_issues",
                severity="high",
                score=0.7,
                description="Recent failed payment attempt"
            ))

        # Check competitor mentions
        if customer_data.get("viewed_competitor", False):
            signals.append(ChurnSignal(
                signal="competitor_interest",
                severity="medium",
                score=0.6,
                description="Visited competitor website"
            ))

        return signals

    def calculate_churn_risk(self, customer_data: Dict[str, Any]) -> float:
        """Calculate 0-1 churn risk score"""

        signals = self.detect_churn_signals(customer_data)
        if not signals:
            return 0.1  # Base risk

        avg_score = sum(s.score for s in signals) / len(signals)
        return min(avg_score, 1.0)

    def estimate_days_to_churn(self, churn_score: float) -> int:
        """Estimate days until churn based on score"""

        if churn_score > 0.8:
            return 7
        elif churn_score > 0.6:
            return 14
        elif churn_score > 0.4:
            return 30
        else:
            return 60

    def generate_retention_plan(
        self, customer_id: str, customer_data: Dict[str, Any]
    ) -> RetentionPlan:
        """Generate personalized retention plan"""

        churn_score = self.calculate_churn_risk(customer_data)
        days_to_churn = self.estimate_days_to_churn(churn_score)

        # Determine churn probability
        if churn_score > 0.8:
            churn_prob = "critical"
        elif churn_score > 0.6:
            churn_prob = "high"
        elif churn_score > 0.4:
            churn_prob = "medium"
        else:
            churn_prob = "low"

        # Recommend actions based on severity
        actions = []
        if churn_score > 0.7:
            actions = [
                RetentionAction.ESCALATION,
                RetentionAction.ACCOUNT_REVIEW,
                RetentionAction.SPECIAL_OFFER
            ]
        elif churn_score > 0.5:
            actions = [
                RetentionAction.PROACTIVE_OUTREACH,
                RetentionAction.SUCCESS_TRAINING,
                RetentionAction.SPECIAL_OFFER
            ]
        elif churn_score > 0.3:
            actions = [
                RetentionAction.PROACTIVE_OUTREACH,
                RetentionAction.LOYALTY_REWARD
            ]
        else:
            actions = [RetentionAction.LOYALTY_REWARD]

        # Upsell opportunity
        current_plan = customer_data.get("plan", "starter")
        if current_plan == "starter":
            upsell = "Professional Plan"
            amount = 99
        elif current_plan == "professional":
            upsell = "Enterprise Plan"
            amount = 299
        else:
            upsell = "Add-on Services"
            amount = 50

        # Discount if at risk
        discount = 0.20 if churn_score > 0.6 else 0.0

        plan = RetentionPlan(
            customer_id=customer_id,
            churn_risk_score=churn_score,
            churn_probability=churn_prob,
            days_until_churn=days_to_churn,
            recommended_actions=actions,
            upsell_opportunity=upsell,
            upsell_amount=amount,
            suggested_discount=discount,
            next_step="Schedule account review call within 24 hours"
        )

        return plan

    def generate_retention_offer(self, plan: RetentionPlan) -> Dict[str, Any]:
        """Generate personalized retention offer"""

        base_price = plan.upsell_amount
        discounted_price = base_price * (1 - plan.suggested_discount)

        offer = {
            "offer_type": "limited_time",
            "valid_days": 7,
            "original_price": base_price,
            "discounted_price": discounted_price,
            "savings": base_price - discounted_price,
            "description": f"Upgrade to {plan.upsell_opportunity} with {int(plan.suggested_discount * 100)}% off",
            "cta": "Upgrade Now",
            "urgency": "Expires in 7 days"
        }

        return offer
