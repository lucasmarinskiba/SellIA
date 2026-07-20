"""Financial Optimizer — Optimizar costos, ingresos, márgenes."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class PricingStrategy(str, Enum):
    """Pricing strategy types."""
    COST_PLUS = "cost_plus"
    VALUE_BASED = "value_based"
    COMPETITOR_BASED = "competitor_based"
    DYNAMIC = "dynamic"
    PSYCHOLOGICAL = "psychological"
    FREEMIUM = "freemium"
    TIERED = "tiered"


@dataclass
class PricingRecommendation:
    """Recommended pricing strategy."""
    strategy: PricingStrategy
    recommended_price: float
    price_range_low: float
    price_range_high: float
    expected_conversion_lift: float  # Percentage
    expected_revenue_impact: float  # Percentage
    expected_volume_change: float  # Percentage
    confidence: float
    reasoning: str
    implementation_steps: List[str]


@dataclass
class CostReduction:
    """Cost reduction opportunity."""
    category: str  # COGS, CAC, Operations, etc.
    opportunity: str
    current_cost: float
    potential_savings: float
    savings_percent: float
    implementation_difficulty: str  # easy, medium, hard
    timeline_weeks: int
    risks: List[str]


@dataclass
class MarginImprovement:
    """Margin improvement opportunity."""
    improvement_type: str  # COGS reduction, price increase, mix shift, scale
    gross_margin_impact: float
    net_margin_impact: float
    implementation_steps: List[str]
    timeline_weeks: int
    risks: List[str]


class FinancialOptimizer:
    """Optimizer for pricing, costs, margins."""

    def __init__(self):
        """Initialize financial optimizer."""
        pass

    def optimize_pricing(
        self,
        current_price: float,
        market_data: Dict[str, Any],
        business_profile: "BusinessProfile",
    ) -> PricingRecommendation:
        """
        Maximize revenue + profit through pricing optimization.

        Considers:
        - Price elasticity (small increase = demand drop %)
        - Competitor pricing (lower = more volume, higher = margin)
        - Cost structure (fixed vs variable)
        - Customer value perception
        - Market positioning

        Args:
            current_price: Current selling price
            market_data: Market data (competition, elasticity, etc.)
            business_profile: Business profile

        Returns:
            Pricing recommendation
        """
        logger.info(f"Optimizing pricing: current_price=${current_price}")

        # Calculate elasticity impact
        elasticity = market_data.get("price_elasticity", -1.2)  # Typical: -1 to -2
        competitor_prices = market_data.get("competitor_prices", [current_price])
        avg_competitor_price = sum(competitor_prices) / len(competitor_prices)

        # Evaluate different strategies
        strategies = {
            PricingStrategy.COST_PLUS: self._cost_plus_pricing(current_price, business_profile),
            PricingStrategy.VALUE_BASED: self._value_based_pricing(current_price, market_data),
            PricingStrategy.COMPETITOR_BASED: self._competitor_based_pricing(current_price, competitor_prices),
            PricingStrategy.PSYCHOLOGICAL: self._psychological_pricing(current_price),
        }

        # Select best strategy
        best_strategy = max(
            strategies.items(),
            key=lambda x: x[1]["expected_revenue_impact"],
        )

        strategy_type, strategy_data = best_strategy

        return PricingRecommendation(
            strategy=strategy_type,
            recommended_price=strategy_data["price"],
            price_range_low=strategy_data["price"] * 0.85,
            price_range_high=strategy_data["price"] * 1.15,
            expected_conversion_lift=strategy_data.get("conversion_lift", 0.0),
            expected_revenue_impact=strategy_data.get("revenue_impact", 0.0),
            expected_volume_change=strategy_data.get("volume_change", 0.0),
            confidence=strategy_data.get("confidence", 0.7),
            reasoning=strategy_data.get("reasoning", "Pricing optimization complete"),
            implementation_steps=strategy_data.get("steps", []),
        )

    def reduce_cac(
        self,
        current_cac: float,
        current_acquisition_channels: List[str],
        business_profile: "BusinessProfile",
    ) -> List[CostReduction]:
        """
        Reduce customer acquisition cost.

        Opportunities:
        - Referrals → cheaper than ads
        - Content → builds over time, compounding
        - Product-market fit → word-of-mouth
        - Automation → scale without cost

        Args:
            current_cac: Current customer acquisition cost
            current_acquisition_channels: Channels currently used
            business_profile: Business profile

        Returns:
            List of CAC reduction opportunities
        """
        logger.info(f"Analyzing CAC reduction: current_cac=${current_cac}")

        opportunities = []

        # Opportunity 1: Improve conversion
        if "organic" not in current_acquisition_channels:
            opportunities.append(
                CostReduction(
                    category="CAC",
                    opportunity="Add organic/content channel",
                    current_cost=current_cac,
                    potential_savings=current_cac * 0.3,
                    savings_percent=0.30,
                    implementation_difficulty="medium",
                    timeline_weeks=12,
                    risks=["Slow to ramp", "Requires consistency"],
                )
            )

        # Opportunity 2: Implement referral program
        if "referral" not in current_acquisition_channels:
            opportunities.append(
                CostReduction(
                    category="CAC",
                    opportunity="Launch referral program",
                    current_cost=current_cac,
                    potential_savings=current_cac * 0.4,
                    savings_percent=0.40,
                    implementation_difficulty="easy",
                    timeline_weeks=4,
                    risks=["Requires existing customer base"],
                )
            )

        # Opportunity 3: Improve paid ads efficiency
        if "ads" in current_acquisition_channels:
            opportunities.append(
                CostReduction(
                    category="CAC",
                    opportunity="Optimize ad targeting & messaging",
                    current_cost=current_cac,
                    potential_savings=current_cac * 0.25,
                    savings_percent=0.25,
                    implementation_difficulty="medium",
                    timeline_weeks=6,
                    risks=["Market saturation", "Ad fatigue"],
                )
            )

        return opportunities

    def improve_margins(
        self,
        business_profile: "BusinessProfile",
        market_data: Dict[str, Any] = None,
    ) -> List[MarginImprovement]:
        """
        Improve gross and net margins.

        Levers:
        - Reduce COGS (negotiate suppliers, economies of scale)
        - Reduce delivery costs (logistics optimization)
        - Increase prices (differentiation justifies)
        - Mix optimization (sell high-margin products more)

        Args:
            business_profile: Business profile with financial data
            market_data: Optional market data

        Returns:
            List of margin improvement opportunities
        """
        logger.info(f"Analyzing margin improvements")

        improvements = []
        current_gross_margin = business_profile.financials.gross_margin_percent

        # Opportunity 1: Reduce COGS through supplier negotiation
        if current_gross_margin < 60:
            improvements.append(
                MarginImprovement(
                    improvement_type="COGS reduction via supplier negotiation",
                    gross_margin_impact=0.05,  # 5 percentage points
                    net_margin_impact=0.03,
                    implementation_steps=[
                        "Audit top suppliers",
                        "Identify volume discounts",
                        "Negotiate annually",
                        "Lock in pricing",
                    ],
                    timeline_weeks=12,
                    risks=["Supplier relationships", "Quality risk"],
                )
            )

        # Opportunity 2: Economies of scale
        if business_profile.stage == "growth":
            improvements.append(
                MarginImprovement(
                    improvement_type="Achieve economies of scale",
                    gross_margin_impact=0.03,  # 3 percentage points
                    net_margin_impact=0.08,
                    implementation_steps=[
                        "Increase order volumes",
                        "Reduce per-unit overhead",
                        "Standardize operations",
                    ],
                    timeline_weeks=24,
                    risks=["Working capital needs"],
                )
            )

        # Opportunity 3: Price increase with differentiation
        if "unique" in str(business_profile.competitive_advantages).lower():
            improvements.append(
                MarginImprovement(
                    improvement_type="Premium pricing via differentiation",
                    gross_margin_impact=0.10,  # 10 percentage points
                    net_margin_impact=0.10,
                    implementation_steps=[
                        "Communicate unique value",
                        "Test price increase (5-10%)",
                        "Monitor conversion impact",
                        "Scale if positive",
                    ],
                    timeline_weeks=8,
                    risks=["Customer backlash", "Competitor response"],
                )
            )

        # Opportunity 4: Product mix optimization
        improvements.append(
            MarginImprovement(
                improvement_type="Shift mix toward high-margin products",
                gross_margin_impact=0.07,  # 7 percentage points
                net_margin_impact=0.07,
                implementation_steps=[
                    "Analyze margin by product",
                    "Prioritize high-margin in sales",
                    "Bundle high/low margin products",
                    "Sunset low-margin offerings",
                ],
                timeline_weeks=12,
                risks=["Customer satisfaction", "Volume impact"],
            )
        )

        return improvements

    def optimize_cash_flow(self, business_profile: "BusinessProfile") -> Dict[str, Any]:
        """Optimize working capital and cash flow."""
        financials = business_profile.financials

        recommendations = {
            "payment_terms_to_customers": "Net 30 to reduce receivables",
            "payment_terms_to_suppliers": "Negotiate Net 60 to extend payables",
            "inventory_management": f"Current: {financials.total_assets / max(business_profile.financials.annual_revenue, 1):.1f}x revenue",
            "cash_reserves_target": max(financials.monthly_burn_rate * 6, 10000),
        }

        return recommendations

    # Private helper methods

    def _cost_plus_pricing(
        self,
        current_price: float,
        business_profile: "BusinessProfile",
    ) -> Dict[str, Any]:
        """Cost-plus pricing: cost + markup %."""
        # Simple but ignores market
        return {
            "price": current_price,
            "revenue_impact": 0.0,
            "conversion_lift": 0.0,
            "volume_change": 0.0,
            "confidence": 0.4,
            "reasoning": "Cost-plus is reactive, not optimizing for revenue",
            "steps": ["Calculate unit cost", "Add markup %", "Set price"],
        }

    def _value_based_pricing(
        self,
        current_price: float,
        market_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Value-based pricing: by value delivered."""
        customer_value = market_data.get("customer_value_perception", 1.0)
        optimized_price = current_price * customer_value

        # Estimate impact
        elasticity = market_data.get("price_elasticity", -1.2)
        price_change_percent = (optimized_price - current_price) / current_price
        volume_change = price_change_percent * elasticity

        revenue_impact = price_change_percent + volume_change

        return {
            "price": optimized_price,
            "revenue_impact": revenue_impact,
            "conversion_lift": max(-volume_change * 0.5, 0.0),
            "volume_change": volume_change,
            "confidence": 0.8,
            "reasoning": "Value-based pricing aligns with customer value perception",
            "steps": [
                "Research customer value perception",
                "Map customer segments",
                "Test pricing with surveys",
                "Implement tiered pricing",
            ],
        }

    def _competitor_based_pricing(
        self,
        current_price: float,
        competitor_prices: List[float],
    ) -> Dict[str, Any]:
        """Competitor-based pricing: match/undercut."""
        avg_competitor = sum(competitor_prices) / len(competitor_prices)
        optimized_price = avg_competitor * 0.95  # 5% discount

        return {
            "price": optimized_price,
            "revenue_impact": 0.10,  # Small volume increase
            "conversion_lift": 0.05,
            "volume_change": 0.15,
            "confidence": 0.6,
            "reasoning": "Undercutting competitors increases volume but reduces margin",
            "steps": ["Monitor competitor pricing", "Adjust dynamically", "Set alerts"],
        }

    def _psychological_pricing(self, current_price: float) -> Dict[str, Any]:
        """Psychological pricing: charm pricing, prestige."""
        # Charm pricing: $9.99 instead of $10
        if current_price > 100:
            optimized_price = int(current_price) + 0.99  # Prestige pricing
        else:
            optimized_price = round(current_price * 0.99, 2)  # Charm pricing

        return {
            "price": optimized_price,
            "revenue_impact": 0.08,
            "conversion_lift": 0.05,
            "volume_change": 0.10,
            "confidence": 0.5,
            "reasoning": "Psychological pricing uses perception to boost conversions",
            "steps": ["Adjust price to X.99 or X.95", "Test with cohorts"],
        }
