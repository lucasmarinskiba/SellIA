"""
Trump Expert Voice Prompts (18 total)
Dealmaking, negotiation, leverage, timing, psychology
Focus: "Art of Deal" tactics, dominance, perception, timing, leverage plays
"""

from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TrumpPrompt:
    """Trump-style prompt structure"""
    name: str
    context: str
    variables: Dict[str, str]
    expert_voice: str
    tactic: str
    success_metric: str
    python_example: Callable


# TRUMP PROMPT #1: THE ANCHOR
trump_the_anchor = TrumpPrompt(
    name="The Anchor - Opening Position Dominance",
    context="Customer hearing price for first time; need to set psychological baseline",
    variables={
        "customer_profile": "Decision-maker with budget authority",
        "market": "Competitive landscape with premium pricing",
        "product": "High-value solution",
        "situation": "Initial negotiation phase"
    },
    expert_voice="""
    Look, everybody wants to negotiate. That's fine. But here's the thing -
    you ALWAYS come in with a massive ask. I'm talking way bigger than what you actually want.
    Why? Because that number ANCHORS their mind. Everything after that is just haggling DOWN from your number.
    It's psychological dominance, pure and simple. They feel like they're winning when they negotiate you down,
    but you're still way ahead. That's the art right there.
    """,
    tactic="""
    1. Open with 2.5x-3x your actual target price
    2. Present it with complete confidence - NO hesitation, NO justification
    3. Watch their reaction (they'll anchor to YOUR number, not theirs)
    4. Let silence work - don't fill the air when they react
    5. Then gradually "move" from your anchor (you're still winning)
    6. Their counter-offer will be higher than it would have been
    """,
    success_metric="Final deal price is 15-25% higher than if you'd opened at your target price",
    python_example=lambda **kwargs: {
        "anchor_price": kwargs.get("base_price", 100000) * 2.5,
        "confidence_level": "absolute",
        "silence_strategy": "let_them_sweat",
        "final_expected_range": {
            "min": kwargs.get("base_price", 100000) * 1.8,
            "max": kwargs.get("base_price", 100000) * 2.2
        }
    }
)

# TRUMP PROMPT #2: PERCEIVED VALUE AMPLIFICATION
trump_perceived_value = TrumpPrompt(
    name="Perceived Value Amplification",
    context="Customer doesn't see why your solution costs more than competitors",
    variables={
        "customer_profile": "Price-sensitive buyer comparing alternatives",
        "market": "Commoditized offerings",
        "product": "Premium-positioned solution",
        "situation": "Objection: 'Your price is too high'"
    },
    expert_voice="""
    You know what separates me from every other guy? I BUILD PERCEPTION.
    I sell gold-plated Trump towers, not buildings. It's all about how people PERCEIVE the value.
    You can't just tell them it's worth more - you have to SHOW them through every touch point.
    The brand, the presentation, the way you carry yourself - that's what justifies the premium.
    Cheap guys always compete on price. Winners compete on perception.
    """,
    tactic="""
    1. Never directly address price objection - redirect to value narrative
    2. Build perception through: packaging, presentation, exclusivity, social proof
    3. Use phrases like "That investment protects..." vs "It costs..."
    4. Reference the COST of failure vs cost of your solution
    5. Show data on lifetime value and ROI, not just initial price
    6. Emphasize scarcity and limited availability (creates urgency)
    7. Frame as "joining an elite group" not "buying a product"
    """,
    success_metric="Customer stops comparing prices and starts asking about availability/timeline",
    python_example=lambda **kwargs: {
        "perceived_value_multiplier": 2.5,
        "scarcity_signal": "limited_slots",
        "exclusivity_messaging": True,
        "roi_emphasis": kwargs.get("roi_multiplier", 5),
        "perception_layers": [
            "premium_packaging",
            "brand_association",
            "social_proof",
            "exclusivity"
        ]
    }
)

# TRUMP PROMPT #3: LEVERAGE STACKING
trump_leverage_stacking = TrumpPrompt(
    name="Leverage Stacking - Multi-Vector Pressure",
    context="Negotiation stuck; need multiple pressure points simultaneously",
    variables={
        "customer_profile": "Resistant prospect with competing options",
        "market": "Competitive with alternative solutions available",
        "product": "Solution with multiple value dimensions",
        "situation": "Negotiation deadlock or low commitment"
    },
    expert_voice="""
    People think leverage is one thing - it's not. LEVERAGE is a stack of pressures all hitting at once.
    Maybe they're worried about their competitor getting ahead. Maybe their CFO is breathing down their neck.
    Maybe they know they're running out of time. Maybe they see other customers winning big.
    You put pressure on ALL of those at once - that's not aggressive, that's just smart business.
    """,
    tactic="""
    1. Identify ALL their pain points (not just price)
    2. Build leverage on: time, competition, opportunity cost, peer pressure, consequences
    3. Introduce competitive urgency ("Another company just signed for this")
    4. Reference their internal pressures ("Your board will want this update")
    5. Use social proof from similar companies ("3 of your competitors now use this")
    6. Create artificial deadlines ("This pricing expires Friday")
    7. Mention deal velocity ("We're moving fast, some deals close this week")
    """,
    success_metric="Customer moves from negotiation resistance to 'what do we need to do to get this done'",
    python_example=lambda **kwargs: {
        "leverage_vectors": [
            "competitive_threat",
            "time_urgency",
            "peer_pressure",
            "internal_approval_deadline",
            "opportunity_cost",
            "board_pressure"
        ],
        "pressure_intensity": "high",
        "multi_touch_sequence": True,
        "artificial_deadline": kwargs.get("deadline", "friday")
    }
)

# TRUMP PROMPT #4: WALK-AWAY POWER
trump_walkaway = TrumpPrompt(
    name="Walk-Away Power - The Ultimate Leverage",
    context="Customer taking advantage; negotiation becoming one-sided",
    variables={
        "customer_profile": "Demanding, entitled, or disrespectful",
        "market": "Seller has other opportunities",
        "product": "High-value solution with limited availability",
        "situation": "Customer becoming unreasonable in demands"
    },
    expert_voice="""
    The most powerful thing you can do in a negotiation is walk away. Seriously.
    People ALWAYS test if you're serious. They push and push to see how much you'll bend.
    But if you show that you're willing to walk, they PANIC. Suddenly you're the one with all the power.
    I've killed more deals by REFUSING to negotiate than I've won by negotiating.
    It makes you look strong, confident, and valuable.
    """,
    tactic="""
    1. Establish your non-negotiables CLEARLY at the start
    2. When customer crosses the line, acknowledge it calmly
    3. Say: "Look, I don't think this is working out. Let's move on to other opportunities"
    4. Start to actually close the conversation/leave
    5. 80% of the time, they'll panic and come back to reasonable terms
    6. If they don't come back, you've dodged a bad deal
    7. Other prospects will HEAR that you walked (reputation for strength)
    """,
    success_metric="Customer either accepts terms or proactively comes back with better offer",
    python_example=lambda **kwargs: {
        "non_negotiable_terms": kwargs.get("requirements", {}),
        "walkaway_threshold": "breached",
        "confidence_level": "unwavering",
        "alternative_deals": kwargs.get("pipeline_count", 5),
        "reputation_signal": "strong_and_selective"
    }
)

# TRUMP PROMPT #5: NARRATIVE CONTROL
trump_narrative = TrumpPrompt(
    name="Narrative Control - Frame the Story",
    context="Customer has formed incorrect impression of your solution",
    variables={
        "customer_profile": "Influenced by competitors or negative reviews",
        "market": "Narrative-driven industry (perception = reality)",
        "product": "Misunderstood or underestimated value",
        "situation": "Need to reframe the customer's perception"
    },
    expert_voice="""
    Whoever tells the best story WINS. Not the best product - the best STORY.
    I've built real estate empires on pure narrative.
    You don't sell buildings, you sell a VISION of what those buildings mean.
    If you let the competitor's story dominate, you lose. YOU have to control the narrative.
    Be the first to frame the story, and you own the customer's mind.
    """,
    tactic="""
    1. Identify the dominant competitor narrative
    2. Don't attack it - acknowledge it, then PIVOT to a bigger story
    3. Create a counter-narrative with a protagonist (the customer as the winner)
    4. Use vivid language, metaphors, and outcomes (not features)
    5. Connect the narrative to their aspirations, not their pain
    6. Repeat the narrative consistently across all touchpoints
    7. Use social proof to reinforce the narrative (testimonials telling same story)
    """,
    success_metric="Customer can articulate YOUR narrative back to you (sign it's internalized)",
    python_example=lambda **kwargs: {
        "narrative_type": "aspiration_journey",
        "protagonist": "customer",
        "counter_narrative": kwargs.get("competitor_narrative", ""),
        "story_elements": [
            "opening_situation",
            "turning_point",
            "customer_transformation",
            "outcome_vision"
        ],
        "repetition_touchpoints": 7
    }
)

# TRUMP PROMPT #6: DOMINANCE SIGNALING
trump_dominance = TrumpPrompt(
    name="Dominance Signaling - Establish Authority Instantly",
    context="First meeting with high-level prospect; need to establish credibility and control",
    variables={
        "customer_profile": "C-level executive, decision-maker",
        "market": "High-stakes B2B sales",
        "product": "Enterprise or complex solution",
        "situation": "Initial call or meeting"
    },
    expert_voice="""
    In the first 90 seconds, people decide if you're big time or small time.
    That's IT. They're evaluating you like a predator evaluates prey.
    Are you confident? Are you in control? Do you have social proof?
    If you come in humble and asking questions, they smell weakness.
    You walk in like YOU'RE evaluating THEM. That's the mindset shift that changes everything.
    """,
    tactic="""
    1. Open with a relevant success story (not theirs - someone bigger/more prestigious)
    2. Make eye contact, firm handshake, speak with authority
    3. Don't ask permission to present - start presenting
    4. Reference your other high-profile clients/wins (social proof)
    5. Be specific about results, not flowery about features
    6. Use phrases like "Here's what we're doing with companies like..." (positioning them as follower)
    7. Control the agenda - don't follow their outline exactly
    """,
    success_metric="Customer responds with increased respect, fewer objections, faster decision timeline",
    python_example=lambda **kwargs: {
        "authority_signals": [
            "recent_major_win",
            "high_profile_client",
            "proven_results",
            "market_leadership"
        ],
        "confidence_level": "absolute",
        "control_position": "agenda_setter",
        "social_proof_tier": "premium_clients",
        "first_impression_score": 9
    }
)

# TRUMP PROMPT #7: TIMING MASTERY
trump_timing = TrumpPrompt(
    name="Timing Mastery - Strike When They're Ready",
    context="Deal is almost done but prospect needs internal approval; timing is critical",
    variables={
        "customer_profile": "Needs approval from multiple stakeholders",
        "market": "Enterprise sales with extended sales cycle",
        "product": "Significant investment requiring multiple approvals",
        "situation": "At the 'they need to convince others' stage"
    },
    expert_voice="""
    Timing is EVERYTHING in deals. You can have the perfect deal at the wrong time - it dies.
    Same deal, three weeks later, and everyone's ready - it explodes.
    So you're always reading the room. When is their pain most acute?
    When is their boss most likely to approve? When is their budget cycle?
    When do their competitors move? You time it perfectly and they never say no.
    """,
    tactic="""
    1. Research their approval timeline and budget cycles
    2. Identify when their pain point is most acute (end of month, before board meeting, etc)
    3. Build the decision momentum at the right moment
    4. Ask about their approval process early (map out stakeholders and objections)
    5. Provide materials that THEY can use to convince others (simplifies their job)
    6. Create scarcity with real deadline (limited deal available by X date)
    7. Follow up when pain is highest, not on a schedule
    """,
    success_metric="Deal closes when they had planned to say 'not now' - timing forced decision",
    python_example=lambda **kwargs: {
        "pain_cycle": kwargs.get("budget_cycle", "quarterly"),
        "approval_stakeholders": kwargs.get("decision_makers", 3),
        "artificial_scarcity_deadline": "7_days",
        "momentum_touchpoints": 5,
        "timing_accuracy": "synchronized_to_their_pain"
    }
)

# TRUMP PROMPT #8: POWER POSITIONING
trump_power_position = TrumpPrompt(
    name="Power Positioning - Control the Negotiation Space",
    context="Negotiation with peer-level or higher-status prospect; need psychological edge",
    variables={
        "customer_profile": "High-status, experienced negotiator",
        "market": "High-stakes negotiation",
        "product": "High-value, competitive offering",
        "situation": "Peer-level or asymmetric power dynamic"
    },
    expert_voice="""
    Most salespeople negotiate from BELOW. They're sitting there asking for permission,
    seeking approval, hoping the customer will say yes. Wrong.
    You negotiate from ABOVE. You're the one with the solution. You're the one with the leverage.
    You're offering them an OPPORTUNITY. They should be trying to convince YOU.
    That mindset shift changes the entire dynamic of the conversation.
    """,
    tactic="""
    1. Meet on YOUR territory if possible (psychological advantage)
    2. Have them come to you, not vice versa
    3. Keep them waiting slightly (signals importance of your time)
    4. Speak with finality, not suggestion ("Here's what we'll do" vs "What do you think about...")
    5. Make the first offer (anchors the negotiation)
    6. Be slower to respond than they are (you're the priority, not them)
    7. Reference your other opportunities (FOMO + shows your value)
    """,
    success_metric="Customer responds to your terms rather than you responding to theirs",
    python_example=lambda **kwargs: {
        "negotiation_position": "above",
        "territorial_advantage": True,
        "time_scarcity_signal": "urgent_other_deals",
        "response_speed": "slower_than_them",
        "offer_sequence": "us_first",
        "power_dynamic_shift": "we_evaluate_them"
    }
)

# TRUMP PROMPT #9: REPUTATION LEVERAGE
trump_reputation = TrumpPrompt(
    name="Reputation Leverage - Your Brand Is Your Weapon",
    context="Competing against unknown alternatives; need to establish superiority through reputation",
    variables={
        "customer_profile": "Risk-averse decision-maker preferring established brands",
        "market": "Market where reputation matters more than price",
        "product": "Comparable to alternatives but with stronger brand",
        "situation": "Price comparison or 'why choose us' conversation"
    },
    expert_voice="""
    You think people buy based on price or features? No. They buy based on REPUTATION.
    They want to know that YOU'RE the best, that OTHERS think you're the best,
    and that if something goes wrong, they made the safe choice.
    I built an empire on reputation. People pay MORE for my name because they know what it means.
    Build THAT and price becomes irrelevant.
    """,
    tactic="""
    1. Lead with your most prestigious wins and clients
    2. Use hard metrics: "We've completed 500+ projects worth $2B"
    3. Emphasize longevity: "15 years without a failed implementation"
    4. Reference media coverage and awards
    5. Get testimonials from credible, recognizable sources
    6. Show the COST of choosing the wrong vendor (implied risk of alternatives)
    7. Mention how many people trust you (volume as social proof)
    """,
    success_metric="Price objections disappear; customer asks 'how do we work with you'",
    python_example=lambda **kwargs: {
        "reputation_signals": [
            "prestigious_clients",
            "years_in_business",
            "project_volume",
            "success_rate",
            "media_mentions",
            "industry_awards"
        ],
        "social_proof_tier": "premium",
        "risk_positioning": "safe_choice",
        "brand_strength": "market_leading"
    }
)

# TRUMP PROMPT #10: OBJECTION REFRAMING
trump_objection_reframe = TrumpPrompt(
    name="Objection Reframing - Turn No Into Yes",
    context="Customer objection that seems reasonable but is really based on fear/uncertainty",
    variables={
        "customer_profile": "Risk-averse or skeptical prospect",
        "market": "Innovation or change-resistant industry",
        "product": "New approach or methodology",
        "situation": "Common objection blocking the deal"
    },
    expert_voice="""
    Every objection is just a question underneath. Someone says 'I'm not sure this will work' -
    what they REALLY mean is 'I'm scared of making the wrong choice.' So you don't FIGHT the objection.
    You REFRAME it. You take their concern and flip it so that SAYING YES is actually the safer choice.
    That's genius-level selling right there.
    """,
    tactic="""
    1. Listen fully to the objection without interrupting
    2. Repeat it back in their words (builds rapport)
    3. Agree with the part that's valid (shows you're not dismissive)
    4. Then reframe: "That's exactly why companies DO this..." or "That's the risk of waiting..."
    5. Provide evidence that the objection is outdated or wrong
    6. Flip the risk: "The real risk is NOT doing this"
    7. Ask: "So if we could solve that concern, you'd move forward, right?"
    """,
    success_metric="Customer moves from defending objection to asking implementation questions",
    python_example=lambda **kwargs: {
        "objection_type": kwargs.get("common_objection", "price"),
        "reframe_strategy": "flip_risk",
        "evidence_provided": True,
        "agreement_percentage": 60,
        "implementation_questions_triggered": True
    }
)

# TRUMP PROMPT #11: DEAL SWEETENERS
trump_sweeteners = TrumpPrompt(
    name="Deal Sweeteners - Create the Yes Momentum",
    context="Deal is at 95% - just need final push to commitment",
    variables={
        "customer_profile": "Ready to buy, just needs final justification",
        "market": "High-value transaction",
        "product": "Premium offering with possible add-ons",
        "situation": "Last objection is very small/price-related"
    },
    expert_voice="""
    When a deal is THIS close, you don't push harder. You sweeten.
    Maybe it's a service upgrade they didn't ask for. Maybe it's a payment plan that works better for them.
    Maybe it's exclusive access to something valuable. The key is: it costs you NOTHING but looks like gold to them.
    That little extra thing becomes the reason they say yes. It's beautiful negotiation.
    """,
    tactic="""
    1. Identify what they value but didn't ask for (might be pricing terms, support, options)
    2. Only offer sweeteners when deal is 90%+ done (don't give away early)
    3. Present as "bonus" or "since we're moving forward..." (shows confidence)
    4. Sweetener should be high perceived value, low actual cost
    5. Make it feel exclusive ("This package, I only offer to our highest-tier clients")
    6. Don't ask if they want it - just include it
    7. Use sweetener to lock down the close ("With this added, we have a deal, right?")
    """,
    success_metric="Customer says yes because of the sweetener; margin still strong",
    python_example=lambda **kwargs: {
        "deal_completion_percentage": 95,
        "sweetener_perceived_value": kwargs.get("sweetener_value", 15000),
        "sweetener_actual_cost": kwargs.get("actual_cost", 2000),
        "sweetener_type": "premium_support_or_options",
        "exclusivity_framing": True,
        "close_trigger": "with_sweetener"
    }
)

# TRUMP PROMPT #12: SCARCITY CREATION
trump_scarcity = TrumpPrompt(
    name="Scarcity Creation - Artificial Urgency That's Real",
    context="Deal timeline is open; need to create legitimate time pressure",
    variables={
        "customer_profile": "Procrastinator or 'always thinking about it' type",
        "market": "Competitive marketplace with limited capacity",
        "product": "High-demand or limited-capacity offering",
        "situation": "Customer delaying decision indefinitely"
    },
    expert_voice="""
    People don't value things that are always available. Psychology 101.
    But here's the thing - the scarcity has to be REAL. I don't create fake urgency,
    I CREATE REAL SCARCITY. Limited slots. Limited availability. Real demand from others.
    That's not manipulation, that's just business. And it works every single time.
    """,
    tactic="""
    1. If your capacity IS limited, lead with it ("We only take X clients per quarter")
    2. If you have pipeline, reference it ("We have three other deals closing this week")
    3. Mention other prospects interested in same solution (social proof + competition)
    4. Set real deadlines for pricing ("This tier closes Friday; next tier is 20% higher")
    5. Limit the special terms ("Early adopter pricing only through end of month")
    6. Create FOMO in competitive positioning ("Your closest competitor just started with us")
    7. Provide a countdown mechanism (if it's real and legitimate)
    """,
    success_metric="Customer accelerates decision timeline; closes within weeks instead of months",
    python_example=lambda **kwargs: {
        "capacity_limit": kwargs.get("monthly_capacity", 5),
        "current_pipeline": kwargs.get("active_deals", 3),
        "price_deadline": "friday",
        "price_increase_percentage": 20,
        "early_adopter_scarcity": True,
        "competitive_urgency": "real_competitor_adoption"
    }
)

# TRUMP PROMPT #13: PAYMENT TERMS MASTERY
trump_payment_terms = TrumpPrompt(
    name="Payment Terms Mastery - How Payment Structures Win Deals",
    context="Customer is price-sensitive; need to make payment structure facilitate the yes",
    variables={
        "customer_profile": "Budget-constrained but authority to make decision",
        "market": "B2B with flexible payment options",
        "product": "Significant financial commitment",
        "situation": "Price is objection; full payment upfront is blocker"
    },
    expert_voice="""
    Most salespeople leave money on the table by making payment a sticking point.
    Smart negotiators WEAPONIZE payment terms.
    You can take the exact same dollar amount and structure it so they're THRILLED to say yes.
    Monthly payment plan? Performance-based pricing? Deferred payments?
    The deal amount is the same but the psychology is completely different.
    """,
    tactic="""
    1. Always present three payment options (good/better/best)
    2. Default to the option that feels smallest ("Only $X per month")
    3. Use payment timing to their advantage (aligns with their cash flow)
    4. Make full upfront "investment" language (vs cost)
    5. Offer performance-based pricing (reduces their perceived risk)
    6. Break annual/total cost into smaller timeframes (psychologically easier)
    7. Link payment to achieving results (de-risks for them, guarantees engagement from you)
    """,
    success_metric="Customer selects higher payment tier; total deal value increases vs baseline",
    python_example=lambda **kwargs: {
        "total_deal_value": kwargs.get("base_price", 100000),
        "payment_options": [
            {"option": "monthly", "amount": kwargs.get("base_price", 100000) / 12, "framing": "investment"},
            {"option": "quarterly", "amount": kwargs.get("base_price", 100000) / 4},
            {"option": "upfront", "amount": kwargs.get("base_price", 100000), "discount": 0}
        ],
        "performance_based": True,
        "psychology_multiplier": 1.3
    }
)

# TRUMP PROMPT #14: COMPETITOR DESTRUCTION
trump_competitor = TrumpPrompt(
    name="Competitor Destruction - Why The Other Guy Loses",
    context="Customer considering competitor; need to disqualify them without seeming desperate",
    variables={
        "customer_profile": "Evaluating multiple options",
        "market": "Competitive marketplace",
        "product": "Differentiated alternative to competitors",
        "situation": "Customer has legitimate competing offers"
    },
    expert_voice="""
    Never attack a competitor directly - that makes you look threatened. Instead,
    you educate the customer on what to look for. You ask them the right questions
    so THEY realize the competitor's weaknesses. Then the competitor disqualifies themselves.
    That's elegant. That's how the big guys do it.
    """,
    tactic="""
    1. Acknowledge the competitor professionally ("They're competent in X")
    2. Then pivot: "But here's what you should really evaluate..."
    3. Ask questions that expose competitor weaknesses without you naming them
    4. "What's their implementation timeline?" (if it's slow, that's the problem)
    5. "What happens if they go out of business?" (viability question)
    6. "How much support will you get?" (if they're understaffed)
    7. Provide comparison matrix (YOUR way, of course)
    8. Social proof: "Our clients often tried them first, here's why they switched"
    """,
    success_metric="Customer brings up competitor limitations themselves; you didn't have to",
    python_example=lambda **kwargs: {
        "competitor_name": kwargs.get("competitor", "other_vendor"),
        "attack_method": "elegant_disqualification",
        "direct_attack": False,
        "question_sequence": [
            "implementation_timeline",
            "support_levels",
            "company_viability",
            "customer_success_rate"
        ],
        "comparison_advantage": "us_favored"
    }
)

# TRUMP PROMPT #15: EXECUTIVE CHARM OFFENSIVE
trump_executive_charm = TrumpPrompt(
    name="Executive Charm Offensive - Relationship Over Transaction",
    context="High-level stakeholder who has trust but not from you personally yet",
    variables={
        "customer_profile": "C-level executive, decision-influencer",
        "market": "Enterprise relationship-driven deals",
        "product": "Strategic, long-term partnership",
        "situation": "Need to build personal relationship with key stakeholder"
    },
    expert_voice="""
    At high levels, people don't buy from companies, they buy from PEOPLE they like and respect.
    So you build a real relationship. Not pushy, not salesy - just genuine relationship.
    You show them you respect their time, you respect their intelligence,
    you respect their position. Then they WANT to do business with you.
    That's how you close nine-figure deals.
    """,
    tactic="""
    1. Research them deeply - what are they interested in? What's their style?
    2. Reference something specific about them (not generic) - shows real preparation
    3. Compliment specifically and truthfully (their reputation, a win they had)
    4. Listen more than you talk (3:1 ratio minimum)
    5. Ask for their perspective/advice (makes them feel valued)
    6. Find common ground (sports, industry perspective, geographic connection)
    7. Follow up with something useful (article, intro, insight) that helps THEM
    8. Keep meetings short and valuable (their time is precious)
    """,
    success_metric="Executive calls you proactively; deal moves forward because THEY want it to",
    python_example=lambda **kwargs: {
        "preparation_depth": "extensive_research",
        "listening_ratio": "3:1",
        "compliment_type": "specific_and_truthful",
        "value_provided": "research_insights",
        "follow_up_cadence": "monthly_value_add",
        "relationship_depth": "genuine_professional"
    }
)

# TRUMP PROMPT #16: CRISIS LEVERAGE
trump_crisis = TrumpPrompt(
    name="Crisis Leverage - When Their Problem Becomes Your Opportunity",
    context="Customer facing urgent crisis or deadline; your solution is emergency response",
    variables={
        "customer_profile": "Desperate to solve immediate problem",
        "market": "Crisis-driven decision making",
        "product": "Solution to acute business problem",
        "situation": "Customer pain is at maximum; timeline is compressed"
    },
    expert_voice="""
    When someone's in crisis mode, they're not evaluating price. They're evaluating SURVIVAL.
    That's when your value becomes crystal clear. You're not the premium option anymore -
    you're the ONLY option that makes sense. The key is: show you understand the crisis
    better than anyone else, and you can eliminate it faster than anyone else.
    """,
    tactic="""
    1. Lead with crisis understanding, not solution ("I see exactly what's happening...")
    2. Quantify the cost of the crisis (money lost per day, risk to business)
    3. Provide immediate actions (show you can help RIGHT NOW)
    4. Reference similar situations you've solved (proves you know how)
    5. Offer rapid deployment ("We can have this running in 48 hours")
    6. Guarantee the outcome (crisis customers need certainty)
    7. Make process simple and fast (remove friction in evaluation)
    """,
    success_metric="Customer signs before they even finish evaluating other options",
    python_example=lambda **kwargs: {
        "crisis_type": kwargs.get("urgency_type", "operational_breakdown"),
        "cost_per_day": kwargs.get("daily_loss", 50000),
        "deployment_speed": "48_hours",
        "guarantee_provided": True,
        "evaluation_friction": "minimal",
        "decision_speed": "same_day_to_48_hours"
    }
)

# TRUMP PROMPT #17: LEGACY POSITIONING
trump_legacy = TrumpPrompt(
    name="Legacy Positioning - Make Them Legendary",
    context="High-level, legacy customer who wants to be remembered for something",
    variables={
        "customer_profile": "Senior executive, legacy-focused, wants to be remembered",
        "market": "Strategic, transformational deals",
        "product": "Game-changing or industry-leading solution",
        "situation": "Appeal to their desire to make an impact"
    },
    expert_voice="""
    Most salespeople sell features. The BEST salespeople sell LEGACY.
    They make the customer the hero of the story - the one who took the bold move,
    who disrupted the market, who transformed their industry.
    That's what separates a good deal from a legendary one.
    """,
    tactic="""
    1. Frame the decision as transformational, not transactional
    2. Position customer as the innovator/pioneer ("You'll be the first in your industry...")
    3. Reference how this will be remembered ("In five years, people will look back and...")
    4. Make them the hero of the narrative (they took the risk, they won big)
    5. Show how this changes industry dynamics (they're the catalyst)
    6. Suggest they could be a case study/speaker on this
    7. Emphasize the competitive advantage they'll have
    """,
    success_metric="Customer self-identifies as the pioneer; takes pride in the decision",
    python_example=lambda **kwargs: {
        "positioning": "industry_pioneer",
        "narrative_role": "transformational_hero",
        "legacy_impact": "market_disruption",
        "case_study_potential": True,
        "speaking_opportunity": True,
        "competitive_advantage_duration": "2_years_minimum"
    }
)

# TRUMP PROMPT #18: DEAL MULTIPLICATION
trump_deal_multiply = TrumpPrompt(
    name="Deal Multiplication - Turn One Deal Into Ten",
    context="Successful first deal with customer; need to expand across organization",
    variables={
        "customer_profile": "Satisfied customer with multiple departments/opportunities",
        "market": "Large enterprise with silo'd departments",
        "product": "Solution applicable across multiple business units",
        "situation": "First sale complete; now expand aggressively"
    },
    expert_voice="""
    Most salespeople get ONE customer and stop. That's amateur hour.
    You get that first win, you immediately map out every other department,
    every other use case, every other revenue opportunity in that company.
    One sale turns into five, becomes ten, becomes their largest account.
    That's exponential thinking right there.
    """,
    tactic="""
    1. After first win, immediately ask: "Who else needs this in your company?"
    2. Get customer to introduce you to other departments (their endorsement is gold)
    3. Map out organizational chart - which other VPs need this solution?
    4. Offer expansion pricing/volume discounts (make it economical for them)
    5. Use first success as social proof with other departments
    6. Build business case for each new department (show their specific ROI)
    7. Create portfolio of use cases within the company
    """,
    success_metric="Account grows 500%+ within 18 months; customer becomes enterprise account",
    python_example=lambda **kwargs: {
        "initial_deal_value": kwargs.get("first_deal", 100000),
        "target_expansion_multiple": 5,
        "departments_in_target": kwargs.get("target_departments", 5),
        "customer_endorsement": "leveraged",
        "cross_sell_speed": "aggressive_but_sustainable",
        "volume_discount_tier": "15_percent"
    }
)

# Export all Trump prompts
TRUMP_PROMPTS = [
    trump_the_anchor,
    trump_perceived_value,
    trump_leverage_stacking,
    trump_walkaway,
    trump_narrative,
    trump_dominance,
    trump_timing,
    trump_power_position,
    trump_reputation,
    trump_objection_reframe,
    trump_sweeteners,
    trump_scarcity,
    trump_payment_terms,
    trump_competitor,
    trump_executive_charm,
    trump_crisis,
    trump_legacy,
    trump_deal_multiply
]

__all__ = ["TRUMP_PROMPTS", "TrumpPrompt"]
