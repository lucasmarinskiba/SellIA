# Sellía Brain Prompt Library — 200 High-Converting Prompts

**Status**: Production-Ready | **Lines**: ~3,500 | **Coverage**: Marketing, Sales, Positioning, Retention

## Overview

This library provides **200 expertly-crafted prompts** organized into 4 strategic domains to fuel the Sellía Brain autonomous sales system:

- **50 Marketing Prompts** (1,000 lines) — Content creation, campaigns, channels, conversion
- **50 Sales Prompts** (900 lines) — Discovery, qualification, proposals, closing
- **50 Positioning Prompts** (800 lines) — Value propositions, messaging, competitive strategy
- **50 Retention Prompts** (800 lines) — Onboarding, engagement, churn prevention, NPS

Each prompt includes:
- ✅ Business context and objectives
- ✅ Detailed template with variable placeholders
- ✅ Real-world example inputs and outputs
- ✅ Success metrics and KPIs
- ✅ Industry-specific variations (SaaS, Real Estate, E-commerce, Services)
- ✅ Best practices and tactical tips
- ✅ Adaptable frameworks, not rigid scripts

---

## Quick Start

### 1. Load the Registry

```python
from app.core.prompts import PromptRegistry, PromptOrchestrator

# Initialize registry (auto-loads all 200 prompts)
registry = PromptRegistry()

# Show stats
stats = registry.get_statistics()
print(f"Loaded {stats['total_prompts']} prompts across {stats['total_categories']} categories")
```

### 2. Find a Prompt

```python
# Search by tag
cold_email_prompts = registry.search_by_tag("copywriting")

# Search by category
sales_discovery = registry.search_by_category("Discovery")

# Search by industry
saas_positioning = registry.search_by_industry("SaaS")

# Get recommended prompts for use case
lead_gen_prompts = registry.get_recommended_prompts("lead_generation")
```

### 3. Execute a Prompt

```python
from app.core.prompts import PromptOrchestrator

orchestrator = PromptOrchestrator(registry)
orchestrator.set_llm_client(your_llm_client)  # Claude, OpenAI, etc.

# Get a prompt
prompt = registry.get_prompt("marketing_001")  # Blog Post Generator

# Prepare context
context = {
    "product_name": "TaskFlow",
    "target_audience": "Project managers",
    "target_keyword": "project management for startups",
    "word_count": "2000",
    "tone": "Friendly, authoritative",
    # ... other variables
}

# Execute
result = orchestrator.execute(prompt, context)
print(result['result'])  # Generated content

# Record effectiveness
orchestrator.record_effectiveness(result['execution_id'], effectiveness_score=0.85)
```

---

## Prompt Categories

### MARKETING PROMPTS (50)

**Content Creation (10)**
- Blog Post Generator (marketing_001)
- Video Script Creator (marketing_002)
- Email Sequence Architect (marketing_003)
- Social Media Content Calendar (marketing_004)
- Copywriting Swipe File (marketing_005)
- Influencer Collaboration Briefing (marketing_006)
- User-Generated Content Campaign (marketing_007)
- Competitor Positioning Analysis (marketing_008)
- Seasonal Campaign Framework (marketing_009)
- [10 more...]

**Campaign Strategy (10)**
- Seasonal Campaign Framework
- Promotional Campaign Planner
- Awareness Campaign Builder
- Conversion Optimization Framework
- Growth Mechanics Designer
- [5 more...]

**Channel Selection (10)**
- Organic vs. Paid Strategy
- Platform Selection Matrix
- Partnership Channel Development
- Distribution Channel Optimizer
- [6 more...]

**Audience Analysis (10)**
- Demographic Analysis Framework
- Psychographic Profiling
- Behavior Segmentation Model
- Persona Development Template
- [6 more...]

**Conversion & Retention (10)**
- Landing Page Conversion Optimizer
- Sales Funnel Architecture
- Retention Marketing Framework
- Churn Prevention Playbook
- Customer Lifetime Value Maximizer
- [5 more...]

### SALES PROMPTS (50)

**Discovery (10)**
- Discovery Question Generator (sales_001)
- Pain Point Discovery Framework (sales_002)
- Buyer Persona Deep-Dive
- Competition Benchmarking Questions
- Use Case Mapping
- [5 more...]

**Qualification (10)**
- Qualification Scoring Framework (sales_011)
- MEDDIC Deep-Dive
- Decision Process Mapper
- Budget Discovery Script
- Buying Committee Identifier
- [5 more...]

**Proposal (10)**
- Proposal Structure Template (sales_021)
- ROI Calculator Template
- Value Prop Builder
- Case Study Integration Framework
- Risk Mitigation Playbook
- [5 more...]

**Negotiation (10)**
- Objection Handling Playbook
- Concession Strategy Framework
- Price Negotiation Guide
- Deal Structure Optimizer
- Win-Loss Analysis Template
- [5 more...]

**Closing (10)**
- Closing Techniques Playbook
- Urgency Creation Framework
- Risk Reversal Strategies
- Final Push Template
- Verbal Closing Scripts
- [5 more...]

**Account Management (10)**
- Expansion Opportunity Identifier
- Renewal Strategy Playbook
- Account Health Scoring
- Executive Relationship Builder
- Upsell Timing Framework
- [5 more...]

### POSITIONING PROMPTS (50)

**Value Proposition (10)**
- Value Proposition Builder (positioning_001)
- Benefit Articulation Framework
- Differentiation Statement Creator
- Unique Selling Proposition (USP) Designer
- Target Customer Value Mapper
- [5 more...]

**Brand Messaging (10)**
- Brand Voice & Tone Guide
- Messaging Hierarchy Builder
- Tagline & Slogan Generator
- Brand Story Framework
- Competitive Message Mapping
- [5 more...]

**Competitive Positioning (10)**
- Competitive Positioning Strategy (positioning_011)
- Competitor Benchmarking Framework
- Market Gap Identifier
- Attack & Defend Strategy
- Positioning Matrix Builder
- [5 more...]

**Market Positioning (10)**
- Market Segment Selector
- Niche Positioning Framework
- Target Market Definition
- Go-To-Market Strategy Builder
- Market Entry Playbook
- [5 more...]

**Pricing Strategy (10)**
- Value-Based Pricing Model
- Competitive Pricing Strategy
- Psychological Pricing Framework
- Price Testing Template
- Pricing Tier Optimizer
- [5 more...]

### RETENTION PROMPTS (50)

**Customer Experience (10)**
- Onboarding Optimization Framework (retention_001)
- Support Excellence Framework
- Customer Delight Playbook
- Feedback Loop Builder
- Experience Journey Mapper
- [5 more...]

**Engagement (10)**
- Engagement Campaigns Playbook
- Community Building Framework
- Feature Adoption Accelerator
- Email Nurture Sequences
- In-App Messaging Strategy
- [5 more...]

**Churn Prevention (10)**
- Churn Prediction & Prevention (retention_011)
- At-Risk Customer Playbook
- Win-Back Campaign Framework
- Retention Metrics Dashboard
- Intervention Strategy Builder
- [5 more...]

**Loyalty (10)**
- Loyalty Program Designer
- Recognition & Rewards Framework
- VIP Customer Strategy
- Exclusive Benefits Program
- Referral Incentive Designer
- [5 more...]

**Upsell/Cross-sell (10)**
- Upsell Opportunity Identifier
- Cross-sell Timing Framework
- Feature Adoption Accelerator
- Expansion Revenue Maximizer
- Customer Success Metrics
- [5 more...]

**Win-Back (10)**
- Reactivation Campaign Framework
- Win-Back Messaging
- Competitive Counter-Strategy
- Customer Recovery Playbook
- Relationship Rebuilding Script
- [5 more...]

---

## Prompt Structure

Each prompt follows this standardized structure:

```python
@dataclass
class PromptTemplate:
    id: str                                    # Unique ID (e.g., "marketing_001")
    name: str                                  # Human-readable name
    category: str                              # Category (e.g., "Content Creation")
    business_context: str                      # Why this prompt matters
    prompt_text: str                           # Template with {placeholders}
    variables: List[str]                       # Required context variables
    example_input: Dict[str, Any]             # Example variable values
    example_output: str                        # Expected output
    success_metrics: List[str]                # KPIs to measure success
    industry_variations: Dict[str, str]       # Variations for different industries
    best_practices: List[str]                 # Tactical tips
    tags: List[str]                           # Searchable tags
```

---

## Usage Examples

### Example 1: Generate a Blog Post

```python
prompt = registry.get_prompt("marketing_001")  # Blog Post Generator

context = {
    "product_name": "TaskFlow",
    "target_audience": "Startup founders",
    "target_keyword": "project management for startups",
    "word_count": "2000",
    "content_focus": "Time-saving productivity tips",
    "tone": "Friendly, authoritative",
    "unique_angle": "First-hand founder experiences",
    "conversion_goal": "Free trial signup"
}

result = orchestrator.execute(prompt, context)
# Returns: Full SEO-optimized blog post outline + copy
```

### Example 2: Create a Discovery Call Script

```python
prompt = registry.get_prompt("sales_001")  # Discovery Question Generator

context = {
    "prospect_company": "Acme Corp",
    "prospect_role": "VP of Operations",
    "current_solution": "Spreadsheets + Asana",
    "suspected_challenge": "Missed deadlines",
    # ... more variables
}

result = orchestrator.execute(prompt, context)
# Returns: Full discovery call script with opening, questions, transitions
```

### Example 3: Build a Value Proposition

```python
prompt = registry.get_prompt("positioning_001")  # Value Prop Builder

context = {
    "product_name": "TaskFlow",
    "target_customer": "Project managers at teams under 200",
    "customer_problem": "Missing 30-40% of deadlines",
    # ... more variables
}

result = orchestrator.execute(prompt, context)
# Returns: 3 tested value proposition options + elevator pitch
```

### Example 4: Design Churn Prevention

```python
prompt = registry.get_prompt("retention_011")  # Churn Prediction & Prevention

context = {
    "product_name": "TaskFlow",
    "current_churn_rate": "5",
    "churn_reason_1": "Feature gap",
    # ... more variables
}

result = orchestrator.execute(prompt, context)
# Returns: Churn risk scoring model, intervention playbook, monitoring strategy
```

---

## Industry Variations

Each prompt includes variations optimized for specific industries:

- **SaaS**: ROI-focused, feature comparison, implementation timelines
- **E-commerce**: Product benefits, urgency/scarcity, styling tips
- **Real Estate**: Market analysis, investment returns, financing
- **Services**: Expertise differentiation, project delivery, client outcomes
- **Consulting**: Industry insights, thought leadership, methodology
- **Healthcare**: Compliance, patient outcomes, regulatory focus
- **Finance**: Risk management, compliance, performance metrics
- **Tech Startups**: Growth metrics, fundraising, product-market fit

To get industry-specific variations:

```python
# Get a prompt with industry variation
saas_variation = registry.search_by_industry("SaaS")
real_estate_variation = registry.search_by_industry("Real Estate")

# Use in context
prompt = registry.get_prompt("positioning_001")
industry_note = prompt.industry_variations.get("SaaS")
# Returns: "ROI-focused, feature comparison, free trial positioning"
```

---

## API Reference

### PromptRegistry

```python
registry = PromptRegistry()

# Lookups
registry.get_prompt(prompt_id)                    # Get prompt by ID
registry.search_by_tag(tag)                       # Find by tag
registry.search_by_category(category)             # Find by category
registry.search_by_industry(industry)             # Find by industry
registry.search(query, search_type='tag')         # General search
registry.get_by_industry_and_category(ind, cat)  # Combined filter
registry.get_recommended_prompts(use_case)        # Suggested for use case

# Management
registry.get_statistics()                         # Registry stats
registry.record_effectiveness(prompt_id, score)   # Log effectiveness
registry.get_top_prompts_by_effectiveness(limit) # Top performers
registry.export_prompts(filter_category)          # Export for sharing
registry.list_all_prompts()                       # All with metadata
```

### PromptOrchestrator

```python
orchestrator = PromptOrchestrator(registry)
orchestrator.set_llm_client(client)

# Execution
orchestrator.execute(prompt, context_vars)        # Run a prompt
orchestrator.batch_execute(prompts_list)          # Run multiple
orchestrator.prepare_prompt(prompt, context)      # Generate template
orchestrator.validate_context(prompt, context)    # Check vars

# Tracking
orchestrator.record_effectiveness(exec_id, score) # Log score
orchestrator.get_execution_history(prompt_id)     # View history
orchestrator.get_execution_stats()                # Performance stats
orchestrator.export_execution_logs(filename)      # Export logs

# Search
orchestrator.search_prompts(query, search_type)   # Find prompts
orchestrator.get_suggested_prompts(use_case)      # Recommendations
```

---

## Integration with Sellía Brain

The prompt library integrates seamlessly with the Sellía Brain orchestration system:

```python
# In BrainOrchestratorV3
from app.core.prompts import PromptRegistry, PromptOrchestrator

class BrainOrchestratorV3:
    def __init__(self):
        self.prompt_registry = PromptRegistry()
        self.prompt_orchestrator = PromptOrchestrator(self.prompt_registry)

    def customize_prompt(self, seller_id: str, prompt: str) -> str:
        """Use registry to fetch and customize prompts."""
        # Get market context
        context = self.get_market_context(seller_id)

        # Get appropriate prompt from registry
        suitable_prompt = self.prompt_registry.search_by_industry(context['market'])

        # Inject market context
        return self.prompt_orchestrator.execute(suitable_prompt, context)
```

---

## Performance & Metrics

### Prompt Usage Tracking

The system automatically tracks:
- **Times used**: How often each prompt is executed
- **Effectiveness score**: Average effectiveness rating (0-100)
- **Execution time**: Duration to generate output
- **Error rate**: Failures or missing variables

### Top Performers (Sample Data)

```
1. Blog Post Generator (marketing_001)           — 156 uses, 0.87 effectiveness
2. Sales Discovery Script (sales_001)            — 143 uses, 0.85 effectiveness
3. Value Proposition Builder (positioning_001)  — 131 uses, 0.89 effectiveness
4. Churn Prevention Playbook (retention_011)    — 98 uses, 0.82 effectiveness
5. Email Sequence Architect (marketing_003)     — 87 uses, 0.84 effectiveness
```

View top performers:

```python
top_prompts = registry.get_top_prompts_by_effectiveness(limit=10)
for p in top_prompts:
    print(f"{p['name']}: {p['effectiveness_score']:.2f} ({p['times_used']} uses)")
```

---

## Version Control & Updates

Each prompt tracks:
- **Version**: Current version (1.0, 1.1, etc.)
- **Created at**: Initial creation timestamp
- **Last updated**: Most recent modification
- **Changelog**: What changed and why

To view version info:

```python
meta = registry.metadata['marketing_001']
print(f"Version: {meta.version}")
print(f"Created: {meta.created_at}")
print(f"Updated: {meta.last_updated}")
```

---

## Best Practices

### 1. Always validate context before executing

```python
is_valid, missing_vars = orchestrator.validate_context(prompt, context_vars)
if not is_valid:
    print(f"Missing: {missing_vars}")
    # Gather missing data before executing
```

### 2. Use industry variations when available

```python
# Generic prompt
prompt = registry.get_prompt("positioning_001")

# Industry-specific guidance
if "SaaS" in prompt.industry_variations:
    industry_note = prompt.industry_variations["SaaS"]
    # "ROI-focused, feature comparison, free trial positioning"
```

### 3. Record effectiveness to improve recommendations

```python
result = orchestrator.execute(prompt, context)
# ... get effectiveness score from results ...
orchestrator.record_effectiveness(result['execution_id'], score=0.85)
```

### 4. Use recommended prompts for common use cases

```python
use_cases = [
    'lead_generation',
    'sales_discovery',
    'deal_closing',
    'customer_retention',
    'brand_positioning',
    'revenue_expansion'
]

recommended = orchestrator.get_suggested_prompts('lead_generation')
# Returns top 5 prompts for lead generation
```

### 5. Batch execute related prompts for efficiency

```python
prompts_to_run = [
    {'prompt': prompt1, 'context_vars': context1},
    {'prompt': prompt2, 'context_vars': context2},
    {'prompt': prompt3, 'context_vars': context3},
]

results = orchestrator.batch_execute(prompts_to_run)
```

---

## Troubleshooting

### Missing Context Variables

```
Error: Missing context variables: product_name, target_audience
```

**Solution**: Check the prompt's `variables` list and provide all required values:

```python
prompt = registry.get_prompt("marketing_001")
print("Required variables:", prompt.variables)
# Provide all variables in context_vars
```

### Execution Timeout

```python
# Set timeout on LLM client
orchestrator.set_llm_client(client_with_timeout)

# Or check execution stats for slow prompts
stats = orchestrator.get_execution_stats()
print(f"Average duration: {stats['average_duration_ms']}ms")
```

### Low Effectiveness Scores

```python
# Find underperforming prompts
low_performers = [p for p in registry.list_all_prompts() 
                  if p['effectiveness'] < 0.70]

# Review and update those prompts
for p in low_performers:
    print(f"Review: {p['name']} ({p['effectiveness']:.2f})")
```

---

## File Structure

```
app/core/prompts/
├── __init__.py                      # Package exports
├── marketing_prompts.py             # 50 marketing prompts (65KB)
├── sales_prompts.py                 # 50 sales prompts (49KB)
├── positioning_prompts.py           # 50 positioning prompts (30KB)
├── retention_prompts.py             # 50 retention prompts (39KB)
├── prompt_registry.py               # Registry + indexing (10KB)
├── prompt_orchestrator.py           # Execution engine (10KB)
└── README.md                        # This file
```

**Total**: ~200KB, ~3,500 lines of prompt content + infrastructure

---

## Contributing & Updates

To add new prompts or update existing ones:

1. **Find the right category**: Marketing, Sales, Positioning, or Retention
2. **Use the PromptTemplate structure**: Ensure all fields are populated
3. **Add industry variations**: Include at least 2-3 industry-specific notes
4. **Test with example input/output**: Validate the prompt works
5. **Update version number**: Increment from 1.0 → 1.1 → 2.0
6. **Document changes**: Add to changelog

```python
# Example: Adding a new sales prompt
new_prompt = SalesPromptTemplate(
    id="sales_051",  # New ID
    name="Competitor Switch Prevention",
    stage=SalesStage.NEGOTIATION.value,
    # ... rest of template
)
```

---

## Support & Questions

For questions, issues, or feature requests:

- **Registry questions**: Check `PromptRegistry.get_statistics()` output
- **Execution issues**: Check `PromptOrchestrator.get_execution_stats()`
- **Prompt content**: Review prompt.example_output for guidance
- **LLM integration**: Ensure `set_llm_client()` is called before execution

---

## License & Usage

These prompts are part of the Sellía Brain system. Use them to:
- ✅ Fuel autonomous sales execution
- ✅ Train sales teams
- ✅ Guide customer interactions
- ✅ Drive marketing campaigns
- ✅ Build retention strategies

Do not:
- ❌ Sell prompts separately
- ❌ Use without attribution
- ❌ Share outside organization

---

**Created**: July 2026 | **Status**: Production | **Next Review**: October 2026
