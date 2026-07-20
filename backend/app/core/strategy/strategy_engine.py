"""Strategy Learning Engine — Core learner + evaluator + adapter."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)


class StrategyCategory(str, Enum):
    """Strategy classification categories."""
    BLUE_OCEAN = "blue_ocean"
    RETENTION = "retention"
    ACQUISITION = "acquisition"
    PRICING = "pricing"
    POSITIONING = "positioning"
    GROWTH = "growth"
    NEGOTIATION = "negotiation"


@dataclass
class StrategyScore:
    """Strategy effectiveness score."""
    strategy_id: str
    strategy_name: str
    conversion_rate: float = 0.0  # % of leads converted
    customer_ltv: float = 0.0  # Lifetime value per customer
    customer_cac: float = 0.0  # Cost to acquire customer
    cac_payback_months: float = 0.0  # How many months to recoup CAC
    retention_rate: float = 0.0  # % of customers retained
    gross_margin: float = 0.0  # Margin %
    net_margin: float = 0.0  # Net margin %
    roi: float = 0.0  # Return on investment
    nps_score: float = 0.0  # Net Promoter Score
    confidence: float = 0.0  # Confidence in measurements (0-1)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    notes: str = ""

    def overall_score(self) -> float:
        """Calculate weighted overall strategy effectiveness (0-100)."""
        weights = {
            "conversion_rate": 0.15,
            "ltv": 0.20,
            "cac": -0.15,  # Lower CAC is better
            "roi": 0.25,
            "retention": 0.15,
            "nps": 0.10,
        }

        # Normalize metrics to 0-1 scale
        conversion_norm = min(self.conversion_rate / 0.50, 1.0)  # Good rate: 50%+
        ltv_norm = min(self.customer_ltv / 10000, 1.0)  # Good LTV: $10k+
        cac_norm = max(1.0 - (self.customer_cac / 5000), 0.0)  # Good CAC: <$5k
        roi_norm = min(self.roi / 3.0, 1.0)  # Good ROI: 3x+
        retention_norm = self.retention_rate  # Already 0-1
        nps_norm = (self.nps_score + 100) / 200  # NPS -100 to 100 → 0 to 1

        weighted_score = (
            weights["conversion_rate"] * conversion_norm +
            weights["ltv"] * ltv_norm +
            weights["cac"] * cac_norm +
            weights["roi"] * roi_norm +
            weights["retention"] * retention_norm +
            weights["nps"] * nps_norm
        )

        return min(max(weighted_score * 100, 0), 100)


@dataclass
class RecommendedStrategy:
    """Recommended strategy with confidence and reasoning."""
    strategy_id: str
    strategy_name: str
    category: StrategyCategory
    confidence: float  # 0-1
    priority: int  # 1 = highest priority
    reasoning: str
    key_actions: List[str]
    expected_outcomes: Dict[str, Any]
    constraints: List[str]
    timeline_weeks: int
    required_resources: Dict[str, str]
    risks: List[str]


@dataclass
class AdaptedStrategy:
    """Strategy adapted to market changes."""
    original_strategy_id: str
    adapted_strategy_id: str
    market_shift: str
    changes: List[str]
    new_timeline: int
    risk_level: str  # low, medium, high


class StrategyLearner:
    """Core learner that observes market + sales results → recommends optimal strategy."""

    def __init__(self, memory_days: int = 90):
        """Initialize strategy learner with historical memory window."""
        self.memory_days = memory_days
        self.strategy_history: List[StrategyScore] = []
        self.market_observations: List[Dict[str, Any]] = []
        self.adaptations: List[AdaptedStrategy] = []

    def learn_best_strategy(
        self,
        business_profile: "BusinessProfile",
        market_data: Dict[str, Any],
        sales_history: List[Dict[str, Any]],
    ) -> List[RecommendedStrategy]:
        """
        Observe market + sales results → recommend optimal strategies.

        Args:
            business_profile: Business profile (goals, stage, financials, etc)
            market_data: Market conditions (trends, competition, size, etc)
            sales_history: Historical sales data + KPI results

        Returns:
            Ranked list of strategy recommendations with confidence scores
        """
        logger.info(f"Learning best strategy for {business_profile.business_model}")

        # Analyze current performance
        current_performance = self._analyze_sales_history(sales_history)

        # Identify market opportunities
        market_gaps = self._identify_market_gaps(market_data, business_profile)

        # Evaluate competitive position
        competitive_analysis = self._analyze_competitive_position(
            market_data, business_profile
        )

        # Generate strategy recommendations
        recommendations = self._generate_recommendations(
            business_profile,
            market_data,
            current_performance,
            market_gaps,
            competitive_analysis,
        )

        # Rank by confidence and alignment
        recommendations.sort(key=lambda x: x.confidence * x.priority, reverse=True)

        logger.info(f"Generated {len(recommendations)} strategy recommendations")
        return recommendations

    def evaluate_strategy(
        self,
        strategy_id: str,
        kpi_results: Dict[str, float],
    ) -> StrategyScore:
        """
        Score strategy effectiveness (conversion, LTV, CAC, retention, margin).

        Args:
            strategy_id: Strategy identifier
            kpi_results: KPI measurements (conversions, revenue, costs, etc)

        Returns:
            Strategy score with effectiveness metrics
        """
        score = StrategyScore(
            strategy_id=strategy_id,
            strategy_name=kpi_results.get("strategy_name", strategy_id),
            conversion_rate=kpi_results.get("conversion_rate", 0.0),
            customer_ltv=kpi_results.get("customer_ltv", 0.0),
            customer_cac=kpi_results.get("customer_cac", 0.0),
            cac_payback_months=kpi_results.get("cac_payback_months", 0.0),
            retention_rate=kpi_results.get("retention_rate", 0.0),
            gross_margin=kpi_results.get("gross_margin", 0.0),
            net_margin=kpi_results.get("net_margin", 0.0),
            roi=kpi_results.get("roi", 0.0),
            nps_score=kpi_results.get("nps_score", 0.0),
            confidence=kpi_results.get("confidence", 0.8),
            notes=kpi_results.get("notes", ""),
        )

        self.strategy_history.append(score)
        logger.info(
            f"Evaluated {strategy_id}: overall_score={score.overall_score():.1f}"
        )
        return score

    def adapt_strategy(
        self,
        current_strategy_id: str,
        market_shift: str,
        new_market_data: Dict[str, Any],
    ) -> AdaptedStrategy:
        """
        Market changed → modify current strategy dynamically.

        Args:
            current_strategy_id: Current strategy ID
            market_shift: Description of market change
            new_market_data: Updated market data

        Returns:
            Adapted strategy with modifications
        """
        logger.info(f"Adapting strategy {current_strategy_id} due to: {market_shift}")

        # Analyze impact of market shift
        impact = self._analyze_market_shift_impact(market_shift, new_market_data)

        # Determine required adaptations
        changes = self._determine_strategy_adaptations(impact)

        # Calculate new timeline
        new_timeline = self._calculate_adaptation_timeline(changes)

        adapted = AdaptedStrategy(
            original_strategy_id=current_strategy_id,
            adapted_strategy_id=f"{current_strategy_id}_v{len(self.adaptations) + 1}",
            market_shift=market_shift,
            changes=changes,
            new_timeline=new_timeline,
            risk_level=self._assess_adaptation_risk(changes),
        )

        self.adaptations.append(adapted)
        return adapted

    # Private helper methods

    def _analyze_sales_history(self, sales_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze historical sales data to understand what works."""
        if not sales_history:
            return {
                "total_leads": 0,
                "total_conversions": 0,
                "conversion_rate": 0.0,
                "avg_deal_size": 0.0,
                "avg_ltv": 0.0,
                "churn_rate": 0.0,
                "success_factors": [],
            }

        total_leads = sum(h.get("leads", 0) for h in sales_history)
        total_conversions = sum(h.get("conversions", 0) for h in sales_history)
        conversion_rate = total_conversions / total_leads if total_leads > 0 else 0.0

        avg_deal_size = sum(h.get("deal_size", 0) for h in sales_history) / len(sales_history)
        avg_ltv = sum(h.get("ltv", 0) for h in sales_history) / len(sales_history)
        churn_rate = sum(h.get("churn_rate", 0) for h in sales_history) / len(sales_history)

        # Identify success factors
        success_factors = [
            h.get("success_factor", "")
            for h in sales_history
            if h.get("success_factor")
        ]

        return {
            "total_leads": total_leads,
            "total_conversions": total_conversions,
            "conversion_rate": conversion_rate,
            "avg_deal_size": avg_deal_size,
            "avg_ltv": avg_ltv,
            "churn_rate": churn_rate,
            "success_factors": success_factors,
        }

    def _identify_market_gaps(
        self,
        market_data: Dict[str, Any],
        business_profile: "BusinessProfile",
    ) -> List[str]:
        """Identify unmet market needs."""
        gaps = []

        if market_data.get("unmet_needs"):
            gaps.extend(market_data.get("unmet_needs", []))

        if market_data.get("competitor_weaknesses"):
            gaps.extend(market_data.get("competitor_weaknesses", []))

        # Check customer pain points
        if business_profile.customer_pain_points:
            gaps.extend(business_profile.customer_pain_points)

        return gaps

    def _analyze_competitive_position(
        self,
        market_data: Dict[str, Any],
        business_profile: "BusinessProfile",
    ) -> Dict[str, Any]:
        """Evaluate competitive advantages and weaknesses."""
        return {
            "strengths": business_profile.competitive_advantages or [],
            "weaknesses": market_data.get("competitor_threats", []),
            "opportunities": self._identify_market_gaps(market_data, business_profile),
            "market_share": business_profile.market_position,
            "differentiation": business_profile.differentiation_strategy or [],
        }

    def _generate_recommendations(
        self,
        business_profile: "BusinessProfile",
        market_data: Dict[str, Any],
        current_performance: Dict[str, Any],
        market_gaps: List[str],
        competitive_analysis: Dict[str, Any],
    ) -> List[RecommendedStrategy]:
        """Generate strategy recommendations based on analysis."""
        recommendations = []

        # 1. Blue Ocean recommendation (if applicable)
        if not competitive_analysis["weaknesses"]:
            recommendations.append(self._recommend_blue_ocean(business_profile))

        # 2. Acquisition recommendation
        if current_performance["conversion_rate"] < 0.3:
            recommendations.append(self._recommend_acquisition_strategy(business_profile))

        # 3. Retention recommendation
        if current_performance["churn_rate"] > 0.15:
            recommendations.append(self._recommend_retention_strategy(business_profile))

        # 4. Pricing optimization recommendation
        if market_data.get("pricing_opportunity"):
            recommendations.append(self._recommend_pricing_strategy(business_profile))

        # 5. Growth recommendation
        if business_profile.stage in ["growth", "scale"]:
            recommendations.append(self._recommend_growth_strategy(business_profile))

        return recommendations

    def _recommend_blue_ocean(self, business_profile: "BusinessProfile") -> RecommendedStrategy:
        """Recommend Blue Ocean strategy."""
        return RecommendedStrategy(
            strategy_id="blue_ocean_01",
            strategy_name="Blue Ocean - Uncontested Market Space",
            category=StrategyCategory.BLUE_OCEAN,
            confidence=0.75,
            priority=1,
            reasoning="Create uncontested market space through value innovation",
            key_actions=[
                "Identify factors to eliminate (reduce cost)",
                "Identify factors to reduce (simplify offering)",
                "Identify factors to raise (improve quality)",
                "Identify factors to create (new value)",
            ],
            expected_outcomes={
                "market_differentiation": "high",
                "price_premium": "10-30%",
                "brand_positioning": "unique",
            },
            constraints=[
                "Requires clear value proposition",
                "Market timing critical",
            ],
            timeline_weeks=12,
            required_resources={
                "strategy_development": "2-4 weeks",
                "implementation": "4-8 weeks",
                "marketing": "ongoing",
            },
            risks=[
                "Market may not adopt new category",
                "Competitors may follow quickly",
            ],
        )

    def _recommend_acquisition_strategy(self, business_profile: "BusinessProfile") -> RecommendedStrategy:
        """Recommend customer acquisition strategy."""
        return RecommendedStrategy(
            strategy_id="acquisition_01",
            strategy_name="Optimized Customer Acquisition",
            category=StrategyCategory.ACQUISITION,
            confidence=0.85,
            priority=2,
            reasoning="Improve conversion rates through targeted channels",
            key_actions=[
                "Analyze best-performing acquisition channels",
                "Optimize high-converting messaging",
                "Test new channels with small budgets",
                "Scale winning channels gradually",
            ],
            expected_outcomes={
                "conversion_rate_improvement": "20-50%",
                "cac_reduction": "15-30%",
            },
            constraints=["Budget constraints", "Skill availability"],
            timeline_weeks=8,
            required_resources={
                "marketing_budget": "dependent",
                "analytics": "1 person",
            },
            risks=["CAC may increase with scaling"],
        )

    def _recommend_retention_strategy(self, business_profile: "BusinessProfile") -> RecommendedStrategy:
        """Recommend retention strategy."""
        return RecommendedStrategy(
            strategy_id="retention_01",
            strategy_name="Customer Retention & NPS Growth",
            category=StrategyCategory.RETENTION,
            confidence=0.80,
            priority=1,
            reasoning="Reduce churn and build loyal customer base",
            key_actions=[
                "Implement NPS tracking",
                "Create proactive support system",
                "Build customer community",
                "Develop win-back campaigns for churned",
            ],
            expected_outcomes={
                "churn_reduction": "10-25%",
                "ltv_increase": "20-50%",
                "nps_improvement": "15-30 points",
            },
            constraints=["Team capacity", "Customer data"],
            timeline_weeks=6,
            required_resources={
                "support_team": "1-2 people",
                "community_platform": "needed",
            },
            risks=["May take time to show results"],
        )

    def _recommend_pricing_strategy(self, business_profile: "BusinessProfile") -> RecommendedStrategy:
        """Recommend pricing optimization strategy."""
        return RecommendedStrategy(
            strategy_id="pricing_01",
            strategy_name="Value-Based Pricing Optimization",
            category=StrategyCategory.PRICING,
            confidence=0.70,
            priority=2,
            reasoning="Optimize price based on customer value perception",
            key_actions=[
                "Map customer segments and willingness to pay",
                "Test price points with small cohorts",
                "Implement tiered pricing structure",
                "Monitor price elasticity",
            ],
            expected_outcomes={
                "revenue_increase": "15-40%",
                "margin_improvement": "10-25%",
            },
            constraints=["Market sensitivity", "Competition"],
            timeline_weeks=10,
            required_resources={
                "pricing_analyst": "1 person",
                "a_b_testing": "capability",
            },
            risks=["Customer backlash", "Reduced volume"],
        )

    def _recommend_growth_strategy(self, business_profile: "BusinessProfile") -> RecommendedStrategy:
        """Recommend growth strategy."""
        return RecommendedStrategy(
            strategy_id="growth_01",
            strategy_name="Scalable Growth Framework",
            category=StrategyCategory.GROWTH,
            confidence=0.75,
            priority=1,
            reasoning="Execute repeatable, scalable growth playbook",
            key_actions=[
                "Build repeatable sales process",
                "Develop marketing automation",
                "Establish product-market fit metrics",
                "Plan expansion into new segments",
            ],
            expected_outcomes={
                "revenue_growth": "50-100% YoY",
                "unit_economics_improvement": "20-40%",
            },
            constraints=["Funding", "Talent", "Systems"],
            timeline_weeks=16,
            required_resources={
                "operations": "2-3 people",
                "technology": "tools & infrastructure",
            },
            risks=["Over-expansion", "Quality degradation"],
        )

    def _analyze_market_shift_impact(
        self,
        market_shift: str,
        new_market_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze impact of market changes."""
        return {
            "shift_description": market_shift,
            "affected_channels": new_market_data.get("affected_channels", []),
            "competitive_impact": new_market_data.get("competitive_impact", "unknown"),
            "urgency": new_market_data.get("urgency", "medium"),
            "opportunities": new_market_data.get("opportunities", []),
        }

    def _determine_strategy_adaptations(self, impact: Dict[str, Any]) -> List[str]:
        """Determine what strategy changes are needed."""
        changes = []

        if impact.get("affected_channels"):
            changes.append("Shift budget away from affected channels")

        if "high" in impact.get("urgency", ""):
            changes.append("Execute changes immediately")

        if impact.get("opportunities"):
            changes.append("Capitalize on new market opportunities")

        return changes or ["Review and adjust current approach"]

    def _calculate_adaptation_timeline(self, changes: List[str]) -> int:
        """Calculate weeks needed for adaptation."""
        return min(4 + len(changes) * 2, 12)  # 4-12 weeks

    def _assess_adaptation_risk(self, changes: List[str]) -> str:
        """Assess risk level of adaptation."""
        if len(changes) > 3:
            return "high"
        elif len(changes) > 1:
            return "medium"
        return "low"
