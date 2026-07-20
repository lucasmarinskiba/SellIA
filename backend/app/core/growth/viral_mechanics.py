"""Viral Mechanics — Referral loops, network effects, organic amplification."""

import logging
from typing import Dict, List, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ViralMechanics:
    """Viral growth mechanics."""

    # Referral incentive models
    REFERRAL_MODELS = {
        "both_benefit": {"referrer": "reward", "referee": "discount"},
        "referrer_only": {"referrer": "cash", "referee": None},
        "tiered": {"referrer": "tiered_rewards", "referee": "escalating_discount"},
    }

    @staticmethod
    def design_referral_loop(
        product_name: str,
        unit_economics: Dict[str, float],
    ) -> Dict[str, Any]:
        """
        Design referral loop maximizing viral coefficient.

        Formula: K = (invites_per_user) * (conversion_rate)
        Target K > 1.0 for exponential growth
        """

        # Baseline assumptions
        invites_per_user = 5  # Average referrals per user
        conversion_rate = 0.15  # 15% convert
        viral_coefficient = invites_per_user * conversion_rate

        # Incentive calculation
        customer_lifetime_value = unit_economics.get("customer_ltv", 500)
        acquisition_cost_without_referral = unit_economics.get("acquisition_cost", 50)

        # Referral incentive budget (can't exceed 50% of LTV)
        max_referral_budget = customer_lifetime_value * 0.5
        referral_incentive = min(50, max_referral_budget / 5)  # Split with referrer

        return {
            "product": product_name,
            "viral_coefficient": round(viral_coefficient, 2),
            "exponential_growth": viral_coefficient > 1.0,
            "invites_per_user": invites_per_user,
            "conversion_rate": conversion_rate,
            "referrer_incentive": f"${referral_incentive}",
            "referee_incentive": f"${referral_incentive}",
            "doubling_time_days": int(30 / viral_coefficient) if viral_coefficient > 0 else None,
        }

    @staticmethod
    def create_content_amplification_strategy() -> Dict[str, Any]:
        """Strategy for users to share content."""

        return {
            "shareable_moments": [
                {"trigger": "First success", "value": "High"},
                {"trigger": "Achievement milestone", "value": "High"},
                {"trigger": "Comparison with competitors", "value": "Medium"},
            ],
            "built_in_sharing": {
                "share_button_placement": "Prominent",
                "pre_filled_message": "Try {product}, it's amazing!",
                "social_proof": "X people already using",
            },
            "community_features": [
                "User profiles",
                "Leaderboards",
                "Badges & achievements",
                "Team/group functionality",
            ],
        }

    @staticmethod
    def calculate_viral_coefficient(
        daily_active_users: int,
        invitations_sent: int,
        new_signups_from_invites: int,
    ) -> Dict[str, Any]:
        """Calculate viral coefficient from actual data."""

        viral_coefficient = (invitations_sent / daily_active_users) * (new_signups_from_invites / invitations_sent) if daily_active_users > 0 else 0

        return {
            "viral_coefficient": round(viral_coefficient, 2),
            "status": "exponential" if viral_coefficient > 1.0 else "linear",
            "growth_mode": "viral" if viral_coefficient > 1.5 else "steady",
            "dau": daily_active_users,
            "invites_per_dau": round(invitations_sent / daily_active_users, 2) if daily_active_users > 0 else 0,
            "conversion_from_invites": round(new_signups_from_invites / invitations_sent * 100, 1) if invitations_sent > 0 else 0,
        }

    @staticmethod
    def optimize_viral_loop(
        current_k: float,
        bottleneck: str,  # "invites" or "conversion"
    ) -> Dict[str, Any]:
        """Suggest optimizations to improve viral coefficient."""

        if bottleneck == "invites":
            tactics = [
                "Add share button to every milestone",
                "Incentivize referrals",
                "Make sharing effortless (1 click)",
                "Create FOMO around features",
            ]
        else:  # conversion
            tactics = [
                "Improve landing page",
                "Add social proof to invite link",
                "Shorten signup process",
                "Offer incentive for clicking link",
            ]

        target_k = 1.5  # Exponential growth

        return {
            "current_k": current_k,
            "target_k": target_k,
            "bottleneck": bottleneck,
            "optimization_tactics": tactics,
            "impact_potential": "High",
        }
