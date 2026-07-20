"""Business Analyzer — Parse business profile → structured data for strategy selection."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class BusinessStage(str, Enum):
    """Business maturity stages."""
    STARTUP = "startup"  # Pre-revenue or <$100k ARR
    GROWTH = "growth"  # $100k-$1M ARR, 30%+ MoM growth
    SCALE = "scale"  # $1M-$10M ARR, 15-30% MoM growth
    MATURE = "mature"  # $10M+ ARR, <15% MoM growth


class BusinessModel(str, Enum):
    """Business model types."""
    B2B = "B2B"  # Business to Business
    B2C = "B2C"  # Business to Consumer
    D2C = "D2C"  # Direct to Consumer
    MARKETPLACE = "marketplace"
    SAAS = "SaaS"
    SERVICES = "services"
    SUBSCRIPTION = "subscription"
    HYBRID = "hybrid"


@dataclass
class FinancialProfile:
    """Financial metrics and structure."""
    annual_revenue: float = 0.0
    monthly_recurring_revenue: float = 0.0
    customer_count: int = 0
    customer_acquisition_cost: float = 0.0
    customer_lifetime_value: float = 0.0
    gross_margin_percent: float = 0.0
    net_margin_percent: float = 0.0
    churn_rate: float = 0.0
    payback_period_months: float = 0.0
    runway_months: float = 0.0
    total_assets: float = 0.0
    total_liabilities: float = 0.0
    equity: float = 0.0
    fixed_costs_monthly: float = 0.0
    variable_costs_percent: float = 0.0
    cash_in_bank: float = 0.0
    monthly_burn_rate: float = 0.0

    def calculate_equity(self) -> float:
        """Calculate equity (assets - liabilities)."""
        return self.total_assets - self.total_liabilities


@dataclass
class BusinessProfile:
    """Complete business profile for strategy selection."""
    business_name: str
    industry: str  # real_estate, commerce, services, finance, etc.
    business_model: BusinessModel
    stage: BusinessStage
    description: str
    team_size: int

    # Goals
    revenue_goal_annual: float = 0.0
    growth_target_percent: float = 0.0
    market_share_target: float = 0.0
    profit_margin_target: float = 0.0
    retention_goal_percent: float = 0.0

    # Market Position
    market_position: str = "unknown"  # niche, competitive, market_leader
    competitive_advantages: List[str] = field(default_factory=list)
    competitive_disadvantages: List[str] = field(default_factory=list)
    differentiation_strategy: Optional[str] = None
    target_customer_segment: Optional[str] = None
    customer_pain_points: List[str] = field(default_factory=list)

    # Financial Info
    financials: FinancialProfile = field(default_factory=FinancialProfile)

    # Inventory/Assets
    assets: List[str] = field(default_factory=list)  # What they own
    liabilities: List[str] = field(default_factory=list)  # What they owe

    # Constraints
    budget_available: float = 0.0
    talent_availability: str = "limited"  # limited, moderate, strong
    technology_maturity: str = "low"  # low, medium, high
    regulatory_constraints: List[str] = field(default_factory=list)

    # Historical Performance
    success_factors: List[str] = field(default_factory=list)
    failure_factors: List[str] = field(default_factory=list)
    recent_wins: List[str] = field(default_factory=list)
    challenges: List[str] = field(default_factory=list)


class BusinessAnalyzer:
    """Parse business profile → structured data for strategy selection."""

    def __init__(self):
        """Initialize business analyzer."""
        pass

    def analyze_business(self, company_data: Dict[str, Any]) -> BusinessProfile:
        """
        Extract and structure business profile data.

        Args:
            company_data: Raw company data (from user input, database, etc)

        Returns:
            Structured BusinessProfile for strategy selection
        """
        logger.info(f"Analyzing business: {company_data.get('business_name', 'Unknown')}")

        profile = BusinessProfile(
            business_name=company_data.get("business_name", "Unknown"),
            industry=company_data.get("industry", "other"),
            business_model=self._identify_business_model(company_data),
            stage=self._classify_stage(company_data),
            description=company_data.get("description", ""),
            team_size=company_data.get("team_size", 1),
            revenue_goal_annual=company_data.get("revenue_goal_annual", 0.0),
            growth_target_percent=company_data.get("growth_target_percent", 0.0),
            market_share_target=company_data.get("market_share_target", 0.0),
            profit_margin_target=company_data.get("profit_margin_target", 0.0),
            retention_goal_percent=company_data.get("retention_goal_percent", 0.0),
            market_position=company_data.get("market_position", "unknown"),
            competitive_advantages=company_data.get("competitive_advantages", []),
            competitive_disadvantages=company_data.get("competitive_disadvantages", []),
            differentiation_strategy=company_data.get("differentiation_strategy"),
            target_customer_segment=company_data.get("target_customer_segment"),
            customer_pain_points=company_data.get("customer_pain_points", []),
            financials=self._analyze_financials(company_data.get("financials", {})),
            assets=company_data.get("assets", []),
            liabilities=company_data.get("liabilities", []),
            budget_available=company_data.get("budget_available", 0.0),
            talent_availability=company_data.get("talent_availability", "limited"),
            technology_maturity=company_data.get("technology_maturity", "low"),
            regulatory_constraints=company_data.get("regulatory_constraints", []),
            success_factors=company_data.get("success_factors", []),
            failure_factors=company_data.get("failure_factors", []),
            recent_wins=company_data.get("recent_wins", []),
            challenges=company_data.get("challenges", []),
        )

        logger.info(f"Analyzed business: stage={profile.stage}, model={profile.business_model}")
        return profile

    def identify_business_model(self, company_data: Dict[str, Any]) -> BusinessModel:
        """Identify business model type (B2B, SaaS, etc.)."""
        return self._identify_business_model(company_data)

    def calculate_unit_economics(self, business_profile: BusinessProfile) -> Dict[str, float]:
        """
        Calculate key unit economics:
        - CAC (Customer Acquisition Cost)
        - LTV (Lifetime Value)
        - Payback period
        - Margin
        """
        financials = business_profile.financials

        # CAC: Total sales & marketing spend / Customers acquired
        cac = financials.customer_acquisition_cost or 0.0

        # LTV: ARPU * Gross Margin * (1 / Monthly Churn Rate)
        # Or: Average revenue per customer * customer lifespan
        arpu = financials.annual_revenue / max(financials.customer_count, 1)
        customer_lifespan_months = 12 / max(financials.churn_rate, 0.01) if financials.churn_rate > 0 else 60
        ltv = arpu * (financials.gross_margin_percent / 100) * customer_lifespan_months

        # Payback period: CAC / (ARPU * Gross Margin %)
        arpu_gross = arpu * (financials.gross_margin_percent / 100)
        payback_months = cac / arpu_gross if arpu_gross > 0 else 0

        # LTV:CAC ratio (healthy = 3:1+)
        ltv_cac_ratio = ltv / cac if cac > 0 else 0

        return {
            "cac": cac,
            "ltv": ltv,
            "ltv_cac_ratio": ltv_cac_ratio,
            "payback_months": payback_months,
            "arpu": arpu,
            "customer_lifespan_months": customer_lifespan_months,
            "annual_revenue": financials.annual_revenue,
            "gross_margin_percent": financials.gross_margin_percent,
            "net_margin_percent": financials.net_margin_percent,
            "churn_rate": financials.churn_rate,
        }

    def assess_competitive_advantage(self, business_profile: BusinessProfile) -> Dict[str, Any]:
        """
        Assess competitive advantages:
        - Unique vs commodity
        - Defensible vs easily copied
        - Growing vs declining
        """
        return {
            "strengths": business_profile.competitive_advantages or [],
            "weaknesses": business_profile.competitive_disadvantages or [],
            "differentiation": business_profile.differentiation_strategy,
            "position": business_profile.market_position,
            "defensibility": self._assess_defensibility(business_profile),
        }

    def evaluate_market_size(self, company_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Estimate market size:
        - TAM (Total Addressable Market)
        - SAM (Serviceable Available Market)
        - SOM (Serviceable Obtainable Market)
        """
        # These are typically provided or need estimation from market research
        return {
            "tam": company_data.get("market_size_tam", 0.0),
            "sam": company_data.get("market_size_sam", 0.0),
            "som": company_data.get("market_size_som", 0.0),
            "market_growth_percent": company_data.get("market_growth_percent", 0.0),
            "tam_reachable": company_data.get("tam_reachable", False),
        }

    def identify_constraints(self, business_profile: BusinessProfile) -> Dict[str, List[str]]:
        """Identify constraints on growth."""
        constraints = {
            "capital": [],
            "talent": [],
            "technology": [],
            "regulatory": [],
            "market": [],
        }

        # Capital constraints
        if business_profile.budget_available < 5000:
            constraints["capital"].append("Limited budget (<$5k)")
        if business_profile.financials.runway_months < 6:
            constraints["capital"].append("Low runway (<6 months)")

        # Talent constraints
        if business_profile.talent_availability == "limited":
            constraints["talent"].append("Limited team")
        if business_profile.team_size < 3:
            constraints["talent"].append("Very small team")

        # Technology constraints
        if business_profile.technology_maturity == "low":
            constraints["technology"].append("Immature technology stack")

        # Regulatory constraints
        constraints["regulatory"] = business_profile.regulatory_constraints

        # Market constraints
        if business_profile.market_position == "niche":
            constraints["market"].append("Niche market")

        return constraints

    # Private helper methods

    def _identify_business_model(self, company_data: Dict[str, Any]) -> BusinessModel:
        """Identify business model from company data."""
        description = (company_data.get("description", "") + " " + company_data.get("business_name", "")).lower()

        # Simple keyword matching
        if any(word in description for word in ["b2b", "business", "enterprise", "corporate", "b2c"]):
            if "b2b" in description or "enterprise" in description:
                return BusinessModel.B2B
            elif "b2c" in description:
                return BusinessModel.B2C
        elif any(word in description for word in ["direct", "consumer", "retail"]):
            return BusinessModel.D2C
        elif any(word in description for word in ["saas", "software", "subscription", "app"]):
            return BusinessModel.SAAS
        elif any(word in description for word in ["marketplace", "platform", "network"]):
            return BusinessModel.MARKETPLACE
        elif any(word in description for word in ["service", "consulting", "agency"]):
            return BusinessModel.SERVICES
        elif any(word in description for word in ["subscription", "membership"]):
            return BusinessModel.SUBSCRIPTION

        return BusinessModel.HYBRID

    def _classify_stage(self, company_data: Dict[str, Any]) -> BusinessStage:
        """Classify business stage based on revenue and growth."""
        financials = company_data.get("financials", {})
        annual_revenue = financials.get("annual_revenue", 0.0)
        monthly_growth = financials.get("monthly_growth_percent", 0.0)

        if annual_revenue == 0:
            return BusinessStage.STARTUP

        if annual_revenue < 100_000:
            return BusinessStage.STARTUP

        if annual_revenue < 1_000_000 and monthly_growth > 0.30:
            return BusinessStage.GROWTH

        if annual_revenue < 10_000_000 and monthly_growth > 0.15:
            return BusinessStage.SCALE

        return BusinessStage.MATURE

    def _analyze_financials(self, financials_data: Dict[str, Any]) -> FinancialProfile:
        """Parse financial data."""
        return FinancialProfile(
            annual_revenue=financials_data.get("annual_revenue", 0.0),
            monthly_recurring_revenue=financials_data.get("monthly_recurring_revenue", 0.0),
            customer_count=financials_data.get("customer_count", 0),
            customer_acquisition_cost=financials_data.get("customer_acquisition_cost", 0.0),
            customer_lifetime_value=financials_data.get("customer_lifetime_value", 0.0),
            gross_margin_percent=financials_data.get("gross_margin_percent", 50.0),
            net_margin_percent=financials_data.get("net_margin_percent", 10.0),
            churn_rate=financials_data.get("churn_rate", 0.05),
            payback_period_months=financials_data.get("payback_period_months", 12.0),
            runway_months=financials_data.get("runway_months", 12.0),
            total_assets=financials_data.get("total_assets", 0.0),
            total_liabilities=financials_data.get("total_liabilities", 0.0),
            equity=financials_data.get("equity", 0.0),
            fixed_costs_monthly=financials_data.get("fixed_costs_monthly", 0.0),
            variable_costs_percent=financials_data.get("variable_costs_percent", 50.0),
            cash_in_bank=financials_data.get("cash_in_bank", 0.0),
            monthly_burn_rate=financials_data.get("monthly_burn_rate", 0.0),
        )

    def _assess_defensibility(self, business_profile: BusinessProfile) -> str:
        """Assess how defensible competitive advantages are."""
        defensibility_factors = 0

        # Defensibility signals
        if "technology" in str(business_profile.competitive_advantages).lower():
            defensibility_factors += 1
        if "patent" in str(business_profile.competitive_advantages).lower():
            defensibility_factors += 2
        if "brand" in str(business_profile.competitive_advantages).lower():
            defensibility_factors += 1
        if "network_effects" in str(business_profile.competitive_advantages).lower():
            defensibility_factors += 2
        if "data" in str(business_profile.competitive_advantages).lower():
            defensibility_factors += 1

        if defensibility_factors >= 2:
            return "high"
        elif defensibility_factors >= 1:
            return "medium"
        else:
            return "low"
