"""Bootstrap Growth — Start from 0 ventas scenario."""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BootstrapGrowth:
    """Strategies for starting from zero."""

    # MVP loops
    MVP_LOOPS = {
        "ecommerce": [
            {"week": 1, "action": "List 10 products", "target": "Initial feedstock"},
            {"week": 2, "action": "Get first 5 sales", "target": "Proof of product-market fit"},
            {"week": 3, "action": "Repeat winning product", "target": "Create first trend"},
            {"week": 4, "action": "Add bundle offers", "target": "Increase AOV"},
        ],
        "service": [
            {"week": 1, "action": "Package service offering", "target": "Clear value prop"},
            {"week": 2, "action": "Get 3 paying customers", "target": "Initial traction"},
            {"week": 3, "action": "Refine based on feedback", "target": "Optimize delivery"},
            {"week": 4, "action": "Create case study", "target": "Social proof"},
        ],
    }

    # Early customer acquisition
    EARLY_ACQUISITION_TACTICS = [
        {"channel": "personal_network", "effort": "1 hour", "expected_customers": 2},
        {"channel": "direct_email", "effort": "2 hours", "expected_customers": 1},
        {"channel": "community", "effort": "3 hours", "expected_customers": 3},
        {"channel": "cold_outreach", "effort": "5 hours", "expected_customers": 5},
    ]

    @staticmethod
    def generate_bootstrap_plan(
        product_category: str,
        target_customers_month1: int = 50,
    ) -> Dict[str, Any]:
        """
        Generate 30-day bootstrap plan from 0 customers.

        Returns:
            {
                "week_1": {...},
                "week_2": {...},
                "week_3": {...},
                "week_4": {...},
                "total_target": int,
                "key_milestones": [list],
            }
        """

        mvp_loop = BootstrapGrowth.MVP_LOOPS.get(product_category, BootstrapGrowth.MVP_LOOPS["ecommerce"])

        return {
            "product_category": product_category,
            "week_1": {
                "goal": f"{target_customers_month1 // 4} customers",
                "tactics": mvp_loop[0] if len(mvp_loop) > 0 else {},
                "metrics": {"acquisitions": target_customers_month1 // 4},
            },
            "week_2": {
                "goal": f"{target_customers_month1 // 4} customers",
                "tactics": mvp_loop[1] if len(mvp_loop) > 1 else {},
                "metrics": {"cumulative": target_customers_month1 // 2},
            },
            "week_3": {
                "goal": f"{target_customers_month1 // 4} customers",
                "tactics": mvp_loop[2] if len(mvp_loop) > 2 else {},
                "metrics": {"cumulative": (target_customers_month1 * 3) // 4},
            },
            "week_4": {
                "goal": f"{target_customers_month1 // 4} customers",
                "tactics": mvp_loop[3] if len(mvp_loop) > 3 else {},
                "metrics": {"cumulative": target_customers_month1},
            },
            "total_target": target_customers_month1,
            "key_milestones": [
                "First customer (Week 1)",
                "5 customers (Week 2)",
                "15 customers (Week 3)",
                "30+ customers (Week 4)",
            ],
        }

    @staticmethod
    def identify_early_adopters(
        network_data: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Identify who should be first customers."""

        characteristics = [
            {"trait": "Problem suffers", "score": 100},
            {"trait": "Active in community", "score": 80},
            {"trait": "Influencer/large network", "score": 70},
            {"trait": "Previous early adopter", "score": 90},
            {"trait": "Vocal about problem", "score": 85},
        ]

        return characteristics

    @staticmethod
    def create_momentum_loops(
        current_users: int,
    ) -> Dict[str, Any]:
        """Create repeatable acquisition loops."""

        return {
            "existing_users": current_users,
            "activation_rate": 0.4,
            "viral_coefficient": 1.2,
            "monthly_organic_growth": current_users * 0.15,  # 15% MoM
            "projected_month_2": int(current_users * 1.15),
        }

    @staticmethod
    def measure_early_success(
        metrics: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Measure if bootstrap phase succeeded."""

        return {
            "initial_customers": metrics.get("customers_month_1", 0),
            "retention_rate": metrics.get("retention_week_2", 0),
            "repeat_purchase_rate": metrics.get("repeat_rate", 0),
            "success": metrics.get("customers_month_1", 0) > 20,
        }
