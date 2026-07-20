# Specialist Agents - Quick Start Guide

## Import All Agents

```python
from backend.app.core.agents.specialists import (
    MethodologyAgent,
    SalesAgent,
    MarketingAgent,
    AdvertisingAgent,
    BusinessAgent,
    InnovationAgent,
    DevelopmentAgent,
    FinancialAgent,
    NegotiationAgent,
    StorytellingAgent,
    SPECIALIST_AGENTS,
    list_specialists,
)
```

## Get Agent by Name (Dynamic)

```python
# Get any agent dynamically
agent = SPECIALIST_AGENTS.get("sales")  # SalesAgent class
agent_method = agent.recommend_methodology()

# List all available agents
specialists = list_specialists()
# Returns: ['methodology', 'sales', 'marketing', 'advertising', 'business', 
#           'innovation', 'development', 'financial', 'negotiation', 'storytelling']
```

---

## Common Use Cases by Agent

### 1. Methodology Agent
```python
# What framework should we use?
recommendation = MethodologyAgent.recommend_framework(
    business_type="b2b_saas",
    business_stage="early_traction"
)
# Returns: Primary framework + alternatives

# How do we implement MEDDIC?
meddic_details = MethodologyAgent.get_framework_details("meddic")

# Create implementation plan
plan = MethodologyAgent.create_implementation_plan(
    framework_key="okrs",
    business_context={"owner": "Product team", "team_size": 5}
)
```

### 2. Sales Agent
```python
# Which sales methodology for this deal?
approach = SalesAgent.recommend_methodology(
    deal_size=100000,
    cycle_length_months=9,
    complexity="complex"
)
# Returns: MEDDIC or Challenger Sale

# How do we handle this objection?
response = SalesAgent.handle_objection(
    objection_type=ObjectionType.PRICE,
    specific_context="Client says we're 2x more expensive"
)

# Get discovery call template
playbook = SalesAgent.get_playbook("discovery_call")
```

### 3. Marketing Agent
```python
# Create marketing strategy
strategy = MarketingAgent.create_marketing_strategy(
    business_context={"stage": "growth", "arpu": 5000},
    target_segments=["Enterprise", "Mid-market"]
)

# Get channel strategy
channel = MarketingAgent.get_channel_strategy(
    channel=MarketingChannel.CONTENT,
    target_segment="Enterprise"
)

# Design growth loop
loop = MarketingAgent.design_growth_loop(
    loop_type="viral",
    product_features=["Referral invite", "Reward system"],
    target_metrics=["Viral coefficient > 1.5"]
)
```

### 4. Advertising Agent
```python
# Which platforms for this campaign?
platforms = AdvertisingAgent.recommend_platform(
    target_audience="B2B buyers",
    campaign_goal="lead_generation",
    budget=50000,
    timeline_days=90
)

# Design A/B test
test = AdvertisingAgent.design_creative_test(
    test_type="headlines",
    variations_count=5
)

# Get bid strategy recommendation
bid_strategy = AdvertisingAgent.get_bid_strategy_recommendation(
    monthly_budget=10000,
    conversion_volume=150,
    revenue_tracking=True
)
```

### 5. Business Agent
```python
# Calculate unit economics
unit_econ = BusinessAgent.calculate_unit_economics(
    arpu=5000,
    cac=1500,
    gross_margin=0.75,
    avg_customer_lifetime_months=36,
    retention_rate=0.95
)
# Returns: LTV, payback period, LTV:CAC ratio, assessment

# Are we ready to scale?
readiness = BusinessAgent.assess_scaling_readiness(
    unit_economics=unit_econ,
    runway_months=18,
    team_size=12
)

# Design business model
model = BusinessAgent.design_business_model(
    business_type="b2b_saas",
    target_market="Enterprise",
    competitive_positioning="Premium"
)
```

### 6. Innovation Agent
```python
# What's the customer job we're solving?
jobs_analysis = InnovationAgent.analyze_jobs_to_be_done(
    customer_segment="Sales leaders",
    situation="Selling complex B2B solutions"
)

# Design Blue Ocean strategy
blue_ocean = InnovationAgent.design_blue_ocean(
    industry="Sales enablement",
    current_competition=["Competitor A", "Competitor B"]
)

# Find market opportunities
opportunities = InnovationAgent.identify_market_opportunities(
    trends=["AI adoption", "Remote work", "Automation"],
    customer_segments=["SMB", "Enterprise"],
    technology_landscape={}
)
```

### 7. Development Agent
```python
# Which tech stack?
stack = DevelopmentAgent.recommend_tech_stack(
    company_stage="mvp",
    expected_scale="1M users",
    team_expertise=["Python", "React", "PostgreSQL"],
    budget=100000
)

# Design growth hack
growth = DevelopmentAgent.design_growth_hack(
    product="SellIA",
    target_users="Sales teams",
    budget=50000,
    timeline_months=3
)

# Create MVP roadmap
mvp = DevelopmentAgent.create_mvp_roadmap(
    product_vision="Automated sales engagement",
    target_launch_date="2026-10-01",
    team_size=5
)

# Prioritize features (RICE framework)
prioritized = DevelopmentAgent.prioritize_features(
    features=[
        {"name": "AI prospecting", "reach": 100, "impact": 3, "confidence": 0.8, "effort": 8},
        {"name": "Email integration", "reach": 80, "impact": 2, "confidence": 0.9, "effort": 3},
    ],
    framework="rice"
)
```

### 8. Financial Agent
```python
# What pricing strategy?
pricing = FinancialAgent.recommend_pricing_strategy(
    product_type="SaaS",
    target_market="Enterprise",
    competition="High",
    business_model="subscription"
)

# Create pricing model with tiers
model = FinancialAgent.create_pricing_model(
    product_name="SellIA",
    target_segments=["Startup", "Scale-up", "Enterprise"],
    value_per_segment={
        "Startup": "Basic automation",
        "Scale-up": "Advanced + integrations",
        "Enterprise": "Custom + dedicated"
    },
    strategy="value_based"
)

# Project financials (24 months)
forecast = FinancialAgent.build_financial_model(
    annual_revenue=500000,
    growth_rate_percent=10,
    gross_margin_percent=75,
    monthly_fixed_costs=50000,
    starting_cash=200000,
    timeline_months=24
)

# Calculate detailed unit economics
econ = FinancialAgent.calculate_unit_economics_detailed(
    arpu=5000,
    monthly_churn=0.05,
    annual_retention=0.94,
    cac=1500,
    cogs_percent=0.25
)
```

### 9. Negotiation Agent
```python
# Prepare for negotiation
prep = NegotiationAgent.prepare_negotiation(
    negotiation_type=NegotiationType.CUSTOMER_SALES,
    other_party="Large prospect",
    objective="Close deal at $100K annual contract value"
)

# Analyze your position
position = NegotiationAgent.analyze_negotiation_position(
    current_offer={"price": 100000, "payment_terms": "annual"},
    must_haves=["$80K minimum", "Annual commitment"],
    nice_to_haves=["Multi-year discount", "Custom features"],
    batna_value=50000  # Best alternative if deal doesn't happen
)

# Create opening offer
offer = NegotiationAgent.create_offer(
    base_value=100000,
    margin=0.15,  # 15% above target (anchor high for selling)
    anchor_strategy="high"
)

# Get closing strategies
closing = NegotiationAgent.closing_strategies()
```

### 10. Storytelling Agent
```python
# Craft brand story
story = StorytellingAgent.craft_brand_story(
    company_name="SellIA",
    founder_origin="Started after losing major deal to manual process",
    mission="Automate sales, humanize relationships",
    target_audience="Sales leaders"
)

# Create customer case study
case_study = StorytellingAgent.create_customer_case_study(
    customer_name="Acme Sales",
    customer_role="VP Sales",
    initial_challenge="Manual prospecting taking 40 hours/week",
    solution_provided="SellIA AI prospecting automation",
    results={
        "time_saved": "30 hours/week",
        "revenue_increase": "35%",
        "quota_achievement": "120%"
    }
)

# Build investor pitch narrative
pitch = StorytellingAgent.build_pitch_narrative(
    company="SellIA",
    problem="Sales teams waste 50% time on manual tasks",
    solution="AI-powered automation that increases deals by 40%",
    market_size="$50B sales enablement market",
    target_customer="Enterprise sales teams"
)

# Apply Hero's Journey
journey = StorytellingAgent.apply_heroes_journey(
    protagonist="Sales leader",
    ordinary_world="Manual, inefficient sales process",
    call_to_adventure="Discover SellIA",
    climax="First automated campaign closes deal",
    resolution="Sales team 3x more effective"
)
```

---

## Agent Interaction Pattern

Most agents follow this pattern:

1. **Analyze/Assess** - Understand current state
2. **Recommend** - Suggest best approach for your context
3. **Design/Create** - Build detailed plan or model
4. **Implement** - Provide playbooks and next steps
5. **Measure** - Suggest metrics to track success

---

## Working with Enums

All agents use enums for type safety. Examples:

```python
from backend.app.core.agents.specialists import (
    BusinessStage,      # "idea", "mvp", "early_traction", "growth", "scale", "mature"
    SalesMethodology,   # "meddic", "sandler", "consultative", etc.
    MarketingChannel,   # "email", "content", "social", "paid_ads", etc.
    AdPlatform,        # "google_search", "facebook", "linkedin", "tiktok", etc.
    RevenueModel,      # "subscription", "usage_based", "freemium", etc.
    DisruptionType,    # "performance", "convenience", "cost", "experience", "model"
    PricingStrategy,   # "cost_plus", "value_based", "competitive", "dynamic", etc.
    NegotiationType,   # "customer_sales", "supplier", "employment", etc.
    StoryType,         # "origin", "mission", "customer", "problem_solution", etc.
)

# Use them like:
recommend = SalesAgent.recommend_methodology(
    deal_size=50000,
    cycle_length_months=6,
    complexity="complex"
)
```

---

## Integration with SellIA Brain

These agents integrate with `SellIA_Brain_v3` to:

1. **Enhance intelligence** - Add specialized expertise to LLM responses
2. **Structure outputs** - Return consistent, actionable data
3. **Enable learning** - Track what works for your business
4. **Provide frameworks** - Use battle-tested methodologies
5. **Suggest metrics** - Know how to validate effectiveness

---

## Performance Benchmarks

Each agent provides industry benchmarks:
- Sales conversion rates by methodology
- Marketing CAC by channel
- Pricing elasticity by product type
- Unit economics by business model
- Negotiation outcomes by strategy
- And more...

---

## Tips

1. **Start with assessment** - Use assessment methods first to understand your context
2. **Follow recommendations** - Agents recommend specific frameworks for your situation
3. **Use playbooks** - Don't create from scratch, use pre-built playbooks
4. **Track metrics** - Each method includes suggested KPIs
5. **Iterate** - Agents suggest next steps and alternative approaches

---

For detailed documentation on each agent, see `SPECIALISTS.md`
