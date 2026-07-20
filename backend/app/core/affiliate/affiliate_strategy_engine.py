"""Affiliate Strategy Engine — Select best strategies for product/market."""

from typing import Dict, List, Optional
from dataclasses import dataclass
from .affiliate_sales_methods import AffiliateMethod, get_best_methods_for_product

@dataclass
class AffiliateStrategy:
    """Complete affiliate strategy for product."""
    product_id: str
    product_name: str
    platform: str
    target_audience: List[str]
    primary_methods: List[AffiliateMethod]
    secondary_methods: List[AffiliateMethod]
    estimated_monthly_revenue: float
    time_to_first_sale: str
    required_resources: Dict[str, int]  # budget, time, channels
    success_metrics: Dict[str, float]

class AffiliateStrategyEngine:
    """Engine for selecting optimal affiliate strategies."""

    def __init__(self):
        self.strategies: Dict[str, AffiliateStrategy] = {}

    def generate_strategy(
        self,
        product_id: str,
        product_name: str,
        product_type: str,
        platform: str,
        target_audience: List[str],
        budget: str = "medium",
        timeline: str = "3_months",
    ) -> AffiliateStrategy:
        """Generate optimal affiliate strategy for product."""

        methods = get_best_methods_for_product(product_type, budget)
        primary = methods[:3] if len(methods) >= 3 else methods
        secondary = methods[3:6] if len(methods) > 3 else []

        strategy = AffiliateStrategy(
            product_id=product_id,
            product_name=product_name,
            platform=platform,
            target_audience=target_audience,
            primary_methods=primary,
            secondary_methods=secondary,
            estimated_monthly_revenue=self._estimate_revenue(
                primary, product_type
            ),
            time_to_first_sale=self._estimate_time_to_sale(primary),
            required_resources=self._estimate_resources(primary, budget),
            success_metrics=self._define_metrics(product_type),
        )

        self.strategies[product_id] = strategy
        return strategy

    def _estimate_revenue(self, methods: List[AffiliateMethod], product_type: str) -> float:
        """Estimate monthly revenue from methods."""
        if not methods:
            return 0
        avg_roi = sum(m.roi_potential for m in methods) / len(methods)
        base_revenue = 1000  # Conservative base
        return base_revenue * (avg_roi / 5)  # Scale by ROI

    def _estimate_time_to_sale(self, methods: List[AffiliateMethod]) -> str:
        """Estimate time to first sale."""
        if not methods:
            return "unknown"
        times = [m.time_to_conversion for m in methods]
        order = {"days": 0, "weeks": 1, "months": 2}
        avg_time = sum(order.get(t, 3) for t in times) / len(times)
        if avg_time < 0.5:
            return "days"
        elif avg_time < 1.5:
            return "weeks"
        return "months"

    def _estimate_resources(self, methods: List[AffiliateMethod], budget: str) -> Dict[str, int]:
        """Estimate required resources."""
        budget_map = {"low": 500, "medium": 2000, "high": 10000}
        effort = sum(m.effort_level for m in methods) / len(methods) if methods else 5
        return {
            "budget_usd": budget_map.get(budget, 2000),
            "hours_per_week": int(effort * 2),
            "channels_required": len(methods),
        }

    def _define_metrics(self, product_type: str) -> Dict[str, float]:
        """Define success metrics."""
        return {
            "clicks_target": 1000,
            "conversion_rate_target": 0.02,
            "revenue_target": 2000,
            "roi_target": 3.0,
        }

    def recommend_quick_wins(self) -> List[AffiliateMethod]:
        """Recommend quick-win methods (fast to setup, good ROI)."""
        all_strategies = list(self.strategies.values())
        quick_wins = []
        for strategy in all_strategies:
            quick_wins.extend(strategy.primary_methods)

        sorted_wins = sorted(
            quick_wins,
            key=lambda m: (
                {"days": 0, "weeks": 1, "months": 2}.get(m.time_to_conversion, 3),
                -m.roi_potential,
            ),
        )
        return sorted_wins[:5]

    def optimize_strategy(self, product_id: str, performance_data: Dict) -> AffiliateStrategy:
        """Optimize strategy based on performance data."""
        strategy = self.strategies.get(product_id)
        if not strategy:
            return None

        # If primary methods underperforming, shift to secondary
        clicks = performance_data.get("clicks", 0)
        conversions = performance_data.get("conversions", 0)
        conversion_rate = conversions / clicks if clicks > 0 else 0

        if conversion_rate < 0.01:  # Below 1% conversion
            strategy.primary_methods = strategy.secondary_methods
            strategy.secondary_methods = []

        return strategy
