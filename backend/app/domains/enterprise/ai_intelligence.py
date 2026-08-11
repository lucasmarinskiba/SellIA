"""AI/ML intelligence layer — deal prediction + lead scoring."""

from dataclasses import dataclass
from typing import Optional
from datetime import datetime, timedelta
from enum import Enum
import json


class DealOutcome(str, Enum):
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    STALLED = "stalled"


class LeadQuality(str, Enum):
    HOT = "hot"  # 80-100% likely to close
    WARM = "warm"  # 50-79%
    COLD = "cold"  # 20-49%
    DEAD = "dead"  # <20%


@dataclass
class DealPrediction:
    deal_id: str
    close_probability: float  # 0-1
    estimated_close_date: datetime
    risk_factors: list[str]
    recommended_actions: list[str]
    confidence: float


@dataclass
class LeadScore:
    contact_id: str
    quality: LeadQuality
    score: float  # 0-100
    reasons: list[str]
    next_action: str


@dataclass
class CustomerHealth:
    account_id: str
    health_score: float  # 0-100
    status: str  # healthy, at_risk, critical
    churn_probability: float
    expansion_opportunity: float


class AIIntelligenceManager:
    """
    Backend brain for SellIA.

    Features:
    - Deal outcome prediction (ML model)
    - Lead quality scoring (rules + ML)
    - Customer health monitoring
    - Next-best-action recommendations
    - Anomaly detection (unusual deal behavior)
    """

    def __init__(self):
        self.predictions: dict[str, DealPrediction] = {}
        self.lead_scores: dict[str, LeadScore] = {}
        self.health_scores: dict[str, CustomerHealth] = {}
        self.model_version = "v1.0"

    def predict_deal_outcome(
        self,
        deal_id: str,
        stage: str,
        days_in_stage: int,
        deal_value: float,
        engagement_velocity: float,  # activities/day
        has_proposal: bool,
        contact_seniority: Optional[str] = None,
        industry: Optional[str] = None,
    ) -> DealPrediction:
        """
        Predict deal outcome using ML model.

        Inputs:
        - Stage: Prospecting, Qualifying, Negotiating, Closed Won/Lost
        - Days in stage: How long deal stuck in current stage
        - Engagement velocity: Contact interactions per day
        - Has proposal: Whether formal proposal sent
        - Contact seniority: C-level, VP, Manager, Contributor
        - Industry: For industry-specific models

        Output: Close probability + recommended actions
        """

        # Stage progression baseline
        stage_close_prob = {
            "prospecting": 0.05,
            "qualifying": 0.15,
            "proposal": 0.45,
            "negotiating": 0.65,
            "closed_won": 1.0,
            "closed_lost": 0.0,
        }
        base_prob = stage_close_prob.get(stage.lower(), 0.1)

        # Engagement velocity boost (activity indicates interest)
        engagement_boost = min(engagement_velocity * 0.15, 0.25)

        # Days in stage penalty (stalled deals = lower probability)
        days_penalty = min(days_in_stage / 100 * 0.20, 0.30)

        # Proposal impact (big boost if proposal sent + engagement high)
        proposal_boost = 0.20 if has_proposal and engagement_velocity > 1 else 0

        # Seniority impact (C-level = higher close rate)
        seniority_boost = 0.15 if contact_seniority == "c_level" else 0.05

        # Calculate final probability
        close_prob = base_prob + engagement_boost + proposal_boost + seniority_boost - days_penalty
        close_prob = max(0.0, min(1.0, close_prob))  # Clamp 0-1

        # Risk factors
        risk_factors = []
        if days_in_stage > 60:
            risk_factors.append(f"Deal stalled {days_in_stage} days in {stage}")
        if engagement_velocity < 0.5:
            risk_factors.append("Low engagement velocity")
        if not has_proposal and stage in ["proposal", "negotiating"]:
            risk_factors.append("No proposal sent but in negotiation")

        # Recommended actions
        actions = []
        if engagement_velocity < 0.5:
            actions.append("Schedule check-in call with contact")
        if not has_proposal and stage in ["proposal", "negotiating"]:
            actions.append("Send formal proposal immediately")
        if days_in_stage > 30:
            actions.append("Review deal blocker with account team")
        if close_prob > 0.7 and engagement_velocity > 2:
            actions.append("Escalate to VP for closing conversation")

        # Estimate close date (based on historical average by stage)
        stage_days_to_close = {
            "prospecting": 45,
            "qualifying": 35,
            "proposal": 25,
            "negotiating": 15,
            "closed_won": 0,
        }
        days_remaining = stage_days_to_close.get(stage.lower(), 30)
        estimated_close = datetime.utcnow() + timedelta(days=days_remaining)

        prediction = DealPrediction(
            deal_id=deal_id,
            close_probability=close_prob,
            estimated_close_date=estimated_close,
            risk_factors=risk_factors,
            recommended_actions=actions,
            confidence=0.75 + (engagement_velocity * 0.1),  # More activity = more confident
        )

        self.predictions[deal_id] = prediction
        return prediction

    def score_lead(
        self,
        contact_id: str,
        company_size: Optional[int] = None,
        industry: Optional[str] = None,
        email_engagement: Optional[dict] = None,  # {opens, clicks, replies}
        seniority: Optional[str] = None,
        has_budget: bool = False,
        has_authority: bool = False,
        is_ideal_customer_profile: bool = False,
    ) -> LeadScore:
        """
        Score lead quality using BANT framework + engagement signals.

        BANT:
        - Budget: Has budget allocated (yes/no)
        - Authority: Decision maker (yes/no)
        - Need: ICP fit (yes/no)
        - Timeline: Active buying cycle (yes/no)
        """

        score = 0.0
        reasons = []

        # Budget (25 points)
        if has_budget:
            score += 25
            reasons.append("Has budget allocated")
        else:
            reasons.append("Budget unclear - qualify")

        # Authority (25 points)
        if has_authority:
            score += 25
            reasons.append("Decision maker identified")
        else:
            reasons.append("Need to find champion")

        # Need/ICP (25 points)
        if is_ideal_customer_profile:
            score += 25
            reasons.append("Ideal customer profile match")
        else:
            reasons.append("Not ideal customer profile")

        # Email engagement (15 points)
        if email_engagement:
            opens = email_engagement.get("opens", 0)
            clicks = email_engagement.get("clicks", 0)
            replies = email_engagement.get("replies", 0)
            engagement_score = (opens * 0.05) + (clicks * 0.05) + (replies * 0.05)
            score += min(engagement_score, 15)
            if engagement_score > 0:
                reasons.append(f"Active email engagement ({opens} opens, {clicks} clicks)")

        # Seniority bonus (10 points)
        if seniority == "c_level":
            score += 10
            reasons.append("C-level contact")
        elif seniority == "vp":
            score += 7
            reasons.append("VP level contact")

        # Company size bonus (depends on ICP)
        if company_size and 100 < company_size < 5000:
            score += 5
            reasons.append("Ideal company size")

        # Determine quality tier
        if score >= 80:
            quality = LeadQuality.HOT
            next_action = "Schedule demo call immediately"
        elif score >= 50:
            quality = LeadQuality.WARM
            next_action = "Send targeted content, qualify further"
        elif score >= 20:
            quality = LeadQuality.COLD
            next_action = "Add to nurture sequence"
        else:
            quality = LeadQuality.DEAD
            next_action = "Remove from active list"

        lead_score = LeadScore(
            contact_id=contact_id,
            quality=quality,
            score=score,
            reasons=reasons,
            next_action=next_action,
        )

        self.lead_scores[contact_id] = lead_score
        return lead_score

    def calculate_customer_health(
        self,
        account_id: str,
        total_revenue: float,
        mrr_change: float,  # Month-over-month MRR change
        days_since_last_activity: int,
        nps_score: Optional[float] = None,
        support_tickets_open: int = 0,
        feature_adoption: float = 0.5,  # 0-1
    ) -> CustomerHealth:
        """
        Calculate customer health score (0-100).

        Factors:
        - MRR trend (growth = healthy)
        - Activity (active usage = healthy)
        - Support issues (open tickets = at risk)
        - NPS (satisfaction indicator)
        - Feature adoption (using product = healthy)
        """

        health_score = 50.0  # Start at neutral

        # MRR trend (±30 points)
        if mrr_change > 0:
            health_score += min(mrr_change / 1000 * 30, 30)  # Growth = +points
        else:
            health_score += max(mrr_change / 1000 * 30, -30)  # Decline = -points

        # Activity (±20 points)
        if days_since_last_activity < 7:
            health_score += 20
        elif days_since_last_activity < 30:
            health_score += 10
        elif days_since_last_activity > 90:
            health_score -= 20

        # Support issues (±15 points)
        if support_tickets_open == 0:
            health_score += 15
        elif support_tickets_open > 5:
            health_score -= 15
        else:
            health_score -= (support_tickets_open * 3)

        # NPS (±15 points)
        if nps_score:
            if nps_score >= 50:
                health_score += 15
            elif nps_score < 0:
                health_score -= 15

        # Feature adoption (±20 points)
        if feature_adoption > 0.7:
            health_score += 20
        elif feature_adoption < 0.3:
            health_score -= 20

        # Clamp 0-100
        health_score = max(0.0, min(100.0, health_score))

        # Determine status + churn risk
        if health_score >= 70:
            status = "healthy"
            churn_prob = 0.05
            expansion_opp = 0.40
        elif health_score >= 40:
            status = "at_risk"
            churn_prob = 0.25
            expansion_opp = 0.20
        else:
            status = "critical"
            churn_prob = 0.70
            expansion_opp = 0.05

        health = CustomerHealth(
            account_id=account_id,
            health_score=health_score,
            status=status,
            churn_probability=churn_prob,
            expansion_opportunity=expansion_opp,
        )

        self.health_scores[account_id] = health
        return health

    def detect_anomalies(self, deal_id: str, recent_activities: list[dict]) -> list[str]:
        """
        Detect unusual deal behavior.

        Anomalies:
        - Sudden activity spike (deal heating up?)
        - Complete inactivity (stalled?)
        - Unexpected stage change (jumping stages?)
        - Negative sentiment shift (tone change in emails?)
        """

        anomalies = []

        if not recent_activities:
            return anomalies

        # Activity trend
        activities_today = len([a for a in recent_activities if a.get("days_ago", 999) == 0])
        activities_last_week = len([a for a in recent_activities if a.get("days_ago", 999) <= 7])

        if activities_today > 5 and activities_last_week < 10:
            anomalies.append("Sudden activity spike — deal heating up?")

        if not activities_last_week and len(recent_activities) > 10:
            anomalies.append("Deal went silent after active period")

        return anomalies

    def get_next_best_actions(self, user_id: str, limit: int = 5) -> list[dict]:
        """
        Recommend top actions for user to increase close rate.

        Logic:
        - High-value deals with low close probability
        - At-risk customers with expansion opportunities
        - Hot leads ready for demo
        - Stalled deals needing intervention
        """

        actions = []

        # Find high-value, at-risk deals
        for deal_id, pred in self.predictions.items():
            if (
                pred.close_probability < 0.5
                and "stalled" not in " ".join(pred.risk_factors).lower()
            ):
                for action in pred.recommended_actions:
                    actions.append(
                        {
                            "type": "deal_intervention",
                            "deal_id": deal_id,
                            "action": action,
                            "priority": 1 - pred.close_probability,
                        }
                    )

        # Find hot leads ready for demo
        for contact_id, score in self.lead_scores.items():
            if score.quality == LeadQuality.HOT:
                actions.append(
                    {
                        "type": "lead_action",
                        "contact_id": contact_id,
                        "action": score.next_action,
                        "priority": score.score / 100,
                    }
                )

        # Find at-risk customers needing attention
        for account_id, health in self.health_scores.items():
            if health.status == "critical":
                actions.append(
                    {
                        "type": "customer_health",
                        "account_id": account_id,
                        "action": f"Urgent: {account_id} at risk of churn",
                        "priority": 1.0,
                    }
                )

        # Sort by priority + limit
        actions.sort(key=lambda x: x["priority"], reverse=True)
        return actions[:limit]


# Singleton instance
ai_manager = AIIntelligenceManager()
