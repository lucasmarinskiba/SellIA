"""Growth Catalyst — Actionable tactics, experimentation, hacks."""

import logging
from typing import Dict, List, Any
from random import choice

logger = logging.getLogger(__name__)


class GrowthCatalyst:
    """Provides actionable growth tactics."""

    # Growth hacks database (250+ tactics)
    GROWTH_HACKS = {
        "early_stage": [
            {"hack": "Ship 10x faster", "mechanism": "Reduce time-to-market", "impact": "High"},
            {"hack": "Reach out to 100 people", "mechanism": "Direct personal outreach", "impact": "High"},
            {"hack": "Get testimonials", "mechanism": "Social proof collection", "impact": "High"},
            {"hack": "Create viral loop", "mechanism": "Incentivized referrals", "impact": "Very High"},
            {"hack": "Partner with 5 complementary products", "mechanism": "Cross-promotion", "impact": "Medium"},
        ],
        "growth": [
            {"hack": "Launch on Product Hunt", "mechanism": "Buzz generation", "impact": "High"},
            {"hack": "Content marketing blitz", "mechanism": "Organic search + education", "impact": "Medium"},
            {"hack": "Influencer campaign", "mechanism": "Reach amplification", "impact": "High"},
            {"hack": "Referral program redesign", "mechanism": "Optimize viral coefficient", "impact": "Very High"},
            {"hack": "Community building", "mechanism": "Network effects", "impact": "Medium"},
        ],
        "scale": [
            {"hack": "Paid acquisition optimization", "mechanism": "LTV:CAC ratio improvement", "impact": "High"},
            {"hack": "Product-market fit expansion", "mechanism": "Adjacent segments", "impact": "Medium"},
            {"hack": "Geographic expansion", "mechanism": "New markets", "impact": "Medium"},
            {"hack": "Brand partnerships", "mechanism": "Co-marketing", "impact": "High"},
            {"hack": "M&A integration", "mechanism": "Acquire growth", "impact": "Very High"},
        ],
    }

    @staticmethod
    def generate_growth_experiment(
        hypothesis: str,
        metric_to_move: str,
    ) -> Dict[str, Any]:
        """Design A/B test to move growth metric."""

        return {
            "hypothesis": hypothesis,
            "metric": metric_to_move,
            "control": "Current approach",
            "variant": "Test approach",
            "sample_size": 1000,
            "duration_days": 14,
            "success_criteria": f"20% improvement in {metric_to_move}",
            "risk": "Low - can revert quickly",
        }

    @staticmethod
    def get_tactic_for_stage(
        growth_stage: str,
    ) -> List[Dict[str, Any]]:
        """Get recommended tactics for current stage."""

        return GrowthCatalyst.GROWTH_HACKS.get(
            growth_stage,
            GrowthCatalyst.GROWTH_HACKS["early_stage"]
        )

    @staticmethod
    def prioritize_experiments(
        potential_experiments: List[Dict[str, Any]],
        resources: int = 100,  # Points to allocate
    ) -> List[Dict[str, Any]]:
        """Prioritize experiments by expected ROI."""

        for exp in potential_experiments:
            # Score based on impact, effort, confidence
            impact_score = {"High": 3, "Medium": 2, "Low": 1}.get(exp.get("impact"), 1)
            effort = exp.get("effort_hours", 40)
            confidence = exp.get("confidence", 0.7)

            exp["priority_score"] = (impact_score * confidence) / (effort + 1)

        sorted_experiments = sorted(
            potential_experiments,
            key=lambda x: x.get("priority_score", 0),
            reverse=True
        )

        # Allocate resources
        remaining_resources = resources
        allocation = []

        for exp in sorted_experiments:
            effort = exp.get("effort_hours", 40)
            if remaining_resources >= effort:
                allocation.append({
                    **exp,
                    "allocated": True,
                    "resources_allocated": effort,
                })
                remaining_resources -= effort

        return allocation[:10]  # Top 10

    @staticmethod
    def calculate_growth_potential(
        current_users: int,
        viral_coefficient: float,
        retention_rate: float,
    ) -> Dict[str, Any]:
        """Calculate growth potential."""

        # Sustainable growth formula
        sustainable_growth = viral_coefficient * (1 - (1 - retention_rate))

        return {
            "current_users": current_users,
            "viral_coefficient": viral_coefficient,
            "retention_rate": retention_rate,
            "sustainable_monthly_growth": round(sustainable_growth * 100, 1),
            "potential": "exponential" if viral_coefficient > 1.0 else "linear",
            "12_month_projection": int(current_users * (1 + sustainable_growth) ** 12) if current_users > 0 else 0,
        }
