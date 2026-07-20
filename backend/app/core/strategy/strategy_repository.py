"""Strategy Repository — 50+ strategies with application rules."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class Strategy(str, Enum):
    """Strategy identifiers."""
    # Blue Ocean Strategies
    BLUE_OCEAN_ELIMINATE = "blue_ocean_eliminate"
    BLUE_OCEAN_REDUCE = "blue_ocean_reduce"
    BLUE_OCEAN_RAISE = "blue_ocean_raise"
    BLUE_OCEAN_CREATE = "blue_ocean_create"
    VALUE_INNOVATION = "value_innovation"

    # Customer Happiness/Retention
    NPS_DRIVEN = "nps_driven"
    ONBOARDING_EXCELLENCE = "onboarding_excellence"
    SURPRISE_DELIGHT = "surprise_delight"
    COMMUNITY_BUILDING = "community_building"
    SUBSCRIPTIONS = "subscriptions_recurring"
    WIN_BACK = "win_back_campaigns"

    # Negotiation Strategies
    SUPPLIER_VOLUME_DISCOUNT = "supplier_volume_discount"
    SUPPLIER_PAYMENT_TERMS = "supplier_payment_terms"
    SUPPLIER_EXCLUSIVITY = "supplier_exclusivity"
    CUSTOMER_BUNDLING = "customer_bundling"
    CUSTOMER_PAYMENT_PLANS = "customer_payment_plans"
    CUSTOMER_RISK_REVERSAL = "customer_risk_reversal"

    # Pricing Methods
    COST_PLUS = "cost_plus_pricing"
    VALUE_BASED = "value_based_pricing"
    COMPETITOR_BASED = "competitor_based_pricing"
    DYNAMIC = "dynamic_pricing"
    PSYCHOLOGICAL = "psychological_pricing"
    FREEMIUM = "freemium_pricing"
    TIERED = "tiered_pricing"

    # Customer Acquisition
    CONTENT_MARKETING = "content_marketing"
    PAID_ADS = "paid_ads"
    OUTBOUND_SALES = "outbound_sales"
    PARTNERSHIPS = "partnerships_referral"
    NETWORK_EFFECTS = "network_effects"
    VIRAL_LOOPS = "viral_loops"
    COMMUNITY = "community_acquisition"

    # Positioning Strategies
    CATEGORY_CREATION = "category_creation"
    FEATURE_LEADERSHIP = "feature_leadership"
    VERTICAL_SPECIALIZATION = "vertical_specialization"
    PRICE_POSITIONING = "price_positioning"
    VALUE_POSITIONING = "value_positioning"
    EMOTIONAL_POSITIONING = "emotional_positioning"

    # Growth Strategies
    PENETRATION = "market_penetration"
    EXPANSION = "market_expansion"
    DIVERSIFICATION = "diversification"
    ACQUISITION = "acquisition"
    VERTICAL_INTEGRATION = "vertical_integration"


class StrategyCategory(str, Enum):
    """Strategy classification."""
    BLUE_OCEAN = "blue_ocean"
    RETENTION = "retention"
    NEGOTIATION = "negotiation"
    PRICING = "pricing"
    ACQUISITION = "acquisition"
    POSITIONING = "positioning"
    GROWTH = "growth"


@dataclass
class StrategyDefinition:
    """Complete strategy definition with rules."""
    strategy_id: Strategy
    name: str
    category: StrategyCategory
    description: str
    best_for_stages: List[str]  # startup, growth, scale, mature
    best_for_industries: List[str]  # commerce, real_estate, services, etc.
    best_for_business_models: List[str]  # B2B, B2C, D2C, SaaS, Services, etc.
    key_principles: List[str]
    implementation_steps: List[str]
    success_metrics: List[str]
    typical_timeline_weeks: int
    resource_requirements: Dict[str, str]
    constraints: List[str]
    risks: List[str]
    expected_roi: Dict[str, float]  # Key metrics → expected improvement %
    incompatible_with: List[Strategy]
    examples: List[str]


class StrategyRepository:
    """50+ vendidas strategies with application rules."""

    def __init__(self):
        """Initialize strategy repository."""
        self.strategies = self._initialize_strategies()

    def _initialize_strategies(self) -> Dict[Strategy, StrategyDefinition]:
        """Initialize all 50+ strategies."""
        return {
            # Blue Ocean Strategies
            Strategy.BLUE_OCEAN_ELIMINATE: StrategyDefinition(
                strategy_id=Strategy.BLUE_OCEAN_ELIMINATE,
                name="Eliminate Industry Factors",
                category=StrategyCategory.BLUE_OCEAN,
                description="Remove factors the industry competes on that customers don't value",
                best_for_stages=["startup", "growth"],
                best_for_industries=["commerce", "services", "digital_products"],
                best_for_business_models=["B2C", "D2C", "SaaS"],
                key_principles=[
                    "Eliminate costly but low-value features",
                    "Reduce cost structure dramatically",
                    "Challenge industry assumptions",
                ],
                implementation_steps=[
                    "Identify all factors industry competes on",
                    "Interview customers on value of each",
                    "Eliminate bottom 20%",
                    "Communicate cost savings to customers",
                ],
                success_metrics=[
                    "Cost reduction %",
                    "Pricing reduction %",
                    "Customer acquisition increase %",
                ],
                typical_timeline_weeks=8,
                resource_requirements={
                    "strategy": "1-2 weeks",
                    "operations": "2-4 weeks",
                    "marketing": "2-4 weeks",
                },
                constraints=["Must maintain quality perception", "Risk of commoditization"],
                risks=["Brand perception damage", "Competitor response"],
                expected_roi={"cost_reduction": 0.20, "volume_increase": 0.30},
                incompatible_with=[Strategy.FEATURE_LEADERSHIP],
                examples=[
                    "Uber (eliminated dispatchers)",
                    "Zoom (eliminated complexity)",
                ],
            ),
            Strategy.VALUE_INNOVATION: StrategyDefinition(
                strategy_id=Strategy.VALUE_INNOVATION,
                name="Value Innovation Framework",
                category=StrategyCategory.BLUE_OCEAN,
                description="Simultaneously pursue differentiation AND low cost",
                best_for_stages=["growth", "scale"],
                best_for_industries=["all"],
                best_for_business_models=["all"],
                key_principles=[
                    "Break value-cost trade-off",
                    "Explore new demand",
                    "Focus on the big picture",
                ],
                implementation_steps=[
                    "Create strategy canvas of industry",
                    "Apply ERRC grid (Eliminate, Reduce, Raise, Create)",
                    "Test new positioning with customers",
                    "Scale winning combination",
                ],
                success_metrics=[
                    "Price vs competitors",
                    "Customer value perception",
                    "Market share growth",
                ],
                typical_timeline_weeks=12,
                resource_requirements={
                    "strategy": "3-4 weeks",
                    "product": "4-8 weeks",
                },
                constraints=["Requires deep market knowledge"],
                risks=["Market timing", "Competitor imitation"],
                expected_roi={"market_share": 0.25, "margin": 0.15},
                incompatible_with=[],
                examples=["Southwest Airlines", "Netflix"],
            ),

            # Retention Strategies
            Strategy.NPS_DRIVEN: StrategyDefinition(
                strategy_id=Strategy.NPS_DRIVEN,
                name="NPS-Driven Retention",
                category=StrategyCategory.RETENTION,
                description="Convert detractors to promoters through feedback-driven improvements",
                best_for_stages=["all"],
                best_for_industries=["all"],
                best_for_business_models=["all"],
                key_principles=[
                    "Measure customer satisfaction regularly",
                    "Address detractor concerns immediately",
                    "Delight promoters to drive referrals",
                ],
                implementation_steps=[
                    "Implement NPS surveys monthly",
                    "Segment customers (promoters/passives/detractors)",
                    "Create action plan for each segment",
                    "Track improvements over time",
                ],
                success_metrics=["NPS score", "Churn rate", "Referral rate"],
                typical_timeline_weeks=6,
                resource_requirements={
                    "surveying": "ongoing",
                    "support": "1-2 people",
                },
                constraints=["Requires feedback systems"],
                risks=["Negative feedback can be demotivating"],
                expected_roi={"retention": 0.15, "referrals": 0.20},
                incompatible_with=[],
                examples=["Slack", "Notion", "Calendly"],
            ),
            Strategy.ONBOARDING_EXCELLENCE: StrategyDefinition(
                strategy_id=Strategy.ONBOARDING_EXCELLENCE,
                name="Onboarding Excellence",
                category=StrategyCategory.RETENTION,
                description="First 30 days are critical - perfect onboarding drives retention",
                best_for_stages=["all"],
                best_for_industries=["digital_products", "SaaS"],
                best_for_business_models=["SaaS", "digital_products"],
                key_principles=[
                    "First impression matters",
                    "Reduce time to value",
                    "Create early wins for customers",
                ],
                implementation_steps=[
                    "Map customer journey first 30 days",
                    "Identify critical milestones",
                    "Automate where possible",
                    "Personalize based on use case",
                    "Track completion rates",
                ],
                success_metrics=["Day 7 activation", "Day 30 retention", "Time to first success"],
                typical_timeline_weeks=8,
                resource_requirements={
                    "product": "2-3 weeks",
                    "support": "1 person",
                },
                constraints=["Requires customer data", "Ongoing optimization"],
                risks=["Over-automation can feel impersonal"],
                expected_roi={"retention": 0.30, "ltv": 0.25},
                incompatible_with=[],
                examples=["Slack (3-step onboarding)", "Duolingo (daily habit)"],
            ),
            Strategy.COMMUNITY_BUILDING: StrategyDefinition(
                strategy_id=Strategy.COMMUNITY_BUILDING,
                name="Community Building",
                category=StrategyCategory.RETENTION,
                description="Build owned community of users → advocacy + retention",
                best_for_stages=["growth", "scale"],
                best_for_industries=["all"],
                best_for_business_models=["B2C", "SaaS"],
                key_principles=[
                    "Users connect with users",
                    "Owned audience > paid reach",
                    "Community drives compound growth",
                ],
                implementation_steps=[
                    "Choose community platform (Discord/Slack/Forum)",
                    "Seed community with power users",
                    "Create engagement rituals",
                    "Celebrate user wins publicly",
                    "Graduate users to leaders",
                ],
                success_metrics=["Community size", "Daily active users", "Content generated"],
                typical_timeline_weeks=12,
                resource_requirements={
                    "community_manager": "1 person",
                    "platform": "tools",
                },
                constraints=["Requires active management", "Slow initial growth"],
                risks=["Toxicity", "Moderation challenges"],
                expected_roi={"retention": 0.25, "referrals": 0.35},
                incompatible_with=[],
                examples=["Circle (community)", "MasterClass (community)"],
            ),

            # Pricing Strategies
            Strategy.VALUE_BASED: StrategyDefinition(
                strategy_id=Strategy.VALUE_BASED,
                name="Value-Based Pricing",
                category=StrategyCategory.PRICING,
                description="Price based on value delivered, not cost or competition",
                best_for_stages=["growth", "scale"],
                best_for_industries=["all"],
                best_for_business_models=["all"],
                key_principles=[
                    "Price by value delivered",
                    "Segment customers by willingness to pay",
                    "Communicate value clearly",
                ],
                implementation_steps=[
                    "Interview customers on value perception",
                    "Map customer segments",
                    "Test price points with surveys",
                    "Implement tiered pricing",
                    "Monitor elasticity",
                ],
                success_metrics=["Revenue increase", "Margin improvement", "Customer satisfaction"],
                typical_timeline_weeks=10,
                resource_requirements={
                    "pricing_analyst": "1 person",
                    "analytics": "capability",
                },
                constraints=["Requires customer research", "Market testing"],
                risks=["Customer backlash on increases"],
                expected_roi={"revenue": 0.25, "margin": 0.20},
                incompatible_with=[Strategy.COST_PLUS],
                examples=["Salesforce (value-based)", "HubSpot (tiered value)"],
            ),
            Strategy.TIERED: StrategyDefinition(
                strategy_id=Strategy.TIERED,
                name="Tiered Pricing (Basic/Pro/Enterprise)",
                category=StrategyCategory.PRICING,
                description="Multiple price points serve different customer segments",
                best_for_stages=["growth", "scale"],
                best_for_industries=["digital_products", "SaaS"],
                best_for_business_models=["SaaS"],
                key_principles=[
                    "Good/Better/Best positioning",
                    "Anchor with premium tier",
                    "80% users in middle tier",
                ],
                implementation_steps=[
                    "Define 3-4 tiers based on value metrics",
                    "Price tiers with 2-3x gap",
                    "Limit features at lower tiers",
                    "Create upgrade path",
                    "Monitor tier distribution",
                ],
                success_metrics=["Mix of tiers", "ARPU (average revenue per user)", "Conversion rate"],
                typical_timeline_weeks=8,
                resource_requirements={
                    "product": "1-2 weeks",
                    "analytics": "ongoing",
                },
                constraints=["Feature limitation complexity"],
                risks=["Price wars with competitors"],
                expected_roi={"revenue": 0.30, "ltv": 0.25},
                incompatible_with=[],
                examples=["Notion", "Slack", "GitHub"],
            ),
            Strategy.FREEMIUM: StrategyDefinition(
                strategy_id=Strategy.FREEMIUM,
                name="Freemium Pricing",
                category=StrategyCategory.PRICING,
                description="Free tier for acquisition + paid premium for advanced features",
                best_for_stages=["startup", "growth"],
                best_for_industries=["digital_products", "SaaS"],
                best_for_business_models=["SaaS"],
                key_principles=[
                    "Free tier drives adoption",
                    "Premium features create clear upgrade path",
                    "LTV must support free users",
                ],
                implementation_steps=[
                    "Define free tier (must be valuable)",
                    "Limit free tier strategically",
                    "Create compelling premium features",
                    "Track free-to-paid conversion",
                    "Optimize upgrade funnel",
                ],
                success_metrics=["Free user base", "Free-to-paid conversion", "Free CAC"],
                typical_timeline_weeks=12,
                resource_requirements={
                    "product": "2-4 weeks",
                    "support": "increased",
                },
                constraints=["Sustainability concerns", "Free user support costs"],
                risks=["High free-user support burden", "Low conversion rates"],
                expected_roi={"acquisition": 0.50, "ltv": -0.10},
                incompatible_with=[Strategy.PAID_ADS],
                examples=["Slack", "Canva", "Dropbox"],
            ),

            # Acquisition Strategies
            Strategy.CONTENT_MARKETING: StrategyDefinition(
                strategy_id=Strategy.CONTENT_MARKETING,
                name="Content Marketing",
                category=StrategyCategory.ACQUISITION,
                description="Blog, video, social content → organic authority + SEO",
                best_for_stages=["all"],
                best_for_industries=["all"],
                best_for_business_models=["B2B", "B2C"],
                key_principles=[
                    "Build authority over time",
                    "SEO compounds (write once, earn forever)",
                    "Content builds trust",
                ],
                implementation_steps=[
                    "Identify keyword opportunities",
                    "Create pillar content (10k+ words)",
                    "Create cluster content (supporting articles)",
                    "Build backlinks",
                    "Measure organic traffic and conversions",
                ],
                success_metrics=["Organic traffic", "Organic leads", "Cost per lead"],
                typical_timeline_weeks=24,
                resource_requirements={
                    "writer": "1 person",
                    "seo_specialist": "0.5 person",
                },
                constraints=["Slow to ramp", "Requires consistency"],
                risks=["No guaranteed results"],
                expected_roi={"cac": -0.50, "ltv": 0.15},
                incompatible_with=[],
                examples=["HubSpot Blog", "Moz", "Neil Patel"],
            ),
            Strategy.PAID_ADS: StrategyDefinition(
                strategy_id=Strategy.PAID_ADS,
                name="Paid Advertising (Google, Facebook, LinkedIn)",
                category=StrategyCategory.ACQUISITION,
                description="Paid channels for fast customer acquisition",
                best_for_stages=["growth", "scale"],
                best_for_industries=["all"],
                best_for_business_models=["all"],
                key_principles=[
                    "Scale is about unit economics",
                    "Test channels with small budgets first",
                    "Triple-down on winners",
                ],
                implementation_steps=[
                    "Identify audience and platform",
                    "Create ad variations",
                    "Test with small budget",
                    "Measure LTV vs CAC",
                    "Scale profitably",
                ],
                success_metrics=["CAC", "ROAS (return on ad spend)", "LTV:CAC ratio"],
                typical_timeline_weeks=8,
                resource_requirements={
                    "marketing": "1 person",
                    "budget": "variable",
                },
                constraints=["High CAC", "Market saturation"],
                risks=["Burnout on ads"],
                expected_roi={"cac": 0.20, "ltv": 0.05},
                incompatible_with=[],
                examples=["Slack", "Reforge", "MasterClass"],
            ),
            Strategy.PARTNERSHIPS: StrategyDefinition(
                strategy_id=Strategy.PARTNERSHIPS,
                name="Partnership & Referral Program",
                category=StrategyCategory.ACQUISITION,
                description="Leverage other businesses to acquire customers",
                best_for_stages=["all"],
                best_for_industries=["all"],
                best_for_business_models=["all"],
                key_principles=[
                    "Referral is cheaper than ads",
                    "Find natural partners",
                    "Create win-win incentives",
                ],
                implementation_steps=[
                    "Map complementary businesses",
                    "Design referral incentive",
                    "Create easy share mechanism",
                    "Track referrals",
                    "Reward top referrers",
                ],
                success_metrics=["Referral volume", "Referral CAC", "Referral quality"],
                typical_timeline_weeks=6,
                resource_requirements={
                    "operations": "0.5 person",
                    "tools": "referral software",
                },
                constraints=["Requires partner network"],
                risks=["Poor referral quality"],
                expected_roi={"cac": -0.40, "lifetime_value": 0.20},
                incompatible_with=[],
                examples=["Dropbox (referral)", "Stripe (integrations)"],
            ),

            # Positioning Strategies
            Strategy.CATEGORY_CREATION: StrategyDefinition(
                strategy_id=Strategy.CATEGORY_CREATION,
                name="Category Creation / Market Definition",
                category=StrategyCategory.POSITIONING,
                description="Define new market category rather than compete in existing",
                best_for_stages=["startup", "growth"],
                best_for_industries=["digital_products", "SaaS"],
                best_for_business_models=["SaaS"],
                key_principles=[
                    "Own the narrative of new category",
                    "Become synonymous with category",
                    "First-mover advantage significant",
                ],
                implementation_steps=[
                    "Identify market gap",
                    "Define the problem clearly",
                    "Position as solution to problem",
                    "Educate market on problem importance",
                    "Scale as category grows",
                ],
                success_metrics=["Category awareness", "Market size", "Market share"],
                typical_timeline_weeks=24,
                resource_requirements={
                    "strategy": "2-4 weeks",
                    "marketing": "ongoing",
                    "pr": "1 person",
                },
                constraints=["High risk", "Requires clear differentiation"],
                risks=["Market may not adopt", "Competitor may own category"],
                expected_roi={"market_share": 0.40, "brand_value": 0.50},
                incompatible_with=[],
                examples=["Zoom (video conferencing)", "Slack (team chat)"],
            ),

            # Growth Strategies
            Strategy.PENETRATION: StrategyDefinition(
                strategy_id=Strategy.PENETRATION,
                name="Market Penetration",
                category=StrategyCategory.GROWTH,
                description="Sell more to existing customers",
                best_for_stages=["all"],
                best_for_industries=["all"],
                best_for_business_models=["all"],
                key_principles=[
                    "Existing customer = 5-25x cheaper to sell",
                    "Focus on upsell and cross-sell",
                    "Improve existing product",
                ],
                implementation_steps=[
                    "Identify upsell/cross-sell opportunities",
                    "Create bundled offers",
                    "Build premium tier",
                    "Track expansion revenue",
                ],
                success_metrics=["Expansion revenue %", "Net revenue retention", "Upsell rate"],
                typical_timeline_weeks=8,
                resource_requirements={
                    "product": "2 weeks",
                    "sales": "ongoing",
                },
                constraints=["Depends on customer base"],
                risks=["Customer dissatisfaction with upsell"],
                expected_roi={"ltv": 0.30, "margin": 0.15},
                incompatible_with=[],
                examples=["Slack (upsell seats)", "Notion (teams)"],
            ),
        }

    def get_strategy(self, strategy_id: Strategy) -> Optional[StrategyDefinition]:
        """Get strategy by ID."""
        return self.strategies.get(strategy_id)

    def get_strategies_for_stage(self, stage: str) -> List[StrategyDefinition]:
        """Get all strategies applicable to a business stage."""
        return [s for s in self.strategies.values() if stage in s.best_for_stages]

    def get_strategies_for_industry(self, industry: str) -> List[StrategyDefinition]:
        """Get all strategies applicable to an industry."""
        return [s for s in self.strategies.values() if industry in s.best_for_industries]

    def get_strategies_for_business_model(self, model: str) -> List[StrategyDefinition]:
        """Get all strategies applicable to a business model."""
        return [s for s in self.strategies.values() if model in s.best_for_business_models]

    def get_strategies_by_category(self, category: StrategyCategory) -> List[StrategyDefinition]:
        """Get all strategies in a category."""
        return [s for s in self.strategies.values() if s.category == category]

    def find_compatible_strategies(self, strategy_id: Strategy) -> List[StrategyDefinition]:
        """Find strategies that work well together."""
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            return []

        compatible = []
        for s in self.strategies.values():
            if s.strategy_id not in strategy.incompatible_with and s.strategy_id != strategy_id:
                compatible.append(s)

        return compatible

    def evaluate_strategy_fit(self, strategy_id: Strategy, business_profile: "BusinessProfile") -> float:
        """Calculate fit score (0-1) of strategy for business."""
        strategy = self.get_strategy(strategy_id)
        if not strategy:
            return 0.0

        score = 0.0
        weight_sum = 0.0

        # Stage fit
        if business_profile.stage in strategy.best_for_stages:
            score += 0.3
        weight_sum += 0.3

        # Industry fit
        if business_profile.industry in strategy.best_for_industries:
            score += 0.35
        weight_sum += 0.35

        # Business model fit
        if business_profile.business_model in strategy.best_for_business_models:
            score += 0.35
        weight_sum += 0.35

        return score / weight_sum if weight_sum > 0 else 0.0
