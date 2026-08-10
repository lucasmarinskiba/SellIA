"""Phase 15: Auto-scaling and performance optimization."""

from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class OptimizationStrategy(str, Enum):
    AGGRESSIVE = "aggressive"  # Max spend to capture market
    BALANCED = "balanced"  # Optimize ROI
    CONSERVATIVE = "conservative"  # Min spend, high ROI
    GROWTH = "growth"  # Focus on volume


@dataclass
class ChannelAllocation:
    channel: str
    recommended_budget: float
    expected_leads: int
    expected_revenue: float
    confidence: float  # 0-1


@dataclass
class OptimizationRecommendation:
    strategy: OptimizationStrategy
    channel_allocations: List[ChannelAllocation]
    total_recommended_budget: float
    expected_total_revenue: float
    expected_roi: float
    rationale: str
    actions: List[str]


class PerformanceOptimizer:
    """Auto-optimize seller performance"""

    def analyze_performance(self, seller_metrics: Dict[str, Any]) -> OptimizationStrategy:
        """Determine optimal strategy based on current performance"""

        roi = seller_metrics.get("roi", 1.0)
        growth_rate = seller_metrics.get("growth_rate", 0.0)
        market_position = seller_metrics.get("market_position", "competitive")

        if roi > 3.0 and growth_rate > 0.20:
            return OptimizationStrategy.AGGRESSIVE
        elif roi > 2.0 and growth_rate > 0.10:
            return OptimizationStrategy.GROWTH
        elif roi > 1.5:
            return OptimizationStrategy.BALANCED
        else:
            return OptimizationStrategy.CONSERVATIVE

    def optimize_channel_spend(
        self, seller_id: str, total_budget: float, strategy: OptimizationStrategy
    ) -> List[ChannelAllocation]:
        """Recommend budget allocation across channels"""

        allocations = []

        # Base allocations by strategy
        if strategy == OptimizationStrategy.AGGRESSIVE:
            channels = {
                "google_maps": 0.30,
                "instagram": 0.25,
                "google_ads": 0.25,
                "facebook_ads": 0.15,
                "linkedin": 0.05
            }
        elif strategy == OptimizationStrategy.GROWTH:
            channels = {
                "google_maps": 0.35,
                "instagram": 0.20,
                "google_ads": 0.20,
                "facebook_ads": 0.15,
                "linkedin": 0.10
            }
        elif strategy == OptimizationStrategy.BALANCED:
            channels = {
                "google_maps": 0.40,
                "whatsapp": 0.20,
                "email": 0.15,
                "instagram": 0.15,
                "linkedin": 0.10
            }
        else:  # CONSERVATIVE
            channels = {
                "google_maps": 0.50,
                "whatsapp": 0.30,
                "email": 0.20
            }

        for channel, pct in channels.items():
            budget = total_budget * pct
            allocation = ChannelAllocation(
                channel=channel,
                recommended_budget=budget,
                expected_leads=int(budget / 10),  # $10 per lead estimate
                expected_revenue=int(budget * 2.5),  # 2.5x ROI target
                confidence=0.85
            )
            allocations.append(allocation)

        return allocations

    def generate_optimization_plan(
        self,
        seller_id: str,
        current_metrics: Dict[str, Any],
        total_budget: float = 1000.0
    ) -> OptimizationRecommendation:
        """Generate complete optimization plan"""

        strategy = self.analyze_performance(current_metrics)
        allocations = self.optimize_channel_spend(seller_id, total_budget, strategy)

        total_expected_leads = sum(a.expected_leads for a in allocations)
        total_expected_revenue = sum(a.expected_revenue for a in allocations)
        expected_roi = total_expected_revenue / total_budget if total_budget > 0 else 0

        rationale = self._generate_rationale(strategy, current_metrics)
        actions = self._generate_actions(strategy, allocations)

        recommendation = OptimizationRecommendation(
            strategy=strategy,
            channel_allocations=allocations,
            total_recommended_budget=total_budget,
            expected_total_revenue=total_expected_revenue,
            expected_roi=expected_roi,
            rationale=rationale,
            actions=actions
        )

        return recommendation

    def _generate_rationale(self, strategy: OptimizationStrategy, metrics: Dict) -> str:
        """Generate explanation for strategy"""
        if strategy == OptimizationStrategy.AGGRESSIVE:
            return "High ROI and growth momentum justify increased spend to capture market share"
        elif strategy == OptimizationStrategy.GROWTH:
            return "Good performance metrics support gradual budget increase for scaling"
        elif strategy == OptimizationStrategy.BALANCED:
            return "Current metrics indicate steady performance - maintain current trajectory"
        else:
            return "Conservative approach recommended - focus on cost efficiency and proven channels"

    def _generate_actions(self, strategy: OptimizationStrategy, allocations: List) -> List[str]:
        """Generate specific implementation steps"""
        actions = [
            f"1. Allocate ${alloc.recommended_budget:.0f} to {alloc.channel}",
            f"2. Monitor daily leads: target {sum(a.expected_leads for a in allocations)} leads",
            f"3. Track conversion rate weekly",
            f"4. Adjust bids based on actual ROI",
            f"5. Review performance bi-weekly"
        ]
        return actions[:5]
