"""
Customer Loyalty Framework — Retention mastery, NPS optimization, lifetime value.

Estrategias: health scoring, churn prediction, win-back, referral loops, upsell timing.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class CustomerLoyaltyFramework:
    """Maximiza retención + referrals + LTV."""

    # Health scoring thresholds
    HEALTH_SIGNALS = {
        "healthy": {"usage_trend": "up", "engagement": "high", "support_tickets": "low"},
        "at_risk": {"usage_trend": "flat", "engagement": "medium", "support_tickets": "medium"},
        "churn_risk": {"usage_trend": "down", "engagement": "low", "support_tickets": "high"},
    }

    @staticmethod
    def calculate_customer_health_score(customer: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calcula health score 0-100.

        Inputs: usage, engagement, support, nps, time_as_customer.
        Output: score + risk level + recommended action.
        """

        score = 100
        signals = []

        # Usage trend (weight: 30%)
        usage_trend = customer.get("usage_trend", 0)  # -1 to +1
        if usage_trend < -0.3:
            score -= 30
            signals.append("usage_declining")
        elif usage_trend < 0:
            score -= 15
            signals.append("usage_flat")

        # Engagement (weight: 25%)
        engagement_score = customer.get("engagement_score", 50)  # 0-100
        if engagement_score < 30:
            score -= 25
            signals.append("low_engagement")
        elif engagement_score < 60:
            score -= 12
            signals.append("medium_engagement")

        # Support tickets (weight: 20%)
        support_tickets_30d = customer.get("support_tickets_30d", 0)
        if support_tickets_30d > 5:
            score -= 20
            signals.append("high_support_issues")
        elif support_tickets_30d > 2:
            score -= 10
            signals.append("medium_support_issues")

        # Email engagement (weight: 15%)
        email_open_rate = customer.get("email_open_rate", 0)  # 0-1
        if email_open_rate < 0.1:
            score -= 15
            signals.append("no_email_opens")
        elif email_open_rate < 0.3:
            score -= 7
            signals.append("low_email_opens")

        # Time as customer (weight: 10%)
        days_customer = customer.get("days_as_customer", 0)
        if days_customer < 30:
            score -= 5
            signals.append("new_customer")

        # Determine risk level
        if score > 75:
            risk_level = "healthy"
            action = "nurture + upsell opportunity"
        elif score > 50:
            risk_level = "at_risk"
            action = "engagement campaign + check-in call"
        else:
            risk_level = "churn_risk"
            action = "win-back campaign + special offer + executive call"

        return {
            "customer_id": customer.get("id"),
            "health_score": max(score, 0),
            "risk_level": risk_level,
            "signals": signals,
            "recommended_action": action,
        }

    @staticmethod
    def build_win_back_sequence(customer: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Construye win-back sequence para churn-risk customer."""

        return [
            {
                "day": 0,
                "channel": "email",
                "subject": "We miss you!",
                "message": "It's been 30 days. What can we improve?",
                "cta": "Take 2-min survey",
            },
            {
                "day": 3,
                "channel": "email",
                "subject": "Exclusive: 30% off (48h only)",
                "message": f"Special offer just for you",
                "cta": "Claim discount",
            },
            {
                "day": 5,
                "channel": "phone",
                "subject": "Quick check-in",
                "message": "Customer success manager calling",
                "goal": "Understand why, offer solution",
            },
            {
                "day": 7,
                "channel": "sms",
                "subject": "Last chance",
                "message": "Discount expires tonight at midnight",
                "urgency": "high",
            },
        ]

    @staticmethod
    def build_nps_optimization_plan(nps_segments: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Optimiza NPS por segment (promoters, passives, detractors).

        Promoters (9-10): referral engine
        Passives (7-8): engagement + upsell
        Detractors (0-6): support + win-back
        """

        return {
            "promoters": {
                "size": len(nps_segments.get("promoters", [])),
                "goal": "referral machine",
                "tactics": [
                    "Referral program: $100 per signup",
                    "Exclusive preview: new features",
                    "VIP community: exclusive perks",
                    "Case study opportunity: feature story",
                ],
                "kpis": "referral_rate >20%, case_studies 2+/month",
            },
            "passives": {
                "size": len(nps_segments.get("passives", [])),
                "goal": "move to promoter",
                "tactics": [
                    "Engagement email: missing out on value",
                    "Feature education: underutilized benefits",
                    "Upsell timing: based on usage",
                    "Exclusive offer: time-limited discount",
                ],
                "kpis": "conversion_to_promoter >40%",
            },
            "detractors": {
                "size": len(nps_segments.get("detractors", [])),
                "goal": "fix issues or save",
                "tactics": [
                    "Immediate support: dedicated CS manager",
                    "Root cause analysis: why disappointed?",
                    "Special concession: discount, extra features",
                    "Win-back offer: 'give us one more chance'",
                ],
                "kpis": "churn_reduction >50%, detractor_recovery 30%",
            },
        }

    @staticmethod
    def calculate_lifetime_value(customer: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula LTV + predice future value."""

        # LTV = ARPU × margin × lifetime (years)
        arpu = customer.get("monthly_spend", 0)
        margin = customer.get("margin", 0.7)  # 70% margin typical
        cohort_retention = customer.get("cohort_retention", 0.8)  # 80% retention year 1

        # Project 5 years
        ltv = 0
        for year in range(5):
            annual_value = arpu * 12 * cohort_retention ** year * margin
            ltv += annual_value

        # Expansion LTV (upsell, cross-sell)
        expansion_rate = customer.get("expansion_rate", 0.15)  # 15% expansion/year
        expansion_ltv = ltv * (1 + expansion_rate)

        return {
            "current_monthly_spend": arpu,
            "base_ltv": ltv,
            "expansion_ltv": expansion_ltv,
            "payback_period_months": (customer.get("cac", 0) / arpu) if arpu > 0 else 0,
            "ltv_cac_ratio": expansion_ltv / customer.get("cac", 1),
        }

    @staticmethod
    def upsell_timing_engine(customer: Dict[str, Any]) -> Dict[str, Any]:
        """Detecta momento óptimo para upsell (based on usage + adoption)."""

        usage_score = customer.get("feature_adoption_score", 0)  # 0-100
        days_active = customer.get("days_as_customer", 0)

        # Upsell readiness criteria:
        # - 60+ days active
        # - 70%+ feature adoption
        # - No support issues last 30 days

        is_ready = (
            days_active > 60
            and usage_score > 70
            and customer.get("support_tickets_30d", 0) < 2
        )

        if is_ready:
            upsell_type = "upgrade_to_pro" if customer.get("current_plan") == "starter" else "add_on"
            upsell_product = customer.get("next_logical_upsell", "")

            return {
                "ready_for_upsell": True,
                "upsell_type": upsell_type,
                "recommended_product": upsell_product,
                "expected_increase": "30-50%",
                "approach": "feature-education first, then offer",
            }
        else:
            return {
                "ready_for_upsell": False,
                "days_until_ready": max(60 - days_active, 0),
                "next_check": "7 days",
            }
