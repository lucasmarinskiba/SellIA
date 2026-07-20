"""Blue Ocean Engine — Estrategias océano azul."""

from dataclasses import dataclass, field
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValueInnovationAnalysis:
    """Blue Ocean Value Innovation analysis."""
    eliminate_factors: List[Dict[str, str]]  # [{"factor": "...", "reason": "..."}]
    reduce_factors: List[Dict[str, Any]]  # [{"factor": "...", "target_level": "..."}]
    raise_factors: List[Dict[str, str]]  # [{"factor": "...", "target": "..."}]
    create_factors: List[Dict[str, str]]  # [{"factor": "...", "benefit": "..."}]
    strategic_reach: str  # "all_customers" or "niche"
    timing_strategy: str  # "pioneer", "follower", "fast_mover"
    expected_market_shift: str
    confidence: float  # 0-1


class BlueOceanEngine:
    """Blue Ocean strategy engine."""

    def __init__(self):
        """Initialize Blue Ocean engine."""
        pass

    def eliminate_factors(
        self,
        industry: str,
        business_profile: "BusinessProfile",
    ) -> List[Dict[str, str]]:
        """
        What factors in the industry DON'T need to exist?

        Example: Taxi industry → eliminate dispatchers → Uber
        Example: Hotel industry → eliminate front desk → Airbnb

        Args:
            industry: Industry identifier
            business_profile: Business profile

        Returns:
            Factors to eliminate with reasoning
        """
        logger.info(f"Analyzing factors to eliminate in {industry}")

        industry_factors = self._get_industry_factors(industry)
        eliminate_list = []

        for factor in industry_factors:
            if self._should_eliminate(factor, business_profile):
                eliminate_list.append({
                    "factor": factor,
                    "reason": self._elimination_reasoning(factor, industry),
                    "cost_savings": self._estimate_savings(factor),
                })

        return eliminate_list

    def reduce_factors(
        self,
        industry: str,
        business_profile: "BusinessProfile",
    ) -> List[Dict[str, Any]]:
        """
        What factors should be REDUCED vs industry norm?

        Example: Zoom → reduce video quality (works on low bandwidth) vs HD

        Args:
            industry: Industry identifier
            business_profile: Business profile

        Returns:
            Factors to reduce with target levels
        """
        logger.info(f"Analyzing factors to reduce in {industry}")

        industry_factors = self._get_industry_factors(industry)
        reduce_list = []

        for factor in industry_factors:
            if self._should_reduce(factor, business_profile):
                current_level = self._get_current_level(factor, industry)
                target_level = self._calculate_target_level(factor, current_level)

                reduce_list.append({
                    "factor": factor,
                    "current_level": current_level,
                    "target_level": target_level,
                    "rationale": self._reduction_rationale(factor, industry),
                })

        return reduce_list

    def raise_factors(
        self,
        industry: str,
        business_profile: "BusinessProfile",
    ) -> List[Dict[str, str]]:
        """
        What factors should be RAISED vs competitors?

        Example: Zoom → raise ease of use (1-click join) vs complicated setup

        Args:
            industry: Industry identifier
            business_profile: Business profile

        Returns:
            Factors to raise with targets
        """
        logger.info(f"Analyzing factors to raise in {industry}")

        raise_list = []

        # Common factors to raise
        raise_candidates = [
            ("ease_of_use", "Simplify user experience dramatically"),
            ("speed", "Faster than any competitor"),
            ("reliability", "99.99% uptime guarantee"),
            ("customer_support", "White-glove concierge service"),
            ("innovation", "Most advanced features"),
            ("sustainability", "Most eco-friendly option"),
        ]

        for factor, benefit in raise_candidates:
            if self._customer_values(factor, business_profile):
                raise_list.append({
                    "factor": factor,
                    "target": f"Top 10% vs competitors",
                    "benefit": benefit,
                    "implementation": self._implementation_steps(factor),
                })

        return raise_list

    def create_factors(
        self,
        industry: str,
        market_data: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """
        What create FACTORS the industry doesn't offer?

        Example: Zoom created simple, free video conferencing for remote work

        Args:
            industry: Industry identifier
            market_data: Market data with trends, unmet needs

        Returns:
            Factors to create with benefits
        """
        logger.info(f"Analyzing factors to create in {industry}")

        market_gaps = market_data.get("unmet_needs", [])
        create_list = []

        for gap in market_gaps:
            create_list.append({
                "factor": gap,
                "benefit": self._benefit_of_new_factor(gap),
                "target_customers": self._identify_target_for_gap(gap),
                "competitive_advantage": "First-mover advantage in new category",
            })

        # Add category creation factor
        if not create_list:
            create_list.append({
                "factor": f"Category: Simple [Industry] for [Target Customer]",
                "benefit": "Own new market category",
                "target_customers": "Early adopters seeking simplicity",
                "competitive_advantage": "Category leadership",
            })

        return create_list

    def evaluate_strategic_reach(
        self,
        business_profile: "BusinessProfile",
        market_data: Dict[str, Any],
    ) -> str:
        """
        Should strategy target ALL customers or NICHE?

        Blue Ocean works better when:
        - Target niche before going mass market
        - Build loyal base of advocates
        - Expand from niche to broader market

        Args:
            business_profile: Business profile
            market_data: Market data

        Returns:
            Strategic reach recommendation: "all_customers" or "niche"
        """
        resources = business_profile.budget_available + (business_profile.financials.annual_revenue * 0.1)

        if resources > 1_000_000:
            return "all_customers"  # Enough resources for mass market
        else:
            return "niche"  # Start with niche, expand later

    def evaluate_timing(
        self,
        industry: str,
        business_profile: "BusinessProfile",
        market_data: Dict[str, Any],
    ) -> str:
        """
        Market timing: when to pioneer, follow, or move fast?

        Strategies:
        - Pioneer: Create new category (high risk/reward)
        - Fast-mover: Follow category creator but dominate (lower risk)
        - Follower: Wait for category to mature (lowest risk)

        Args:
            industry: Industry identifier
            business_profile: Business profile
            market_data: Market data

        Returns:
            Timing strategy: "pioneer", "fast_mover", or "follower"
        """
        market_stage = market_data.get("market_stage", "emerging")
        capital_available = business_profile.budget_available

        if market_stage == "emerging" and capital_available > 500_000:
            return "pioneer"  # Enough capital to create category
        elif market_stage in ["emerging", "early_growth"]:
            return "fast_mover"  # Follow fast after category created
        else:
            return "follower"  # Market mature, compete on execution

    def analyze_value_innovation(
        self,
        industry: str,
        business_profile: "BusinessProfile",
        market_data: Dict[str, Any],
    ) -> ValueInnovationAnalysis:
        """
        Full Blue Ocean value innovation analysis (ERRC).

        ERRC Grid:
        - Eliminate: Remove factors the industry competes on
        - Reduce: Reduce factors to below industry standard
        - Raise: Increase factors above industry standard
        - Create: Create factors the industry never offered

        Args:
            industry: Industry identifier
            business_profile: Business profile
            market_data: Market data

        Returns:
            Complete value innovation analysis
        """
        logger.info(f"Performing Blue Ocean ERRC analysis for {industry}")

        eliminate = self.eliminate_factors(industry, business_profile)
        reduce = self.reduce_factors(industry, business_profile)
        raise_factors = self.raise_factors(industry, business_profile)
        create = self.create_factors(industry, market_data)

        strategic_reach = self.evaluate_strategic_reach(business_profile, market_data)
        timing = self.evaluate_timing(industry, business_profile, market_data)

        return ValueInnovationAnalysis(
            eliminate_factors=eliminate,
            reduce_factors=reduce,
            raise_factors=raise_factors,
            create_factors=create,
            strategic_reach=strategic_reach,
            timing_strategy=timing,
            expected_market_shift=(
                f"Shift from competing on features to competing on {raise_factors[0]['factor'] if raise_factors else 'value'} "
                f"while eliminating {len(eliminate)} costly factors"
            ),
            confidence=0.75,
        )

    # Private helper methods

    def _get_industry_factors(self, industry: str) -> List[str]:
        """Get typical industry competitive factors."""
        industry_factors_map = {
            "commerce": [
                "inventory_size",
                "physical_stores",
                "store_location_quality",
                "brand_advertising",
                "product_variety",
                "price_matching",
                "customer_service_staff",
                "delivery_speed",
            ],
            "real_estate": [
                "fancy_offices",
                "property_size",
                "location_prestige",
                "property_management",
                "luxury_amenities",
                "commission_rates",
                "agent_experience",
            ],
            "saas": [
                "feature_richness",
                "integration_count",
                "support_24_7",
                "on_premise_option",
                "customization",
                "dedicated_account_manager",
                "training_programs",
            ],
            "services": [
                "consultant_prestige",
                "brand_reputation",
                "large_team",
                "luxury_office",
                "extensive_experience",
                "industry_certifications",
                "premium_pricing",
            ],
        }

        return industry_factors_map.get(industry, [
            "price",
            "quality",
            "features",
            "service",
            "brand",
        ])

    def _should_eliminate(self, factor: str, business_profile: "BusinessProfile") -> bool:
        """Determine if factor should be eliminated."""
        # Eliminate if:
        # - High cost
        # - Low customer value
        # - Not part of differentiation
        costly_factors = ["luxury", "size", "premium", "variety", "staff"]
        return any(term in factor.lower() for term in costly_factors)

    def _elimination_reasoning(self, factor: str, industry: str) -> str:
        """Provide reasoning for elimination."""
        return f"Customers don't value {factor} enough to justify cost in {industry}"

    def _estimate_savings(self, factor: str) -> str:
        """Estimate cost savings from elimination."""
        savings_map = {
            "luxury": "20-40%",
            "staff": "15-30%",
            "variety": "10-20%",
            "size": "15-25%",
        }

        for key, value in savings_map.items():
            if key in factor.lower():
                return value

        return "10-15%"

    def _should_reduce(self, factor: str, business_profile: "BusinessProfile") -> bool:
        """Determine if factor should be reduced."""
        # Reduce if not part of value proposition
        return business_profile.differentiation_strategy and factor not in business_profile.differentiation_strategy

    def _get_current_level(self, factor: str, industry: str) -> str:
        """Get current industry level for factor."""
        return "Industry standard"

    def _calculate_target_level(self, factor: str, current_level: str) -> str:
        """Calculate target reduced level."""
        return "50-75% of industry standard"

    def _reduction_rationale(self, factor: str, industry: str) -> str:
        """Provide rationale for reduction."""
        return f"Reduce {factor} to below-industry level while maintaining value perception"

    def _customer_values(self, factor: str, business_profile: "BusinessProfile") -> bool:
        """Check if customers value this factor."""
        # Check against pain points and value proposition
        return factor in str(business_profile.customer_pain_points).lower() or \
               factor in str(business_profile.competitive_advantages).lower()

    def _implementation_steps(self, factor: str) -> List[str]:
        """Steps to improve factor."""
        return [
            f"Assess current {factor} performance",
            f"Identify industry-leading ${factor} approach",
            "Implement improvements",
            "Communicate advantage in marketing",
        ]

    def _benefit_of_new_factor(self, gap: str) -> str:
        """Benefit of addressing market gap."""
        return f"Address unmet customer need: {gap}"

    def _identify_target_for_gap(self, gap: str) -> str:
        """Identify target customers for gap."""
        return "Customers currently dissatisfied with existing solutions"
