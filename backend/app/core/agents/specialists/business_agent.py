"""
Business Agent — Business model design, scaling strategy, and unit economics.

Specialties:
- Business model design and optimization
- Unit economics and profitability analysis
- Scaling strategy (CAC, LTV, payback period)
- Competitive positioning and market analysis
"""

import logging
from typing import Dict, List, Any, Optional
from enum import Enum
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class RevenueModel(str, Enum):
    """Revenue stream types."""
    SUBSCRIPTION = "subscription"
    USAGE_BASED = "usage_based"
    TRANSACTION_FEE = "transaction_fee"
    LICENSING = "licensing"
    MARKETPLACE = "marketplace"
    ADVERTISING = "advertising"
    FREEMIUM = "freemium"
    ONE_TIME_PURCHASE = "one_time_purchase"
    SERVICE_FEES = "service_fees"


class CostType(str, Enum):
    """Cost categories."""
    COGS = "cogs"  # Cost of goods sold
    PAYROLL = "payroll"
    INFRASTRUCTURE = "infrastructure"
    MARKETING = "marketing"
    SALES = "sales"
    SUPPORT = "support"
    ADMIN = "admin"
    R_AND_D = "r_and_d"


@dataclass
class UnitEconomics:
    """Unit economics definition."""
    arpu: float  # Average Revenue Per User
    cac: float  # Customer Acquisition Cost
    payback_period_months: float
    ltv: float  # Customer Lifetime Value
    ltv_to_cac_ratio: float
    gross_margin: float
    retention_rate: float
    churn_rate: float


class BusinessAgent:
    """Expert in business model design and scaling."""

    REVENUE_MODELS = {
        RevenueModel.SUBSCRIPTION: {
            "name": "Subscription",
            "description": "Recurring revenue from customers paying regularly",
            "best_for": "SaaS, software, digital services",
            "pricing_strategies": [
                "Monthly/annual billing",
                "Tiered pricing (Starter/Pro/Enterprise)",
                "Per-user or per-feature pricing",
            ],
            "advantages": [
                "Predictable recurring revenue",
                "Better LTV calculation",
                "Customer lock-in",
            ],
            "challenges": [
                "Churn management",
                "Customer acquisition cost recovery",
                "Feature/value justification",
            ],
            "metrics": ["MRR", "ARR", "Churn rate", "CAC", "LTV"],
        },
        RevenueModel.USAGE_BASED: {
            "name": "Usage-based (Pay-as-you-go)",
            "description": "Customers pay based on actual usage",
            "best_for": "Cloud services, APIs, compute-heavy products",
            "pricing_strategies": [
                "Per-unit pricing",
                "Tiered pricing by volume",
                "Combination of base + usage",
            ],
            "advantages": [
                "Aligns value with payment",
                "Low barrier to entry",
                "Revenue scales with customer success",
            ],
            "challenges": [
                "Revenue unpredictability",
                "Price sensitivity",
                "Complex billing",
            ],
            "metrics": ["ARPU", "Consumption per customer", "Gross margin"],
        },
        RevenueModel.FREEMIUM: {
            "name": "Freemium",
            "description": "Free basic product + paid premium features",
            "best_for": "B2C apps, developer tools, collaboration tools",
            "conversion_strategy": [
                "Feature limits on free tier",
                "Seat/user limits",
                "Storage limits",
                "Support tier limits",
            ],
            "advantages": [
                "High user acquisition",
                "Natural product trial",
                "Brand awareness",
            ],
            "challenges": [
                "Low conversion rates (1-5%)",
                "Support costs for free users",
                "Defining free vs. paid",
            ],
            "metrics": ["Free to paid conversion rate", "Payback period", "Expansion revenue"],
        },
        RevenueModel.MARKETPLACE: {
            "name": "Marketplace",
            "description": "Revenue from transactions between buyers and sellers",
            "best_for": "Two-sided marketplaces, sharing economy",
            "fee_structures": [
                "Transaction fee (% of sale)",
                "Seller commission",
                "Buyer surcharge",
                "Premium seller tiers",
            ],
            "advantages": [
                "Supply creates demand",
                "Scales with network effects",
                "Multiple revenue streams",
            ],
            "challenges": [
                "Chicken-and-egg problem (sellers vs. buyers)",
                "Quality control",
                "Trust and safety",
            ],
            "metrics": ["GMV", "Take rate", "Liquidity ratio", "Network effects"],
        },
    }

    FINANCIAL_METRICS = {
        "gross_margin": {
            "definition": "(Revenue - COGS) / Revenue",
            "benchmarks": {
                "saas": "0.70-0.95",
                "ecommerce": "0.20-0.50",
                "services": "0.40-0.70",
            },
            "importance": "Profit available for operating expenses",
        },
        "magic_number": {
            "definition": "Revenue growth rate / Magic Number (how efficient is growth?)",
            "calculation": "QoQ revenue growth / Sales & Marketing spend",
            "target": "> 0.75",
            "context": "Shows sales & marketing efficiency",
        },
        "burn_rate": {
            "definition": "Monthly cash burn (runway calculation)",
            "calculation": "Monthly operating costs - revenue",
            "runway": "Cash on hand / burn rate",
            "target": "12-24 months runway",
        },
        "rule_of_40": {
            "definition": "Growth rate + profit margin",
            "target": "> 40%",
            "context": "Indicates healthy business (growth OR profitability)",
        },
    }

    CAC_LTV_FRAMEWORK = {
        "customer_acquisition_cost": {
            "definition": "Total sales & marketing spend / New customers",
            "calculation_steps": [
                "1. Sum all sales & marketing expenses for period",
                "2. Count new customers acquired",
                "3. Divide expenses by customers",
            ],
            "optimization": [
                "Improve conversion rate (fewer $ per customer)",
                "Increase AOV (same $ acquires more value)",
                "Reduce payback period (shorter duration)",
            ],
            "payback_period": {
                "definition": "Months to recover CAC through gross profit",
                "calculation": "CAC / (ARPU * gross margin %)",
                "benchmark": "< 12 months",
            },
        },
        "customer_lifetime_value": {
            "definition": "Total profit generated from customer relationship",
            "simple_calculation": "ARPU * gross margin % * avg customer lifetime (months)",
            "advanced_calculation": "Includes retention rates, expansion revenue, referrals",
            "optimization": [
                "Increase ARPU (upsells, cross-sells)",
                "Improve retention (reduce churn)",
                "Expand gross margin (lower COGS)",
                "Extend customer lifetime",
            ],
        },
        "ltv_to_cac_ratio": {
            "definition": "LTV / CAC",
            "benchmarks": {
                "early_stage": "1:1 acceptable",
                "growth_stage": "3:1 target",
                "scale_stage": "5:1+ expected",
            },
            "implications": [
                "3:1 = Business is repeatable and scalable",
                "Below 1:1 = Unsustainable acquisition",
                "> 5:1 = Strong unit economics",
            ],
        },
    }

    SCALING_PRINCIPLES = {
        "unit_economics_first": {
            "principle": "Ensure positive unit economics before scaling",
            "checklist": [
                "LTV:CAC ratio > 3:1",
                "CAC payback < 12 months",
                "Retention rate stable/improving",
                "Gross margin > 60% (SaaS)",
            ],
        },
        "distribution_moat": {
            "principle": "Build defensible advantages in how you acquire customers",
            "strategies": [
                "Network effects (users attract more users)",
                "Community (strong community barrier)",
                "Content/SEO (organic, scalable channels)",
                "Partnerships (exclusive channels)",
                "Brand (premium positioning)",
            ],
        },
        "retention_before_growth": {
            "principle": "High retention enables more growth",
            "logic": "Retain customers → LTV grows → Can spend more on CAC",
            "target_retention": {
                "year_1": "85%+ annual retention",
                "year_2+": "90%+ annual retention",
            },
        },
        "capital_efficiency": {
            "principle": "Grow with minimal capital",
            "metrics": [
                "CAC payback period (shorter = better)",
                "Magic Number (> 0.75)",
                "Burn multiple (lower = better)",
            ],
        },
    }

    COMPETITIVE_POSITIONING = {
        "analysis_framework": {
            "direct_competitors": "Same solution, same market",
            "indirect_competitors": "Different solution, same job to be done",
            "substitutes": "Alternative ways to accomplish job",
            "new_entrants": "Potential future competitors",
        },
        "positioning_strategies": [
            "Cost leadership: Compete on price",
            "Differentiation: Unique features/benefits",
            "Focus: Niche market dominance",
            "Blue ocean: Create new market space",
        ],
    }

    @staticmethod
    def calculate_unit_economics(
        arpu: float,
        cac: float,
        gross_margin: float,
        avg_customer_lifetime_months: int,
        retention_rate: float
    ) -> UnitEconomics:
        """Calculate key unit economics metrics."""
        # LTV calculation
        ltv = arpu * gross_margin * avg_customer_lifetime_months

        # Payback period
        payback_months = cac / (arpu * gross_margin) if arpu * gross_margin > 0 else 0

        # LTV to CAC ratio
        ltv_to_cac = ltv / cac if cac > 0 else 0

        # Churn rate
        churn_rate = 1.0 - retention_rate

        return UnitEconomics(
            arpu=arpu,
            cac=cac,
            payback_period_months=payback_months,
            ltv=ltv,
            ltv_to_cac_ratio=ltv_to_cac,
            gross_margin=gross_margin,
            retention_rate=retention_rate,
            churn_rate=churn_rate,
        )

    @staticmethod
    def assess_scaling_readiness(
        unit_economics: UnitEconomics,
        runway_months: int,
        team_size: int
    ) -> Dict[str, Any]:
        """Assess readiness to scale."""
        readiness = {
            "ready_to_scale": True,
            "score": 0,
            "strengths": [],
            "concerns": [],
            "recommended_actions": [],
        }

        # Unit economics score
        if unit_economics.ltv_to_cac_ratio >= 3:
            readiness["score"] += 35
            readiness["strengths"].append("Strong unit economics (LTV:CAC > 3:1)")
        elif unit_economics.ltv_to_cac_ratio >= 1:
            readiness["score"] += 15
            readiness["concerns"].append(f"Unit economics weak (LTV:CAC = {unit_economics.ltv_to_cac_ratio:.1f}:1)")
        else:
            readiness["ready_to_scale"] = False
            readiness["concerns"].append("Unit economics negative - fix before scaling")

        # Payback period
        if unit_economics.payback_period_months <= 12:
            readiness["score"] += 30
            readiness["strengths"].append(f"Quick payback ({unit_economics.payback_period_months:.0f} months)")
        else:
            readiness["concerns"].append(f"Long payback period ({unit_economics.payback_period_months:.0f} months)")

        # Retention
        if unit_economics.retention_rate >= 0.90:
            readiness["score"] += 20
            readiness["strengths"].append("Good retention (90%+)")
        else:
            readiness["concerns"].append(f"Churn concerns ({unit_economics.churn_rate*100:.0f}% monthly)")

        # Runway
        if runway_months >= 18:
            readiness["score"] += 15
            readiness["strengths"].append(f"Adequate runway ({runway_months} months)")
        else:
            readiness["concerns"].append(f"Limited runway ({runway_months} months)")

        readiness["score"] = min(100, readiness["score"])
        readiness["ready_to_scale"] = readiness["score"] >= 70

        return readiness

    @staticmethod
    def design_business_model(
        business_type: str,
        target_market: str,
        competitive_positioning: str
    ) -> Dict[str, Any]:
        """Design complete business model."""
        return {
            "business_type": business_type,
            "target_market": target_market,
            "competitive_positioning": competitive_positioning,
            "revenue_streams": [],
            "cost_structure": {
                "fixed_costs": [],
                "variable_costs": [],
            },
            "customer_segments": [],
            "value_propositions": [],
            "channels": [],
            "partnerships": [],
            "key_resources": [],
            "key_activities": [],
            "financial_projections": {
                "year_1": {},
                "year_2": {},
                "year_3": {},
            },
        }

    @staticmethod
    def model_financial_scenarios(
        base_case: Dict[str, Any],
        optimistic_case: Dict[str, Any],
        pessimistic_case: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Model financial scenarios."""
        return {
            "base_case": base_case,
            "optimistic_case": optimistic_case,
            "pessimistic_case": pessimistic_case,
            "key_sensitivities": [
                "CAC",
                "Churn rate",
                "ARPU",
                "Implementation timeline",
            ],
            "decision_framework": "Use base case for planning, scenarios for risk management",
        }

    @staticmethod
    def analyze_competitive_position(
        company_positioning: str,
        competitors: List[str],
        market_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze competitive positioning."""
        return {
            "positioning": company_positioning,
            "competitors": [
                {
                    "name": competitor,
                    "strengths": [],
                    "weaknesses": [],
                    "market_share": "",
                }
                for competitor in competitors
            ],
            "differentiation_analysis": {},
            "defensibility": {
                "moats": [],
                "threats": [],
            },
            "market_opportunity": {},
        }

    @staticmethod
    def forecast_growth(
        current_revenue: float,
        growth_rate_percent: float,
        timeline_years: int
    ) -> Dict[str, Any]:
        """Forecast revenue growth."""
        forecast = {
            "current_revenue": current_revenue,
            "growth_rate": f"{growth_rate_percent}%",
            "timeline": f"{timeline_years} years",
            "projected_revenue": {},
            "key_assumptions": [
                f"Constant {growth_rate_percent}% growth rate",
                "No major market changes",
                "Competitive position maintained",
            ],
        }

        revenue = current_revenue
        for year in range(1, timeline_years + 1):
            revenue = revenue * (1 + growth_rate_percent / 100)
            forecast["projected_revenue"][f"year_{year}"] = revenue

        return forecast

    @staticmethod
    def get_revenue_model_guidance(business_type: str) -> Dict[str, Any]:
        """Get revenue model recommendations."""
        recommendations = {
            "business_type": business_type,
            "recommended_models": [],
            "alternative_models": [],
            "comparison": {},
        }

        return recommendations

    @staticmethod
    def optimize_pricing(
        current_price: float,
        elasticity: float,
        cost_to_serve: float
    ) -> Dict[str, Any]:
        """Optimize pricing strategy."""
        return {
            "current_price": current_price,
            "elasticity": elasticity,
            "cost_to_serve": cost_to_serve,
            "suggested_price": current_price,
            "price_sensitivity_analysis": {
                "increase_10_percent": {},
                "decrease_10_percent": {},
            },
            "value_based_pricing": {},
            "competitive_pricing": {},
        }

    @staticmethod
    def calculate_payback_period(
        cac: float,
        arpu: float,
        gross_margin: float,
        monthly_churn: float = 0.05
    ) -> float:
        """Calculate customer acquisition payback period."""
        if arpu * gross_margin == 0:
            return float('inf')

        monthly_profit = arpu * gross_margin
        payback_months = 0
        remaining_cac = cac

        while remaining_cac > 0 and payback_months < 60:  # Cap at 60 months
            remaining_cac -= monthly_profit * (1 - monthly_churn) ** payback_months
            payback_months += 1

        return payback_months
