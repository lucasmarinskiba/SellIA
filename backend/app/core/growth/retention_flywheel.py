"""Retention Flywheel — Onboarding, activation, habit loops, win-backs."""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class RetentionFlywheel:
    """Maximize retention through flywheel."""

    # Onboarding stages
    ONBOARDING_STAGES = {
        "welcome": {"duration_hours": 1, "goal": "First impression"},
        "setup": {"duration_hours": 2, "goal": "Configure basics"},
        "first_action": {"duration_hours": 1, "goal": "First win"},
        "habit_formation": {"duration_days": 21, "goal": "Regular usage"},
    }

    # Activation triggers
    ACTIVATION_TRIGGERS = {
        "first_successful_outcome": 0.3,  # 30% conversion
        "shared_with_friend": 0.25,  # 25% conversion
        "customized_settings": 0.4,  # 40% conversion
        "completed_onboarding": 0.35,  # 35% conversion
    }

    @staticmethod
    def design_onboarding_flow(
        product_type: str,
    ) -> Dict[str, Any]:
        """Design optimal onboarding sequence."""

        flows = {
            "ecommerce": [
                {"step": 1, "action": "Show top 3 products", "time": "10 seconds"},
                {"step": 2, "action": "First purchase incentive", "time": "2 minutes"},
                {"step": 3, "action": "Cart abandoned recovery", "time": "24 hours"},
                {"step": 4, "action": "Repeat purchase email", "time": "7 days"},
            ],
            "saas": [
                {"step": 1, "action": "Tour of key features", "time": "5 minutes"},
                {"step": 2, "action": "First project setup", "time": "10 minutes"},
                {"step": 3, "action": "First success email", "time": "1 day"},
                {"step": 4, "action": "Advanced features unlock", "time": "7 days"},
            ],
        }

        return flows.get(product_type, flows["saas"])

    @staticmethod
    def identify_activation_moment(
        user_actions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Identify when user becomes activated."""

        activation_actions = [
            "first_purchase",
            "first_share",
            "first_review",
            "first_interaction",
            "settings_customized",
        ]

        activated = False
        activation_time = None

        for action in user_actions:
            if action.get("action_type") in activation_actions:
                activated = True
                activation_time = action.get("timestamp")
                break

        return {
            "activated": activated,
            "activation_time": activation_time,
            "activation_action": "See logs for details",
            "time_to_activation": "Calculate from signup",
        }

    @staticmethod
    def build_habit_loop(
        trigger: str,
        action: str,
        reward: str,
    ) -> Dict[str, Any]:
        """Design habit loop (from Nir Eyal's Hooked)."""

        return {
            "trigger": trigger,
            "action": action,
            "reward": reward,
            "investment": "Make next loop more powerful",
            "cycle_time_days": 1,
            "target_cycles_per_week": 7,  # Daily habit
            "example": {
                "trigger": f"Daily notification: 'Check your {trigger}'",
                "action": f"Open app, {action}",
                "reward": "Points/progress shown",
                "investment": "Share results, unlock new features",
            },
        }

    @staticmethod
    def predict_churn_risk(
        days_since_last_action: int,
        engagement_score: float,
    ) -> Dict[str, Any]:
        """Predict if user is at risk of churning."""

        churn_risk = 0
        actions = []

        if days_since_last_action > 30:
            churn_risk += 0.6
            actions.append("Send re-engagement email within 1 day")

        if engagement_score < 0.3:
            churn_risk += 0.2
            actions.append("Offer special incentive to return")

        if days_since_last_action > 60:
            churn_risk = 0.9
            actions = ["Launch win-back campaign", "Final offer before churn"]

        return {
            "churn_risk": round(min(1.0, churn_risk), 2),
            "risk_level": "critical" if churn_risk > 0.6 else "high" if churn_risk > 0.3 else "low",
            "days_inactive": days_since_last_action,
            "engagement_score": engagement_score,
            "recommended_actions": actions,
        }

    @staticmethod
    def design_winback_campaign(
        inactive_users: int,
    ) -> Dict[str, Any]:
        """Design win-back campaign for inactive users."""

        return {
            "target_segment": "Inactive users",
            "segment_size": inactive_users,
            "campaign_sequence": [
                {
                    "day": 1,
                    "message": "We miss you! Here's what's new",
                    "expected_return": 0.05,  # 5%
                },
                {
                    "day": 3,
                    "message": "Exclusive offer for you",
                    "expected_return": 0.03,  # 3%
                },
                {
                    "day": 7,
                    "message": "Last chance offer",
                    "expected_return": 0.02,  # 2%
                },
            ],
            "expected_total_return": 0.10,  # 10%
            "expected_reactivated_users": int(inactive_users * 0.10),
        }

    @staticmethod
    def calculate_lifetime_value(
        monthly_revenue_per_user: float,
        monthly_churn_rate: float,
    ) -> Dict[str, Any]:
        """Calculate customer LTV."""

        months = 1 / monthly_churn_rate if monthly_churn_rate > 0 else 120

        ltv = monthly_revenue_per_user * months

        return {
            "monthly_revenue": monthly_revenue_per_user,
            "monthly_churn_rate": round(monthly_churn_rate * 100, 1),
            "average_lifetime_months": round(months, 1),
            "lifetime_value": round(ltv, 2),
            "implication": "Focus on retention" if monthly_churn_rate > 0.15 else "Acquisition leverage",
        }

    @staticmethod
    def measure_retention_effectiveness(
        cohort_size: int,
        retained_week_1: int,
        retained_week_4: int,
        retention_improvement: float,
    ) -> Dict[str, Any]:
        """Measure effectiveness of retention initiatives."""

        return {
            "cohort_size": cohort_size,
            "week_1_retention": round(retained_week_1 / cohort_size * 100, 1),
            "week_4_retention": round(retained_week_4 / cohort_size * 100, 1),
            "improvement_from_baseline": round(retention_improvement * 100, 1),
            "ltv_impact": f"+{round(retention_improvement * 15, 1)}%",  # Rough estimate
            "recommendation": "Scale retention initiatives" if retention_improvement > 0.1 else "Test more variations",
        }
