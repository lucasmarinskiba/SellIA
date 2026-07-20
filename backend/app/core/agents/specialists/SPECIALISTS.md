# SellIA Specialist Agents

10 production-ready specialist agents providing deep expertise across business, sales, marketing, and operations.

## Overview

Total: **~5,100 lines** of production-ready Python code across 10 specialist agents.

Each agent:
- Has deep domain expertise with frameworks, methodologies, and tactics
- Provides structured guidance and implementations
- Integrates with SellIA's LLM for real reasoning
- Suggests next steps and metrics for validation
- Learns from user context (market, business stage, goals)

---

## Agents

### 1. **Methodology Agent** (557 lines)
**Framework knowledge and business methodology expertise**

**Specialties:**
- Jobs to be Done (JTBD) framework
- Value Proposition Design
- Lean Startup methodology
- OKRs (Objectives & Key Results)
- Business Model Canvas
- Design Thinking
- North Star Metric

**Key Methods:**
```python
MethodologyAgent.recommend_framework()  # Recommend by business type/stage
MethodologyAgent.get_framework_details()  # Deep dive into specific framework
MethodologyAgent.create_implementation_plan()  # Actionable roadmap
MethodologyAgent.assess_framework_readiness()  # Can you execute this framework?
```

**Use Cases:**
- Define business strategy and methodology
- Select frameworks for business stage
- Build OKR systems
- Validate business model
- Create product strategy

---

### 2. **Sales Agent** (647 lines)
**Master of sales methodologies, tactics, and playbooks**

**Specialties:**
- Sales methodologies: MEDDIC, Sandler, Consultative, Challenger Sale, SPIN, Conceptual Selling
- Sales tactics: discovery, qualification, objection handling, closing
- Sales scripts and playbooks
- Sales training materials
- Objection handling framework

**Key Methods:**
```python
SalesAgent.get_methodology()  # Deep dive into methodology
SalesAgent.recommend_methodology()  # Which methodology for this deal?
SalesAgent.get_stage_guidance()  # Guidance for each sales stage
SalesAgent.handle_objection()  # Respond to common objections
SalesAgent.get_playbook()  # Pre-built playbooks (cold outreach, discovery, closing)
```

**Use Cases:**
- Train sales team on methodologies
- Structure sales conversations
- Handle difficult objections
- Customize sales scripts
- Build sales playbooks

---

### 3. **Marketing Agent** (648 lines)
**Strategy, positioning, messaging, and campaigns**

**Specialties:**
- Marketing strategy and STP framework (Segmentation, Targeting, Positioning)
- Marketing mix (4Ps: Product, Price, Place, Promotion)
- Content marketing and content pillars
- Growth loops (viral, content, retention, referral)
- Customer journey stages (awareness → advocacy)
- Campaign design and optimization
- Messaging and positioning

**Key Methods:**
```python
MarketingAgent.analyze_positioning()  # Analyze current positioning
MarketingAgent.create_marketing_strategy()  # Build comprehensive strategy
MarketingAgent.get_channel_strategy()  # Deep dive into specific channel
MarketingAgent.create_content_calendar()  # Plan content distribution
MarketingAgent.design_growth_loop()  # Design growth mechanisms
MarketingAgent.get_journey_guidance()  # Guidance for each journey stage
```

**Use Cases:**
- Define marketing strategy
- Optimize positioning
- Build content strategy
- Design campaigns
- Implement growth loops
- Improve customer journey

---

### 4. **Advertising Agent** (496 lines)
**Paid advertising strategy and optimization**

**Specialties:**
- Ad platform optimization (Google, Facebook, LinkedIn, TikTok, etc.)
- Audience segmentation and targeting
- Creative testing and A/B testing frameworks
- ROAS optimization and bid strategies
- Budget allocation models
- Campaign structure and organization
- Compliance guidelines

**Key Methods:**
```python
AdvertisingAgent.get_platform_strategy()  # Deep dive into platform
AdvertisingAgent.recommend_platform()  # Which platform for this campaign?
AdvertisingAgent.create_audience_segments()  # Build audience structure
AdvertisingAgent.design_creative_test()  # A/B test framework
AdvertisingAgent.optimize_budget()  # Allocate budget effectively
AdvertisingAgent.get_bid_strategy_recommendation()  # Which bidding approach?
```

**Use Cases:**
- Plan advertising strategy
- Select optimal platforms
- Design A/B tests
- Optimize ROAS
- Allocate budget
- Manage campaigns

---

### 5. **Business Agent** (472 lines)
**Business model design, scaling strategy, and unit economics**

**Specialties:**
- Business model design and optimization
- Revenue model analysis (subscription, usage-based, freemium, marketplace, etc.)
- Unit economics and CAC/LTV analysis
- Scaling principles and readiness assessment
- Financial metrics (MRR, ARR, magic number, burn rate)
- Competitive positioning
- Growth forecasting

**Key Methods:**
```python
BusinessAgent.calculate_unit_economics()  # Calculate LTV, CAC, payback
BusinessAgent.assess_scaling_readiness()  # Ready to scale?
BusinessAgent.design_business_model()  # Build complete business model
BusinessAgent.analyze_competitive_position()  # Competitive analysis
BusinessAgent.forecast_growth()  # Revenue projections
BusinessAgent.optimize_pricing()  # Pricing strategy
```

**Use Cases:**
- Design business model
- Evaluate unit economics
- Determine scaling readiness
- Analyze competition
- Forecast growth
- Optimize pricing

---

### 6. **Innovation Agent** (481 lines)
**Innovation frameworks and product strategy**

**Specialties:**
- Jobs to be Done (JTBD) framework
- Blue Ocean Strategy
- Design Thinking process
- Disruption patterns (performance, convenience, cost, experience, model)
- Trend analysis and opportunity identification
- Ideation techniques (SCAMPER, brainwriting, lateral thinking)
- Product roadmapping

**Key Methods:**
```python
InnovationAgent.analyze_jobs_to_be_done()  # Analyze customer jobs
InnovationAgent.design_blue_ocean()  # Create uncontested market space
InnovationAgent.identify_market_opportunities()  # Find opportunities
InnovationAgent.disruption_strategy()  # Design disruption approach
InnovationAgent.ideation_techniques()  # Get ideation prompts
InnovationAgent.validate_innovation()  # Validate new ideas
```

**Use Cases:**
- Innovate new products
- Find market opportunities
- Design disruption strategies
- Conduct innovation workshops
- Validate product ideas
- Analyze market trends

---

### 7. **Development Agent** (462 lines)
**Technical strategy and growth hacking**

**Specialties:**
- Tech stack selection and architecture decisions
- Growth hacking tactics (product, content, referral, paid, partnership)
- MVP strategy and feature prioritization
- Feature prioritization frameworks (RICE, Kano, Value vs Effort)
- Technical debt management
- Automation opportunities
- Growth metrics framework

**Key Methods:**
```python
DevelopmentAgent.recommend_tech_stack()  # Which tech stack?
DevelopmentAgent.design_growth_hack()  # Design growth experiment
DevelopmentAgent.create_mvp_roadmap()  # MVP development plan
DevelopmentAgent.prioritize_features()  # Prioritize using framework
DevelopmentAgent.assess_technical_debt()  # Evaluate technical debt
DevelopmentAgent.identify_automation_opportunities()  # What to automate?
```

**Use Cases:**
- Select technology stack
- Design growth experiments
- Build MVP roadmap
- Prioritize features
- Manage technical debt
- Identify automation

---

### 8. **Financial Agent** (547 lines)
**Financial modeling and pricing strategy**

**Specialties:**
- Financial modeling and projections (monthly, annual, scenarios)
- Pricing strategies (cost-plus, value-based, competitive, dynamic, usage-based, tiered)
- Pricing research methods (Van Westendorp, conjoint analysis)
- Psychological pricing tactics
- Gross margin optimization
- Unit economics and CAC/LTV
- Financial scenario analysis

**Key Methods:**
```python
FinancialAgent.recommend_pricing_strategy()  # Which pricing strategy?
FinancialAgent.create_pricing_model()  # Build tiered pricing
FinancialAgent.build_financial_model()  # Project financials 24 months
FinancialAgent.calculate_unit_economics_detailed()  # Detailed unit econ
FinancialAgent.optimize_gross_margin()  # Improve profitability
FinancialAgent.price_sensitivity_analysis()  # Price elasticity analysis
```

**Use Cases:**
- Design pricing strategy
- Create pricing models
- Build financial projections
- Optimize unit economics
- Improve gross margin
- Analyze price sensitivity

---

### 9. **Negotiation Agent** (533 lines)
**Negotiation frameworks and deal strategy**

**Specialties:**
- Negotiation frameworks (BATNA, anchoring, ZOPA, win-win, concessions)
- Negotiation types (customer, supplier, employment, partnership, investment)
- Negotiation tactics (information gathering, listening, patience, bracketing, flinching, nibbling)
- Deal structures (straight transaction, payment plans, volume discounts, contingent payment)
- Objection handling in negotiation
- Closing strategies

**Key Methods:**
```python
NegotiationAgent.prepare_negotiation()  # Pre-negotiation preparation
NegotiationAgent.analyze_negotiation_position()  # Analyze your position
NegotiationAgent.create_offer()  # Create opening offer
NegotiationAgent.handle_objection()  # Handle negotiation objection
NegotiationAgent.build_deal_structure()  # Design deal structure
NegotiationAgent.closing_strategies()  # Get closing approaches
```

**Use Cases:**
- Prepare for negotiations
- Analyze negotiation position
- Negotiate customer deals
- Negotiate supplier terms
- Negotiate employment
- Structure deals

---

### 10. **Storytelling Agent** (577 lines)
**Brand storytelling and communication frameworks**

**Specialties:**
- Brand storytelling (origin, mission, customer stories)
- Communication frameworks (Hero's Journey, Pixar structure, TED talks, problem-solution)
- Pitch decks and investor narratives
- Customer case studies and testimonials
- Content narratives and messaging variations
- Storytelling for different audiences

**Key Methods:**
```python
StorytellingAgent.craft_brand_story()  # Build brand narrative
StorytellingAgent.create_customer_case_study()  # Create case study
StorytellingAgent.build_pitch_narrative()  # Build pitch story
StorytellingAgent.design_investor_pitch()  # Design investor pitch deck
StorytellingAgent.apply_heroes_journey()  # Apply Hero's Journey framework
StorytellingAgent.create_content_narratives()  # Tailor narratives by segment
```

**Use Cases:**
- Craft brand story
- Create investor pitch
- Build case studies
- Design pitch decks
- Develop messaging
- Apply storytelling frameworks

---

## Integration with SellIA

### How They Work Together

Each specialist agent:
1. **Integrates with LLM** - Uses Claude for advanced reasoning and creativity
2. **Provides frameworks** - Gives structured methodologies, not just advice
3. **Suggests metrics** - Recommends KPIs to validate effectiveness
4. **Learns from context** - Takes into account business stage, market, goals
5. **Enables next steps** - Provides actionable recommendations

### Usage Example

```python
from backend.app.core.agents.specialists import (
    MethodologyAgent,
    SalesAgent,
    BusinessAgent,
)

# 1. Recommend methodology for business stage
methodology = MethodologyAgent.recommend_framework(
    business_type="b2b_saas",
    business_stage="growth"
)

# 2. Get sales methodology for deal type
sales_approach = SalesAgent.recommend_methodology(
    deal_size=50000,
    cycle_length_months=6,
    complexity="complex"
)

# 3. Evaluate business model viability
unit_econ = BusinessAgent.calculate_unit_economics(
    arpu=5000,
    cac=1500,
    gross_margin=0.75,
    avg_customer_lifetime_months=36
)
```

---

## Key Metrics and KPIs by Agent

### Methodology Agent
- Framework adoption rate
- Goal achievement rate (OKRs)
- Process maturity score

### Sales Agent
- Win rate, deal size, sales cycle length
- Conversion rate by stage
- Objection win rate

### Marketing Agent
- CAC by channel, ROAS, CTR
- Content engagement, lead quality
- Customer journey conversion rates

### Advertising Agent
- ROAS, CPA, CPL
- Creative performance (CTR, conversion)
- Budget efficiency

### Business Agent
- Unit economics (LTV:CAC, payback period)
- Gross margin, MRR/ARR growth
- Retention rate, churn

### Innovation Agent
- Time to market, MVP build time
- Feature adoption rate
- Market opportunity size

### Development Agent
- Velocity, deployment frequency
- Technical debt score
- Growth loop viral coefficient

### Financial Agent
- Revenue forecast accuracy
- Gross margin %, pricing elasticity
- Runway, burn rate

### Negotiation Agent
- Deal closure rate
- Price realization
- Contract terms satisfaction

### Storytelling Agent
- Brand recall, engagement
- Conversion from content
- Case study impact (leads from case studies)

---

## Architecture

```
backend/app/core/agents/specialists/
├── __init__.py                  # Module exports and registry
├── methodology_agent.py          # 557 lines - Business frameworks
├── sales_agent.py               # 647 lines - Sales methodologies
├── marketing_agent.py           # 648 lines - Marketing strategy
├── advertising_agent.py         # 496 lines - Paid advertising
├── business_agent.py            # 472 lines - Business model
├── innovation_agent.py          # 481 lines - Innovation frameworks
├── development_agent.py         # 462 lines - Technical strategy
├── financial_agent.py           # 547 lines - Financial modeling
├── negotiation_agent.py         # 533 lines - Negotiation tactics
├── storytelling_agent.py        # 577 lines - Brand storytelling
└── SPECIALISTS.md               # This documentation

Total: ~5,100 lines of production-ready code
```

---

## Design Principles

1. **Frameworks Over Opinions** - Provide tested frameworks, not just advice
2. **Structured Output** - Return dictionaries with clear field meanings
3. **Business Context** - Adapt recommendations based on business stage, type, goals
4. **Actionable Guidance** - Always include next steps and success metrics
5. **Ethical Defaults** - Align with SellIA's commitment to ethical sales
6. **Extensibility** - Easy to add new frameworks and methodologies
7. **Integration Ready** - Work seamlessly with LLM and other agents

---

## Development Roadmap

Future enhancements:
- Integration with LLM for conversational access
- Multi-language support
- Customizable frameworks per industry
- A/B testing framework comparison
- Competitor monitoring integration
- Real-time market data integration
- Team collaboration features

---

## Authors

Created for SellIA - Ethical Sales Automation Platform

Framework credits:
- Jobs to be Done: Clayton Christensen
- Blue Ocean: Kim & Mauborgne
- MEDDIC: Dick Dunkel
- SPIN Selling: Neil Rackham
- Storytelling: Joseph Campbell, Pixar, TED
- OKRs: John Doerr, Andy Grove
- Lean Startup: Eric Ries
- Design Thinking: IDEO, Stanford

---

## License

Part of SellIA Platform - Internal Use
