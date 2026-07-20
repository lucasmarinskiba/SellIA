"""
Financial Agent — Financial modeling and pricing strategy.

Specialties:
- Financial modeling and projections
- Pricing strategy (value-based, dynamic, psychological)
- Gross margin optimization
- Unit economics and CAC/LTV analysis
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class PricingStrategy(str, Enum):
    """Pricing strategies."""
    COST_PLUS = "cost_plus"
    VALUE_BASED = "value_based"
    COMPETITIVE = "competitive"
    DYNAMIC = "dynamic"
    FREEMIUM = "freemium"
    USAGE_BASED = "usage_based"
    TIERED = "tiered"


class FinancialMetric(str, Enum):
    """Financial metrics to track."""
    ARR = "arr"  # Annual Recurring Revenue
    MRR = "mrr"  # Monthly Recurring Revenue
    GROSS_MARGIN = "gross_margin"
    MAGIC_NUMBER = "magic_number"
    BURN_RATE = "burn_rate"
    RUNWAY = "runway"
    CAC = "cac"
    LTV = "ltv"
    ROAS = "roas"


@dataclass
class PricingModel:
    """Pricing model definition."""
    name: str
    description: str
    tiers: List[Dict[str, Any]]
    value_prop_per_tier: Dict[str, str]
    positioning: str
    psychological_factors: List[str]


class FinancialAgent:
    """Expert in financial modeling and pricing."""

    PRICING_STRATEGIES = {
        PricingStrategy.COST_PLUS: {
            "name": "Cost-Plus Pricing",
            "description": "Price = Cost + Markup",
            "formula": "COGS * (1 + markup_percentage)",
            "pros": [
                "Simple to calculate",
                "Ensures profitability",
                "Easy to adjust",
            ],
            "cons": [
                "Ignores customer value",
                "Ignores competition",
                "May leave money on table",
            ],
            "best_for": "B2B services, consulting, manufacturing",
            "typical_markup": "50-200%",
        },

        PricingStrategy.VALUE_BASED: {
            "name": "Value-Based Pricing",
            "description": "Price based on perceived value to customer",
            "approach": [
                "1. Calculate customer value",
                "2. Research willingness to pay",
                "3. Set price to capture portion of value",
            ],
            "pros": [
                "Maximizes profitability",
                "Aligns price with value",
                "Premium positioning",
            ],
            "cons": [
                "Complex to determine value",
                "Requires research",
                "Needs strong positioning",
            ],
            "best_for": "B2B SaaS, premium products",
            "implementation": "Assess customer ROI, perform pricing research",
        },

        PricingStrategy.COMPETITIVE: {
            "name": "Competitive Pricing",
            "description": "Price based on competitor pricing",
            "approach": [
                "1. Research competitor prices",
                "2. Position below, at, or above",
                "3. Monitor and adjust",
            ],
            "pros": [
                "Market-tested",
                "Easy to understand",
                "Lower risk",
            ],
            "cons": [
                "Race to bottom",
                "Ignores your value",
                "Commoditizes offering",
            ],
            "best_for": "Commoditized products, competitive markets",
        },

        PricingStrategy.TIERED: {
            "name": "Tiered Pricing",
            "description": "Multiple price points for different customer segments",
            "tiers": [
                "Starter (small businesses, entry-level)",
                "Professional (growing companies)",
                "Enterprise (large organizations)",
            ],
            "approach": [
                "1. Define tier characteristics",
                "2. Assign features to tiers",
                "3. Price each tier",
                "4. Ensure clear progression",
            ],
            "pros": [
                "Captures multiple segments",
                "Encourages upgrades",
                "Maximizes revenue",
            ],
            "cons": [
                "Complex to manage",
                "Feature cannibalization",
                "Customer confusion",
            ],
            "best_for": "SaaS, software, subscriptions",
        },

        PricingStrategy.DYNAMIC: {
            "name": "Dynamic Pricing",
            "description": "Price changes based on demand, supply, or context",
            "examples": [
                "Airline pricing (demand)",
                "Uber surge pricing (demand)",
                "Retail sales (inventory)",
                "Personalized pricing (customer segment)",
            ],
            "pros": [
                "Maximizes revenue",
                "Adjusts to market conditions",
                "Captures willingness to pay",
            ],
            "cons": [
                "Customer backlash (perceived unfairness)",
                "Complex implementation",
                "Regulatory concerns",
            ],
            "best_for": "E-commerce, services, digital products",
        },

        PricingStrategy.USAGE_BASED: {
            "name": "Usage-Based Pricing",
            "description": "Price based on actual product usage",
            "examples": [
                "AWS (compute hours)",
                "Twilio (SMS/calls)",
                "DataDog (data ingestion)",
            ],
            "pros": [
                "Aligns cost with value",
                "Low entry barrier",
                "Revenue scales with customer success",
            ],
            "cons": [
                "Revenue unpredictable",
                "Pricing complexity",
                "Customer surprise at bill time",
            ],
            "best_for": "Infrastructure, APIs, heavy compute products",
        },
    }

    FINANCIAL_MODELS = {
        "monthly_projection": {
            "description": "Project revenue, costs, and profitability by month",
            "components": [
                "Revenue: MRR, churn, growth",
                "Fixed costs: Salary, rent, tools",
                "Variable costs: COGS, CAC",
                "Cash flow: Inflows, outflows, runway",
            ],
            "duration": "12-24 months",
            "update_frequency": "Monthly with actuals",
        },
        "annual_projection": {
            "description": "Multi-year financial projection",
            "timeline": "3-5 years",
            "components": [
                "Revenue growth rate",
                "Operating expenses",
                "Gross margin development",
                "Break-even point",
            ],
        },
        "scenario_analysis": {
            "description": "Model different business scenarios",
            "scenarios": [
                "Base case: Expected outcome",
                "Optimistic: Best case (50% more growth)",
                "Pessimistic: Worst case (50% less growth)",
            ],
            "use_case": "Risk planning and decision-making",
        },
    }

    GROSS_MARGIN_LEVERS = {
        "pricing": {
            "tactics": [
                "Increase price (if market allows)",
                "Value-based pricing",
                "Remove discounts",
                "Implement tiered pricing",
            ],
            "impact": "Direct increase to margin",
        },
        "product_mix": {
            "tactics": [
                "Shift to higher-margin products",
                "Upsell premium tier",
                "Bundle high-margin items",
                "Phase out low-margin offerings",
            ],
            "impact": "Increase average margin",
        },
        "cogs_reduction": {
            "tactics": [
                "Negotiate supplier costs",
                "Improve production efficiency",
                "Automation",
                "Scale to reduce unit cost",
            ],
            "impact": "Direct increase to margin",
        },
        "delivery_efficiency": {
            "tactics": [
                "Reduce support costs",
                "Self-serve vs. hands-on",
                "Automate delivery",
                "Improve infrastructure efficiency",
            ],
            "impact": "Reduce fulfillment costs",
        },
    }

    PSYCHOLOGICAL_PRICING = {
        "charm_pricing": {
            "description": "End price in 9 or 7 ($9.99 vs $10)",
            "effect": "Appears 20-30% cheaper",
            "best_for": "B2C, e-commerce",
            "caveat": "Diminishes for high prices",
        },
        "anchoring": {
            "description": "Show higher price first to make your price seem good",
            "example": "List suggested price, then show discount",
            "effect": "Increases perceived value",
            "best_for": "E-commerce, sales pages",
        },
        "bundling": {
            "description": "Group products/features together",
            "benefit": "Increases perceived value",
            "example": "Starter bundle vs. à la carte",
        },
        "prestige_pricing": {
            "description": "Higher price signals premium quality",
            "principle": "Price = Quality signal",
            "risk": "Must deliver on quality",
            "best_for": "Luxury, premium positioning",
        },
        "scarcity": {
            "description": "Limited supply or time-limited offers",
            "mechanism": "Creates urgency",
            "tactics": [
                "Limited seats (per tier)",
                "Time-limited pricing",
                "Limited inventory messaging",
            ],
        },
    }

    PRICING_RESEARCH_METHODS = {
        "van_westendorp_price_sensitivity": {
            "description": "Survey to find optimal price",
            "questions": [
                "At what price is this too cheap? (seems low quality)",
                "At what price is this a bargain?",
                "At what price is this expensive?",
                "At what price is this too expensive?",
            ],
            "output": "Price range and optimal price",
            "sample_size": "50-100 target customers",
        },
        "conjoint_analysis": {
            "description": "Test feature combinations and pricing",
            "approach": "Survey showing different packages",
            "output": "Which features/price combination is preferred",
        },
        "competitive_analysis": {
            "description": "Research competitor pricing",
            "approach": [
                "List all direct competitors",
                "Document their pricing",
                "Note included features per tier",
                "Identify positioning gaps",
            ],
        },
        "customer_interviews": {
            "description": "Direct customer research",
            "questions": [
                "What budget do you have?",
                "Would you pay $X?",
                "What would you expect at each price?",
                "What would make this unfeasible?",
            ],
        },
    }

    @staticmethod
    def recommend_pricing_strategy(
        product_type: str,
        target_market: str,
        competition: str,
        business_model: str
    ) -> Dict[str, Any]:
        """Recommend pricing strategy."""
        recommendation = {
            "product_type": product_type,
            "target_market": target_market,
            "competition_level": competition,
            "recommended_strategy": None,
            "rationale": [],
            "alternative_strategies": [],
            "implementation": {},
        }

        if business_model == "subscription":
            recommendation["recommended_strategy"] = PricingStrategy.TIERED.value
        elif product_type == "infrastructure":
            recommendation["recommended_strategy"] = PricingStrategy.USAGE_BASED.value
        elif competition == "high":
            recommendation["recommended_strategy"] = PricingStrategy.VALUE_BASED.value
        else:
            recommendation["recommended_strategy"] = PricingStrategy.COST_PLUS.value

        return recommendation

    @staticmethod
    def create_pricing_model(
        product_name: str,
        target_segments: List[str],
        value_per_segment: Dict[str, float],
        strategy: str
    ) -> Dict[str, Any]:
        """Create detailed pricing model."""
        return {
            "product": product_name,
            "strategy": strategy,
            "tiers": [
                {
                    "name": segment,
                    "price": 0,
                    "annual_price": 0,
                    "value_proposition": value_per_segment.get(segment, ""),
                    "features": [],
                    "target_customer": "",
                    "positioning": "",
                }
                for segment in target_segments
            ],
            "psychological_pricing_tactics": [],
            "projected_conversion_rates": {},
            "revenue_model": {},
        }

    @staticmethod
    def price_sensitivity_analysis(
        current_price: float,
        elasticity: float,
        unit_economics: Dict[str, float]
    ) -> Dict[str, Any]:
        """Analyze price elasticity and impacts."""
        analysis = {
            "current_price": current_price,
            "elasticity": elasticity,
            "scenarios": {},
        }

        for price_change in [-20, -10, 0, 10, 20]:
            new_price = current_price * (1 + price_change / 100)
            demand_change = price_change * elasticity
            revenue_impact = (price_change / 100) + (demand_change / 100)

            analysis["scenarios"][f"{price_change:+d}%"] = {
                "new_price": new_price,
                "demand_change": f"{demand_change:.1f}%",
                "revenue_impact": f"{revenue_impact:.1f}%",
            }

        return analysis

    @staticmethod
    def build_financial_model(
        annual_revenue: float,
        growth_rate_percent: float,
        gross_margin_percent: float,
        monthly_fixed_costs: float,
        starting_cash: float,
        timeline_months: int = 24
    ) -> Dict[str, Any]:
        """Build financial projection model."""
        projection = {
            "assumptions": {
                "starting_annual_revenue": annual_revenue,
                "growth_rate": f"{growth_rate_percent}%",
                "gross_margin": f"{gross_margin_percent}%",
                "monthly_fixed_costs": monthly_fixed_costs,
                "starting_cash": starting_cash,
            },
            "monthly_projections": [],
            "key_metrics": {
                "breakeven_month": None,
                "breakeven_revenue": None,
                "peak_burn": 0,
                "ending_cash": starting_cash,
            },
        }

        monthly_revenue = annual_revenue / 12
        cash = starting_cash
        cumulative_revenue = 0

        for month in range(1, timeline_months + 1):
            # Revenue (grows each month)
            revenue = monthly_revenue * ((1 + growth_rate_percent / 100) ** ((month - 1) / 12))

            # COGS (variable cost)
            cogs = revenue * (1 - gross_margin_percent / 100)

            # Gross profit
            gross_profit = revenue - cogs

            # Operating expenses (fixed)
            operating_costs = monthly_fixed_costs

            # Net profit
            net_profit = gross_profit - operating_costs

            # Cash flow
            cash += net_profit

            cumulative_revenue += revenue

            projection["monthly_projections"].append({
                "month": month,
                "revenue": round(revenue, 2),
                "cogs": round(cogs, 2),
                "gross_profit": round(gross_profit, 2),
                "operating_costs": operating_costs,
                "net_profit": round(net_profit, 2),
                "cash_balance": round(cash, 2),
            })

            # Track breakeven
            if net_profit > 0 and projection["key_metrics"]["breakeven_month"] is None:
                projection["key_metrics"]["breakeven_month"] = month
                projection["key_metrics"]["breakeven_revenue"] = round(cumulative_revenue, 2)

            # Track peak burn
            if net_profit < 0:
                projection["key_metrics"]["peak_burn"] = max(
                    projection["key_metrics"]["peak_burn"],
                    abs(net_profit)
                )

        projection["key_metrics"]["ending_cash"] = round(cash, 2)
        projection["key_metrics"]["runway_months"] = (
            (cash / monthly_fixed_costs) if monthly_fixed_costs > 0 else float('inf')
        )

        return projection

    @staticmethod
    def calculate_unit_economics_detailed(
        arpu: float,
        monthly_churn: float,
        annual_retention: float,
        cac: float,
        cogs_percent: float
    ) -> Dict[str, Any]:
        """Calculate detailed unit economics."""
        # Customer lifetime (months)
        lifetime_months = 12 / (12 * monthly_churn) if monthly_churn > 0 else 120

        # LTV = ARPU * Gross Margin * Customer Lifetime
        gross_margin = 1 - cogs_percent
        ltv = arpu * gross_margin * lifetime_months

        # Payback period = CAC / (ARPU * Gross Margin)
        payback_months = cac / (arpu * gross_margin) if arpu * gross_margin > 0 else 0

        # LTV:CAC ratio
        ltv_to_cac_ratio = ltv / cac if cac > 0 else 0

        return {
            "arpu": arpu,
            "monthly_churn": f"{monthly_churn*100:.1f}%",
            "annual_retention": f"{annual_retention*100:.1f}%",
            "customer_lifetime_months": round(lifetime_months, 1),
            "cac": cac,
            "gross_margin": f"{gross_margin*100:.1f}%",
            "ltv": round(ltv, 2),
            "payback_period_months": round(payback_months, 1),
            "ltv_to_cac_ratio": round(ltv_to_cac_ratio, 2),
            "assessment": FinancialAgent._assess_unit_economics(ltv_to_cac_ratio),
        }

    @staticmethod
    def _assess_unit_economics(ltv_to_cac_ratio: float) -> str:
        """Assess health of unit economics."""
        if ltv_to_cac_ratio < 1:
            return "❌ Negative - Unit economics broken, fix before scaling"
        elif ltv_to_cac_ratio < 3:
            return "⚠️ Weak - Needs improvement before major growth"
        elif ltv_to_cac_ratio < 5:
            return "✓ Good - Healthy unit economics, ready to scale"
        else:
            return "✓✓ Excellent - Strong profitability, can scale aggressively"

    @staticmethod
    def compare_pricing_scenarios(
        scenario_a: Dict[str, Any],
        scenario_b: Dict[str, Any],
        scenario_c: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Compare different pricing scenarios."""
        return {
            "scenarios": {
                "A": scenario_a,
                "B": scenario_b,
                "C": scenario_c,
            },
            "comparison": {
                "revenue_potential": {},
                "customer_attraction": {},
                "positioning": {},
            },
            "recommendation": "",
            "rationale": [],
        }

    @staticmethod
    def optimize_gross_margin(
        current_cogs_percent: float,
        current_price: float,
        target_margin: float
    ) -> Dict[str, Any]:
        """Identify ways to improve gross margin."""
        current_margin = 1 - current_cogs_percent

        return {
            "current_cogs": f"{current_cogs_percent*100:.1f}%",
            "current_margin": f"{current_margin*100:.1f}%",
            "target_margin": f"{target_margin*100:.1f}%",
            "margin_gap": f"{(target_margin - current_margin)*100:.1f}%",
            "levers": [
                {
                    "lever": "Price increase",
                    "impact": "Direct margin increase",
                    "options": [f"${current_price * x:.0f} ({(x-1)*100:+.0f}%)" for x in [1.1, 1.2, 1.3]],
                },
                {
                    "lever": "COGS reduction",
                    "impact": "Lower manufacturing/delivery costs",
                    "tactics": ["Supplier negotiation", "Automation", "Scale efficiency"],
                },
                {
                    "lever": "Product mix",
                    "impact": "Shift to higher-margin items",
                    "tactics": ["Feature deprecation", "Upsell premium", "Bundle differently"],
                },
            ],
        }
