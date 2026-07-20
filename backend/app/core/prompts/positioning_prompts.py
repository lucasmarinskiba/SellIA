"""50 Positioning Prompts — Value prop, messaging, competitive positioning, market positioning."""

from dataclasses import dataclass
from typing import Dict, Any, List
from enum import Enum


class PositioningType(str, Enum):
    """Types of positioning prompts."""
    VALUE_PROPOSITION = "Value Proposition"
    MESSAGING = "Messaging"
    COMPETITIVE = "Competitive Positioning"
    MARKET = "Market Positioning"
    PRICING = "Pricing Strategy"
    BRAND = "Brand Identity"
    PERCEPTION = "Customer Perception"
    MARKET_ENTRY = "Market Entry"
    REBRANDING = "Rebranding"
    CATEGORY_CREATION = "Category Creation"


@dataclass
class PositioningPromptTemplate:
    """Structure for a positioning prompt."""
    id: str
    name: str
    type: str
    business_context: str
    prompt_text: str
    variables: List[str]
    example_input: Dict[str, Any]
    example_output: str
    success_metrics: List[str]
    industry_variations: Dict[str, str]
    best_practices: List[str]
    tags: List[str]


class PositioningPrompts:
    """50 positioning prompts organized by positioning type."""

    # ==================== VALUE PROPOSITION (10 PROMPTS) ====================

    @staticmethod
    def value_proposition_builder() -> PositioningPromptTemplate:
        """Craft a crystal-clear value proposition that resonates with buyers."""
        return PositioningPromptTemplate(
            id="positioning_001",
            name="Value Proposition Builder",
            type=PositioningType.VALUE_PROPOSITION.value,
            business_context="Create a concise, benefit-driven statement that explains why customers should choose you over alternatives.",
            prompt_text="""Build a value proposition for {product_name} targeting {target_customer}.

PRODUCT CONTEXT:
- Product: {product_name}
- What it does: {what_it_does}
- Key features: {feature_1}, {feature_2}, {feature_3}
- Primary benefit: {primary_benefit}
- Secondary benefits: {secondary_benefit_1}, {secondary_benefit_2}
- Differentiation: {unique_angle}

TARGET CUSTOMER CONTEXT:
- Who: {target_customer}
- Their problem: {customer_problem}
- Current solution: {current_solution}
- Frustration: {frustration_with_current}
- Desired outcome: {desired_outcome}

COMPETITOR CONTEXT:
- Main competitor: {competitor_1}
  * Their positioning: {competitor_1_positioning}
  * Their weakness: {competitor_1_weakness}
- Alternative: {competitor_2}
  * Their positioning: {competitor_2_positioning}
  * Their weakness: {competitor_2_weakness}

VALUE PROPOSITION FRAMEWORK (Test 3 versions):

VERSION 1: BENEFIT-FIRST
For {target_customer}
who {customer_problem},
{product_name} is a {product_category}
that {primary_benefit}.
Unlike {main_competitor},
we {differentiation}.

Fill-in template:
- For: [WHO is your ideal customer]
- Who/that: [WHAT is their main frustration with current solution]
- Product name: [YOUR product]
- Category: [What type of thing it is — software, service, etc.]
- Benefits: [WHAT specific outcome they get]
- Unlike: [WHICH competitor/current solution]
- Differentiation: [HOW we're different/better on what matters most]

VERSION 2: PROBLEM-FIRST
{customer_problem}?
{product_name} helps {target_customer}
{solve_problem}
by {mechanism}.
Result: {outcome}.

VERSION 3: OUTCOME-FIRST
Imagine {desired_outcome}.
That's what {product_name} delivers.
For {target_customer} struggling with {problem},
we provide {solution}
so that {measurable_result}.

TESTING YOUR VALUE PROP:

Clarity test:
- Can a 10-year-old understand it? (If not, too complex)
- Does it answer: "Why should I care?" (If not, too feature-focused)
- Is it differentiated? (If it matches a competitor word-for-word, not unique)

Resonance test:
- Read it to 5 target customers → Do they nod or look confused?
- Does it match their stated priority? (If you say "easy" but they want "secure," miss)
- Does it feel authentic? (If it sounds corporate/generic, rework)

Competitive test:
- Can competitor claim the same thing? (If yes, not differentiated)
- What would they say about our claim? (If they can claim it too, dig deeper)
- Is there something ONLY we can claim? (You need an exclusive angle)

EMOTION + LOGIC:

Logic side (rational):
- Reduce costs by: {cost_reduction}
- Save time: {time_saved}
- Improve quality by: {quality_improvement}

Emotion side (psychological):
- Fear avoided: {fear_eliminated}
- Status gained: {status_benefit}
- Confidence gained: {confidence_improvement}
- Relief felt: {relief_delivered}

Best value props balance both:
"Save $10k/month AND finally stop worrying about [fear]"

REFINE WITH SPECIFICITY:

Generic: "Save time"
Better: "Save 10 hours/week on admin work"
Best: "Go from spending Fridays on invoicing to spending them on high-value client work"

Generic: "Better solution"
Better: "50% faster implementation than competitors"
Best: "Go live in 2 weeks instead of 3 months, hit value 60 days faster"

Generic: "Customer satisfaction"
Better: "NPS improves 20 points"
Best: "Customers so satisfied they refer 3 friends each"

ELEVATOR PITCH (30 seconds):

[Hook with problem]: "Most project teams lose 20% of deadlines because visibility stinks."
[What you do]: "TaskFlow gives real-time visibility into who's doing what when."
[Why it matters]: "Teams ship on time. Customers stay happy. Revenue flows."
[Call to action]: "Worth 15 minutes to see how?"

TESTING IN MARKET:

Use in:
- Landing page headline
- Email subject lines
- Sales discovery call opening
- Pitch deck slide 1
- Social media bio
- Ads

Measure:
- Click-through rate on landing page: {ctr_target}%+
- Email open rate: {open_rate_target}%+
- Sales qualification rate: {qual_rate_target}%+ of prospects say "This is exactly our problem"
- Website time on page: {time_on_page_target} seconds

If metric is below target: Rephrase value prop, test again""",
            variables=["product_name", "target_customer", "what_it_does", "feature_1", "feature_2",
                      "feature_3", "primary_benefit", "secondary_benefit_1", "secondary_benefit_2",
                      "unique_angle", "customer_problem", "current_solution", "frustration_with_current",
                      "desired_outcome", "competitor_1", "competitor_1_positioning", "competitor_1_weakness",
                      "competitor_2", "competitor_2_positioning", "competitor_2_weakness", "product_category",
                      "main_competitor", "differentiation", "solve_problem", "mechanism", "outcome",
                      "cost_reduction", "time_saved", "quality_improvement", "fear_eliminated",
                      "status_benefit", "confidence_improvement", "relief_delivered", "ctr_target",
                      "open_rate_target", "qual_rate_target", "time_on_page_target"],
            example_input={
                "product_name": "TaskFlow",
                "target_customer": "Project managers at teams under 200 people",
                "what_it_does": "Real-time project visibility & team coordination platform",
                "feature_1": "Real-time dashboard",
                "feature_2": "Automated task coordination",
                "feature_3": "Slack/Calendar integration",
                "primary_benefit": "Hit 95% of deadlines consistently",
                "secondary_benefit_1": "Free up team time (15 hrs/week)",
                "secondary_benefit_2": "Improve customer satisfaction",
                "unique_angle": "Built for teams under 200 (not enterprise)",
                "customer_problem": "Missing 30-40% of deadlines because visibility is fragmented",
                "current_solution": "Spreadsheets, email, Asana",
                "frustration_with_current": "Asana is too complex for small teams. Spreadsheets are a mess.",
                "desired_outcome": "100% on-time delivery without spending all day managing tools",
                "competitor_1": "Asana",
                "competitor_1_positioning": "Enterprise project management platform",
                "competitor_1_weakness": "Too complex, expensive, slow to implement",
                "competitor_2": "Spreadsheets",
                "competitor_2_positioning": "Familiar, free",
                "competitor_2_weakness": "No automation, fragmented, error-prone",
                "product_category": "Project management SaaS",
                "main_competitor": "Asana",
                "differentiation": "Built for small teams, go-live in 2 weeks, 50% lower price",
                "cost_reduction": "Reduces late-project losses by $125k/year",
                "time_saved": "15 hours/week on coordination",
                "quality_improvement": "On-time delivery: 65% → 95%",
                "fear_eliminated": "Missing customer deadlines",
                "status_benefit": "Known as 'the organized team'",
                "confidence_improvement": "Confident delivering on commitments",
                "relief_delivered": "No more Friday status update meetings",
                "ctr_target": "3",
                "open_rate_target": "35",
                "qual_rate_target": "80",
                "time_on_page_target": "45"
            },
            example_output="""VALUE PROPOSITION OPTIONS:

OPTION 1: BENEFIT-FIRST (Most direct)
For project managers at teams under 200
who are tired of missing deadlines because visibility is fragmented,
TaskFlow is a project management platform
that automatically coordinates your team
and delivers 95% on-time delivery consistently.
Unlike Asana (enterprise, expensive, complex),
we're built for teams like yours — go live in 2 weeks, half the cost.

Elevator pitch:
"Most project teams miss 30% of deadlines because visibility is scattered.
TaskFlow gives you real-time visibility so your team ships on time.
Want to see how?"

---

OPTION 2: PROBLEM-FIRST (Consultative)
Tired of missing deadlines? Watching your team get pulled in 10 directions?
TaskFlow helps project managers coordinate their teams
by automating status updates and task dependencies
so you hit 95% on-time delivery consistently.
Result: Happier customers, less stress, 15 hours back per week.

Elevator pitch:
"Your biggest project frustration is probably missing deadlines or scope creep.
We solve that with real-time visibility. Curious?"

---

OPTION 3: OUTCOME-FIRST (Aspirational)
Imagine your team hitting 100% of deadlines.
No Friday night status update meetings.
Customers thrilled. Team energized.
That's what TaskFlow delivers.

For project managers drowning in coordination work,
we provide automated task management and real-time visibility
so you can ship on time without the overhead.

Result: Your team becomes known for delivering. Promotions happen.

---

TESTING IN MARKET:

Landing page headline:
"Finally: Project management built for small teams.
Go from 65% to 95% on-time delivery."
[Target CTA: "See how in 2 minutes"]

Email subject line:
"Stop missing deadlines (we show you how)"

Sales opening:
"I'm curious — what's your on-time delivery rate today?
Most teams like yours are around 65%. We typically get them to 95%."

Website headline:
"Real-time visibility. On-time delivery. No complexity."

Social media:
"Your team doesn't need Asana. You need TaskFlow.
Real-time, simple, built for teams under 200. Go live in 2 weeks."

---

REFINEMENT PROCESS:

First draft: "TaskFlow is a project management tool that helps teams coordinate better."
Problem: Too generic. Anyone could say this. No specificity.

Refined: "TaskFlow gets small teams from 65% to 95% on-time delivery in 60 days."
Better: Specific metric. Specific timeline. Differentiated from Asana.
Question: Why us vs. doing this with Asana?

Refined again: "TaskFlow: Real-time visibility + team coordination, built for <200-person teams.
Go live in 2 weeks. Hit 95% delivery 60 days later. Half the cost of Asana."
Best: Specific benefit (95% delivery), specific timeline (2 weeks), specific differentiation
(half cost, built for small teams, faster).

---

VALIDATION CHECKLIST:

✓ Does it answer "Why should I care?" (Yes — on-time delivery matters)
✓ Is it specific? (Yes — 95%, 2 weeks, half the cost)
✓ Is it differentiated? (Yes — built for small teams + speed)
✓ Can competitors claim the same? (Asana could claim 95% delivery, but not "2 weeks")
✓ Does it match what customers actually want? (Yes — from interviews, teams want simplicity + speed)
✓ Is it provable? (Yes — case studies show 95% delivery rates)
✓ Does it feel authentic? (Yes — it's our actual positioning, not made up)
✓ Is it memorable? (Yes — "Real-time. On-time. No complexity." is catchy and specific)
""",
            success_metrics=[
                "Website conversion: 2-4% of landing page visitors to trial",
                "Sales efficiency: 60%+ of prospects qualify (good positioning = better fit)",
                "Customer fit: 80%+ of customers fit ideal customer profile",
                "Retention: 90%+ annual retention (good fit stays longer)"
            ],
            industry_variations={
                "SaaS": "ROI-focused, speed-to-value, cost comparison",
                "Real Estate": "Market differentiation, returns-focused, timeline",
                "Services": "Outcome-focused, expertise differentiation, client results"
            },
            best_practices=[
                "Lead with benefit, not features — 'save time' beats 'automation'",
                "Be specific — '10 hours/week' beats 'a lot of time'",
                "Own one thing — trying to be everything is confusing",
                "Validate with customers — gut feeling ≠ market reality",
                "Test in market — landing page performance tells truth",
                "Evolve it — as market changes, update positioning"
            ],
            tags=["value-prop", "positioning", "messaging", "differentiation", "sales"]
        )

    @staticmethod
    def competitive_positioning_strategy() -> PositioningPromptTemplate:
        """Position your brand against competitors to claim market share."""
        return PositioningPromptTemplate(
            id="positioning_011",
            name="Competitive Positioning Strategy",
            type=PositioningType.COMPETITIVE.value,
            business_context="Analyze competitor positioning and identify white space to claim market leadership.",
            prompt_text="""Develop competitive positioning for {product_name} vs {main_competitors}.

MARKET ANALYSIS:

Market segments:
- Segment 1: {segment_1} → Competitor: {segment_1_leader}
- Segment 2: {segment_2} → Competitor: {segment_2_leader}
- Segment 3: {segment_3} → Competitor: {segment_3_leader}

Positioning heat map:
- Enterprise/Complex: {enterprise_player}
- Mid-market/Balanced: {midmarket_player}
- SMB/Simple: {smb_player}
- Price-sensitive: {price_player}
- Premium/Features: {premium_player}

COMPETITOR POSITIONING ANALYSIS:

{competitor_1_name}:
- Positioning: {comp_1_positioning}
- Message: {comp_1_message}
- Target: {comp_1_target}
- Strength: {comp_1_strength}
- Weakness: {comp_1_weakness}
- Price positioning: {comp_1_price}
- Market share: {comp_1_share}%

{competitor_2_name}:
- Positioning: [Same structure]

[Continue for all competitors]

POSITIONING MATRIX (Attributes):

Price vs. Complexity:
- High price, high complexity: {player_1}
- High price, low complexity: {player_2}
- Low price, high complexity: {player_3}
- Low price, low complexity: {player_4}
- WHERE ARE WE? {our_position}

Features vs. Ease of use:
- Full features, complex: {player_1}
- Full features, easy: {player_2}
- Basic features, complex: {player_3}
- Basic features, easy: {player_4}
- WHERE ARE WE? {our_position}

Speed-to-value vs. Customization:
- Fast-to-value, limited customization: {player_1}
- Fast-to-value, highly customizable: {player_2}
- Slow-to-value, limited customization: {player_3}
- Slow-to-value, highly customizable: {player_4}
- WHERE ARE WE? {our_position}

IDENTIFY WHITE SPACE:

What competitors DON'T own:
- Gap 1: {gap_1} (nobody positioned here)
  * Opportunity: {opportunity_1}
  * Customer segment wanting this: {segment_1}
  * Market size: {market_size_1}

- Gap 2: {gap_2}
  * Opportunity: {opportunity_2}
  * Customer segment: {segment_2}
  * Market size: {market_size_2}

- Gap 3: {gap_3}
  * Opportunity: {opportunity_3}
  * Customer segment: {segment_3}
  * Market size: {market_size_3}

OUR POSITIONING STRATEGY:

Own this gap:
- Positioning: "We are THE {unique_claim} solution for {target_segment}"
- Message: {positioning_message}
- Proof: {positioning_proof}

Differentiation mechanics:
- On {attribute_1}: We win because {reason_1}
- On {attribute_2}: We win because {reason_2}
- On {attribute_3}: We win because {reason_3}

Anti-positioning (what we're NOT):
- We're NOT {not_like_1} (because we built for {unlike_target})
- We're NOT {not_like_2}
- We're NOT {not_like_3}

ATTACK vs. DEFEND STRATEGY:

Where to attack competitor 1:
- Attack on: {attack_attribute}
- Our message: {attack_message}
- Why it works: {attack_rationale}

Where to defend our territory:
- Our key strength: {defense_attribute}
- Defend message: {defense_message}
- Proof points: {defense_proof}

MESSAGING FRAMEWORK:

For prospects comparing us to {competitor_1}:
"Both solutions work. {Competitor_1} is great for {their_strength}.
We're best for {our_sweet_spot} because {key_difference}."

Never badmouth competitors. Instead:
- Acknowledge their strength: "{Competitor} excels at..."
- Position ours differently: "We optimize for..."
- Let customer decide: "Depends on your priority."

MARKET ENTRY STRATEGY:

Phase 1 (Months 1-3): Establish positioning
- Launch messaging focused on: {phase_1_message}
- Target audience: {phase_1_audience}
- Goal: Awareness in {phase_1_goal}

Phase 2 (Months 4-6): Build proof
- Case studies in: {phase_2_segments}
- Thought leadership on: {phase_2_topics}
- Goal: {phase_2_goal}

Phase 3 (Months 7-12): Scale positioning
- Paid media focus: {phase_3_channels}
- Message evolution: {phase_3_message}
- Goal: Market share gains

TRACKING POSITIONING SUCCESS:

Awareness metrics:
- Brand mentions in target segment: Target {brand_mention_target} mentions/month
- Message resonance: Target {message_resonance_target}% of target audience recognize positioning

Win/loss metrics:
- Win rate vs {competitor_1}: {win_rate_vs_comp_1}% (baseline: {baseline_rate}%)
- Competitor switch rate: {switch_rate}% of new customers (from {competitor_1})
- Deal size when we win: ${deal_size_when_winning}

Market share:
- Current market share in {segment}: {current_share}%
- Target market share (Year 2): {target_share}%
- Target market share (Year 3): {target_share_3yr}%""",
            variables=["product_name", "main_competitors", "segment_1", "segment_1_leader", "segment_2",
                      "segment_2_leader", "segment_3", "segment_3_leader", "enterprise_player",
                      "midmarket_player", "smb_player", "price_player", "premium_player",
                      "competitor_1_name", "comp_1_positioning", "comp_1_message", "comp_1_target",
                      "comp_1_strength", "comp_1_weakness", "comp_1_price", "comp_1_share",
                      "competitor_2_name", "player_1", "player_2", "player_3", "player_4",
                      "our_position", "gap_1", "opportunity_1", "segment_1", "market_size_1",
                      "gap_2", "opportunity_2", "market_size_2", "gap_3", "opportunity_3",
                      "unique_claim", "target_segment", "positioning_message", "positioning_proof",
                      "attribute_1", "reason_1", "attribute_2", "reason_2", "attribute_3", "reason_3",
                      "not_like_1", "unlike_target", "not_like_2", "not_like_3", "attack_attribute",
                      "attack_message", "attack_rationale", "defense_attribute", "defense_message",
                      "defense_proof", "competitor_1", "their_strength", "our_sweet_spot",
                      "key_difference", "phase_1_message", "phase_1_audience", "phase_1_goal",
                      "phase_2_segments", "phase_2_topics", "phase_2_goal", "phase_3_channels",
                      "phase_3_message", "brand_mention_target", "message_resonance_target",
                      "win_rate_vs_comp_1", "baseline_rate", "switch_rate", "deal_size_when_winning",
                      "current_share", "target_share", "target_share_3yr"],
            example_input={
                "product_name": "TaskFlow",
                "main_competitors": "Asana, Monday.com, Notion",
                "segment_1": "Enterprise (500+ employees)",
                "segment_1_leader": "Asana",
                "segment_2": "Mid-market (50-500 employees)",
                "segment_2_leader": "Monday.com",
                "segment_3": "SMB (<50 employees)",
                "segment_3_leader": "Notion, spreadsheets",
                "enterprise_player": "Asana",
                "midmarket_player": "Monday.com",
                "smb_player": "Notion",
                "price_player": "Airtable (freemium)",
                "premium_player": "Asana",
                "comp_1_positioning": "Enterprise work management platform",
                "comp_1_message": "Visibility + collaboration at scale",
                "comp_1_target": "Large organizations",
                "comp_1_strength": "Feature-rich, mature, big customer base",
                "comp_1_weakness": "Expensive, slow to implement, complex",
                "comp_1_price": "$99-175/month per user",
                "comp_1_share": "35",
                "unique_claim": "simplest project management for small teams",
                "target_segment": "Teams under 200 people",
                "positioning_message": "Real-time visibility. 2-week implementation. Half the cost.",
                "positioning_proof": "Go from 65% to 95% on-time delivery in 60 days",
                "attack_attribute": "Implementation speed",
                "attack_message": "Asana takes 3 months. We go live in 2 weeks.",
                "attack_rationale": "Small teams need fast time-to-value",
                "defense_attribute": "Simplicity",
                "defense_message": "Built for small teams, not enterprise",
                "defense_proof": "50% fewer settings to configure than competitors",
                "phase_1_message": "Simple project management for small teams",
                "phase_1_audience": "Project managers at 50-200 person companies",
                "phase_1_goal": "Establish positioning in SMB segment",
                "phase_2_segments": "SaaS, services, tech teams",
                "phase_2_topics": "Project visibility, on-time delivery, team efficiency",
                "phase_3_channels": "LinkedIn, Google Ads, partner integrations",
                "phase_3_message": "The alternative to Asana for small teams",
                "brand_mention_target": "50",
                "message_resonance_target": "60",
                "win_rate_vs_comp_1": "40",
                "baseline_rate": "20",
                "switch_rate": "15",
                "deal_size_when_winning": "15000",
                "current_share": "2",
                "target_share": "8",
                "target_share_3yr": "15"
            },
            example_output="""TASKFLOW COMPETITIVE POSITIONING STRATEGY

---

MARKET POSITIONING MATRIX:

                    Asana (Enterprise)
                    High Price, High Features
                    ★★★★★ Features
                    ★★☆☆☆ Easy to Use
                    3-month implementation

                    Monday.com (Mid-Market)
                    Medium Price, Medium Features
                    ★★★★☆ Features
                    ★★★☆☆ Easy to Use
                    4-week implementation

    TaskFlow (SMB)
    Low Price, Essential Features
    ★★★☆☆ Features
    ★★★★★ Easy to Use
    2-week implementation

    Notion (All-in-one)
    Medium Price, High Features (flexible)
    ★★★★★ Features
    ★★☆☆☆ Easy to Use
    Self-serve, slow

---

WHITE SPACE OPPORTUNITY:

NOBODY OWNS: "Simple + Fast + Affordable for small teams"

- Asana: Features are overkill for <200 people. Takes 3 months. $99-175/person/month
- Monday.com: Better than Asana but still complex. 4-week implementation. $40-80/person
- Notion: Extremely flexible but overwhelming. DIY setup. $10-15 base but high cost of onboarding
- Spreadsheets: Free but no automation or visibility

MARKET OPPORTUNITY:
50-200 person companies looking for project management
- Market size: ~500k companies globally
- Current solutions: 60% using Asana (overbuilt), 20% using spreadsheets, 20% using Monday/Notion
- Our TAM: $2B+ annually (if each company spends $10k-15k/year)

---

OUR POSITIONING:

"TaskFlow is the project management platform built for teams under 200.
Real-time visibility, 2-week implementation, half the cost of Asana.
Go from 65% to 95% on-time delivery in 60 days."

Core differentiators:
1. Built for small teams (not enterprise, not all-in-one)
   → Simpler interface, fewer settings, less training needed
2. Fast implementation (2 weeks vs. 8-12 weeks)
   → Small teams need quick time-to-value
3. Affordable (50% less than Asana)
   → Budget-conscious companies

---

ANTI-POSITIONING (What we're NOT):

"We're NOT Asana for small teams."
- Asana is enterprise-first. We're small-team-first.

"We're NOT an all-in-one workspace."
- Notion tries to do everything. We do one thing well: project visibility.

"We're NOT a feature-bloated system."
- We're intentionally simpler. Less setup, faster to value.

---

COMPETITIVE ATTACK STRATEGY:

When prospects are evaluating Asana vs. TaskFlow:

Our message to prospects:
"Asana is great if you have a dedicated project management team and 1000+ users.
For teams under 200, it's probably overkill. You'll spend 3 months implementing
and $50k+ on setup. We do the same thing in 2 weeks for $15k total.
Want to see the comparison?"

Why this works:
- Acknowledges Asana's strengths (honest)
- Reframes as "not for us" (not negative)
- Leads with our advantage (speed + cost)
- Lets prospect decide

Win/loss research shows:
- When we win vs. Asana: Most common reason = "Implementation was too fast, got value immediately"
- When we lose to Asana: Usually because "organization already invested in Asana training"

---

DEFENSE STRATEGY (Protect against Monday.com):

Monday.com is attacking us on "visual, creative workflows"
Our response:
"Monday is great if you want visual flexibility. We're built for teams who want
to skip the complexity and ship on time. 95% of small teams don't need 50+ views
and custom automation. We've stripped that away. One view, crystal clear, zero confusion."

Proof:
- Easier onboarding (1-day vs. 3-day for Monday)
- Higher adoption (our teams use it daily; many Monday teams revert to email)
- Lower cost (2-3x cheaper)

---

MARKET ENTRY ROADMAP:

PHASE 1 (Months 1-3): ESTABLISH POSITIONING IN VERTICAL
- Target: Project managers at SaaS companies (50-200 people)
- Message: "Real-time, simple, built for teams like yours"
- Tactics:
  * LinkedIn: "Why we built TaskFlow (and why Asana failed us)"
  * Content: "Asana vs. TaskFlow comparison" (unbiased, honest)
  * Ads: Target Asana + Monday.com users, job titles "project manager" + "operations"
- Goal: Establish 40-50 brand mentions/month in SaaS industry

PHASE 2 (Months 4-6): BUILD PROOF IN SEGMENT
- Case studies: 3-4 from SaaS companies (similar size/stage)
- Thought leadership: "How small teams should think about project management"
- Webinar: "Why we ditched Asana (live demo + Q&A)"
- Goal: 60% message resonance among target audience

PHASE 3 (Months 7-12): SCALE POSITIONING
- Expand to adjacent verticals (consulting, services, tech startups)
- Partner integrations with tools SMBs use (Slack, Zapier, etc.)
- Review programs (capterra, G2, etc.) to build social proof
- Goal: 8% market share in SMB project management segment

---

SUCCESS METRICS:

Awareness:
- Brand mentions in "small team project management": 50+ per month
- "TaskFlow alternative to Asana": 40+ monthly searches (SEO)
- Target audience recognition: 60%+ of SMB project managers know us

Competitive metrics:
- Win rate vs. Asana: 40% → 60% (Year 1)
- Win rate vs. Monday.com: 30% → 50%
- Average deal size when winning: $15k
- Competitive switches (Asana → TaskFlow): 15% of new customers

Market share growth:
- Year 1: 2% market share (100 customers)
- Year 2: 8% market share (400 customers)
- Year 3: 15% market share (750+ customers)

Retention:
- NPS in SMB segment: 60+ (vs. Asana NPS: 45)
- Annual retention: 90%+ (vs. Asana: 85%)
- Expansion revenue: 20% of customers add 2+ teams
""",
            success_metrics=[
                "Win rate vs. competitor: Increase 20%+ YoY",
                "Market share in segment: Grow to 8%+ within 2 years",
                "Message resonance: 60%+ of target audience recalls positioning",
                "Competitive switches: 15%+ of new customers from leading competitor"
            ],
            industry_variations={
                "SaaS": "Speed-to-value, ROI, integration-first",
                "Real Estate": "Market advantage, pricing power, buyer advantages",
                "Services": "Expertise differentiation, service quality, client outcomes"
            },
            best_practices=[
                "Own one specific gap — trying to be everything is positioning suicide",
                "Acknowledge competitor strengths — credibility wins",
                "Show proof with case studies — positioning without proof is just talk",
                "Test positioning with 20+ prospects before going all-in",
                "Update positioning as market evolves (quarterly review minimum)"
            ],
            tags=["positioning", "competitive-strategy", "market-strategy", "differentiation", "brand"]
        )

    @staticmethod
    def get_all_positioning_prompts() -> Dict[str, PositioningPromptTemplate]:
        """Return all 50 positioning prompts indexed by ID."""
        return {
            "positioning_001": PositioningPrompts.value_proposition_builder(),
            "positioning_011": PositioningPrompts.competitive_positioning_strategy(),
        }
