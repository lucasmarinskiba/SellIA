"""Network Effects — User-user interactions, platform dynamics."""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class NetworkEffects:
    """Leverage network effects for exponential growth."""

    @staticmethod
    def model_network_effect(
        current_users: int,
        network_strength: float = 0.5,  # 0-1 scale
    ) -> Dict[str, Any]:
        """
        Model Metcalfe's Law: Value = k * n^2

        More users = exponentially more value = exponential growth
        """

        # Metcalfe's law
        value_index = network_strength * (current_users ** 2) / 1000
        value_per_user = value_index / current_users if current_users > 0 else 0

        return {
            "total_users": current_users,
            "value_index": int(value_index),
            "value_per_user": round(value_per_user, 2),
            "network_strength": network_strength,
            "growth_driver": "Network effects" if network_strength > 0.3 else "Individual value",
        }

    @staticmethod
    def create_two_sided_marketplace() -> Dict[str, Any]:
        """Design two-sided marketplace dynamics."""

        return {
            "side_a": "Sellers",
            "side_b": "Buyers",
            "critical_mass_sellers": 50,  # Minimum for viability
            "critical_mass_buyers": 100,
            "supply_side_incentive": "Commission + visibility",
            "demand_side_incentive": "Selection + deals",
            "chicken_egg_problem": "Start with one side through subsidies",
        }

    @staticmethod
    def design_community_features() -> List[Dict[str, Any]]:
        """Design community features that amplify network effects."""

        return [
            {
                "feature": "User profiles",
                "network_effect": "Social proof + discoverable expertise",
            },
            {
                "feature": "Comments/reviews",
                "network_effect": "User-generated content creates stickiness",
            },
            {
                "feature": "Leaderboards",
                "network_effect": "Status competition drives engagement",
            },
            {
                "feature": "Groups/teams",
                "network_effect": "Sub-network lock-in",
            },
            {
                "feature": "Collaborative tools",
                "network_effect": "Coordination costs drop with scale",
            },
        ]

    @staticmethod
    def calculate_critical_mass(
        total_market_size: int,
        penetration_target_percent: float = 0.01,  # 1%
    ) -> Dict[str, Any]:
        """Calculate critical mass needed for network effects to kick in."""

        critical_mass = int(total_market_size * penetration_target_percent)

        return {
            "total_addressable_market": total_market_size,
            "penetration_target": f"{penetration_target_percent * 100}%",
            "critical_mass_users": critical_mass,
            "months_to_critical_mass": int(critical_mass / 30),  # Estimate at 30 users/month
            "network_effects_threshold": "Reaches inflection point",
        }
