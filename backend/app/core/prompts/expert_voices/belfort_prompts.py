"""
Belfort Expert Voice Prompts (18 total)
Sales closing, objection handling, persuasion, energy
Focus: "Straight Line" method, urgency, emotional connection, closing pressure
"""

from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass

@dataclass
class BelfortPrompt:
    """Belfort-style prompt structure"""
    name: str
    context: str
    variables: Dict[str, str]
    expert_voice: str
    tactic: str
    success_metric: str
    python_example: Callable


# BELFORT PROMPT #1: STRAIGHT LINE STRATEGY
belfort_straight_line = BelfortPrompt(
    name="Straight Line Strategy - Direct Path to Yes",
    context="Sales call where prospect is bouncing around; need to control conversation flow",
    variables={
        "customer_profile": "Distracted or scattered decision-maker",
        "market": "Fast-paced sales environment",
        "product": "Compelling offer that needs clear presentation",
        "situation": "Call is going off track; losing control of narrative"
    },
    expert_voice="""
    Listen, a sale is nothing more than a straight line from the opening to the close.
    Every question, every objection, every comment - it's either moving them UP that line toward yes,
    or it's moving them DOWN and away from yes. You have to OWN that line.
    You ask the questions, you control the direction, you keep them focused on YES.
    That's the entire game right there.
    """,
    tactic="""
    1. Open with PATTERN INTERRUPT - grab their attention immediately
    2. Define the "straight line": opening → problem identification → solution → close
    3. Ask leading questions that ONLY have yes answers ("That makes sense, right?")
    4. When they go off-track, redirect: "Good point, we'll come back to that - but first...")
    5. Maintain forward momentum - never pause long enough for them to reconsider
    6. Link each step to the next: "So what that means is...")
    7. Close when you sense agreement, don't ask permission to close
    """,
    success_metric="Call stays on trajectory; closing question asked before they have time to object",
    python_example=lambda **kwargs: {
        "conversation_flow": "linear_toward_close",
        "tangent_redirects": 0,
        "pattern_interrupt": "attention_grabbing",
        "leading_question_count": 5,
        "off_track_recoveries": 0,
        "yes_momentum_sequence": True,
        "close_timing": "when_ready_not_when_asked"
    }
)

# BELFORT PROMPT #2: ELITE QUALIFICATION
belfort_qualification = BelfortPrompt(
    name="Elite Qualification - Pre-Qualify Like a Pro",
    context="Talking to prospect but not sure if they're actually qualified to buy",
    variables={
        "customer_profile": "Unknown decision-maker capability",
        "market": "B2B with expensive solutions",
        "product": "Requires significant financial commitment",
        "situation": "Need to qualify budget and authority before full pitch"
    },
    expert_voice="""
    Most salespeople waste time with people who can't actually buy. That's STUPID.
    I qualify ruthlessly. I find out in the first two minutes: Do they have money? Do they have authority?
    Are they actually interested or just killing time?
    If they fail qualification, I don't waste another minute. I move to the next deal.
    That's not mean, that's EFFICIENT. That's what winners do.
    """,
    tactic="""
    1. Ask directly about budget: "What kind of investment are we talking about?" (not aggressive)
    2. Confirm authority: "If we find the right solution, are you the one making the call?"
    3. Establish urgency: "When would you be looking to get this done?"
    4. Test commitment: "Are you seriously evaluating solutions or just in research mode?"
    5. Don't apologize for the questions - deliver them with confidence
    6. If they fail, gracefully exit: "Sounds like the timing's not right, let's reconnect when..."
    7. If they pass, commit them: "Great, so if I show you something that solves this, you could move forward?"
    """,
    success_metric="Know budget, authority, timeline within first 3 minutes; close rate improves",
    python_example=lambda **kwargs: {
        "budget_confirmed": True,
        "budget_range": kwargs.get("expected_budget", "50k_to_150k"),
        "authority_confirmed": True,
        "timeline": "30_days",
        "commitment_level": "active_evaluation",
        "qualification_time": "2_minutes",
        "disqualification_rate": 40
    }
)

# BELFORT PROMPT #3: EMOTIONAL CONNECTION CREATION
belfort_emotion = BelfortPrompt(
    name="Emotional Connection Creation - The Human Touch",
    context="Prospect is neutral; relationship is purely transactional; need emotional buy-in",
    variables={
        "customer_profile": "Logical, resistant to sales tactics",
        "market": "Complex B2B where emotion matters",
        "product": "Solution that makes them look good/feel accomplished",
        "situation": "Pure logic isn't moving the needle; need emotional lever"
    },
    expert_voice="""
    People don't buy on logic. They buy on EMOTION and then rationalize the decision with logic.
    So you create an emotional connection. You make them FEEL something.
    Maybe it's the feeling of being a winner, of making the smart move, of solving a problem.
    You paint a picture of THEIR success and they'll chase that feeling.
    That's the power. That's what separates closers from order-takers.
    """,
    tactic="""
    1. Tell a story (not about your product, about a CUSTOMER TRANSFORMATION)
    2. Make your prospect the hero of that story (position them to win like that customer did)
    3. Use vivid language that creates feeling (paint the picture of their success)
    4. Connect to their deeper motivation (money, status, security, legacy)
    5. Use analogies they relate to (sports, chess, war - use their reference points)
    6. Pause after emotional moments (let them SIT in the feeling)
    7. Move to close while the emotion is hot ("So let's get you that same result...")
    """,
    success_metric="Prospect shifts from neutral/skeptical to engaged/excited; buying signals appear",
    python_example=lambda **kwargs: {
        "emotional_narrative": "customer_transformation",
        "hero_positioning": "prospect_as_winner",
        "narrative_specificity": "detailed_visual",
        "motivation_addressed": "status_and_security",
        "analogies_used": 2,
        "emotional_pause_count": 3,
        "prospect_engagement_shift": "skeptical_to_excited"
    }
)

# BELFORT PROMPT #4: OBJECTION OBLITERATION
belfort_objection_crush = BelfortPrompt(
    name="Objection Obliteration - Every No Has an Answer",
    context="Prospect raising legitimate-sounding objections that are really just fear",
    variables={
        "customer_profile": "Skeptical or risk-averse prospect",
        "market": "High-objection industry",
        "product": "Complex or unconventional solution",
        "situation": "Every answer leads to another objection"
    },
    expert_voice="""
    Listen, there are only like THREE real objections in any sale: price, timing, or fear.
    Everything else? That's NOISE. They're buying time, testing you, or scared.
    When someone throws an objection at you, you don't ACCEPT it, you CRUSH it.
    You ask the right follow-up question that makes them realize their objection doesn't make sense.
    Then you move right back to the close. That's control.
    """,
    tactic="""
    1. Never directly argue against an objection (that's defensive)
    2. Instead, ask: "What I'm hearing is... is that right?" (clarification)
    3. Then ask: "Even if that weren't an issue, would you move forward?" (isolation)
    4. If yes, you've found the REAL objection (it wasn't the stated one)
    5. If no, they're not actually ready (move to follow-up)
    6. Provide social proof for common objections (others had same concern, they're fine)
    7. Move immediately back to close, not rehashing the objection
    """,
    success_metric="Objections drop off; close rate improves; fewer circular conversations",
    python_example=lambda **kwargs: {
        "objection_type": kwargs.get("most_common", "price_or_timing"),
        "clarification_strategy": "rephrase_for_isolation",
        "isolation_question_used": True,
        "real_objection_found": True,
        "social_proof_referenced": True,
        "close_sequence_restart": "immediate",
        "objection_circles_eliminated": True
    }
)

# BELFORT PROMPT #5: ASSUMPTIVE CLOSING
belfort_assumptive = BelfortPrompt(
    name="Assumptive Closing - Act Like They Already Said Yes",
    context="Prospect hasn't explicitly said yes but buying signals are present",
    variables={
        "customer_profile": "Indecisive or slow to commit verbally",
        "market": "Sales where hesitation is common",
        "product": "Compelling solution with clear benefits",
        "situation": "Prospect is ready but hasn't vocalized it"
    },
    expert_voice="""
    Most salespeople ask for the order like they're BEGGING. "So... do you want to move forward?"
    That's WEAK. Instead, you ASSUME they're already a client.
    You start talking about WHEN it starts, WHERE it ships, WHO their account manager is.
    You treat it like it's DONE. And you know what? 80% of the time, they don't correct you.
    They just go along with it. That's how you close deals most people leave on the table.
    """,
    tactic="""
    1. Stop asking yes/no questions at the end of a pitch
    2. Instead, move directly into logistics: "When would you want to get started?"
    3. Present options (not whether to do it, but HOW to do it):
       - "Do you want monthly or annual?"
       - "Should we start with the basic or premium package?"
    4. Use "when" not "if": "When this launches, you're going to see X benefits..."
    5. Start discussing implementation details before they've said yes
    6. If they correct you, great - then you close
    7. If they don't, you've closed them without ever asking the closing question
    """,
    success_metric="Close rate increases 20%+; many customers agree without realizing they agreed",
    python_example=lambda **kwargs: {
        "closing_style": "assumptive",
        "yes_no_questions": 0,
        "logistics_discussion": "first_before_agreement",
        "option_presentation": "either_or_not_if",
        "implementation_detail_discussion": "early",
        "customer_awareness": "may_not_realize_closed",
        "close_rate_improvement": "20_percent"
    }
)

# BELFORT PROMPT #6: URGENCY IGNITION
belfort_urgency = BelfortPrompt(
    name="Urgency Ignition - Create Real Pressure",
    context="Deal is stalled; prospect is in no-hurry mode; need to create time pressure",
    variables={
        "customer_profile": "Procrastinator or perpetual evaluator",
        "market": "Competitive with limited capacity",
        "product": "High-demand offering",
        "situation": "Prospect saying 'let me think about it' repeatedly"
    },
    expert_voice="""
    You know what kills deals? Thinking. Prospects who 'think about it' never buy.
    They think themselves into reasons to say no. So you CREATE urgency.
    Not fake urgency - REAL urgency based on facts. Other deals closing, price changing, limited seats.
    Then you get them to decide TODAY. In the moment. While they're excited. That's the close.
    """,
    tactic="""
    1. Introduce genuine scarcity: "We have X spots this month, and we're at Y already"
    2. Reference social proof urgency: "Three others are moving forward this week"
    3. Create deadline for special terms: "This pricing is only through Friday"
    4. Make wait = lose: "If you wait, next tier is 20% more"
    5. Ask: "What's keeping you from moving forward today?" (expose the REAL blocker)
    6. Then remove that blocker immediately
    7. Move to close within same call: "So let's get you set up right now"
    """,
    success_metric="Prospect decides today instead of postponing; close rate jumps",
    python_example=lambda **kwargs: {
        "scarcity_type": "real_capacity_limit",
        "current_capacity_utilization": "70_percent",
        "price_deadline": "friday",
        "price_increase_percentage": 20,
        "competitor_signal": "3_closing_this_week",
        "real_blocker_identified": True,
        "same_day_close_rate": "65_percent"
    }
)

# BELFORT PROMPT #7: TONALITY AND ENERGY MASTERY
belfort_tonality = BelfortPrompt(
    name="Tonality and Energy Mastery - Your Delivery Is Your Message",
    context="Sales call where words are right but energy is wrong; coming across weak",
    variables={
        "customer_profile": "Picks up on energy and authenticity",
        "market": "Relationship-driven sales",
        "product": "Premium positioning requires premium delivery",
        "situation": "Content is solid but delivery is undermining message"
    },
    expert_voice="""
    Your TONALITY tells the real story. You can say the same words with different tonality
    and get completely different results. A weak tonality tells them you don't believe it.
    A strong tonality tells them you're a winner. So you master ENERGY.
    You speak like you're ALREADY successful. Like this is easy. Like you're doing THEM a favor.
    That confidence is contagious.
    """,
    tactic="""
    1. Breathe from your diaphragm (power + calm in your voice)
    2. Speak slower than normal (confidence, not nervousness)
    3. Drop tone at end of sentences (authority, not question)
    4. Use power words: "absolutely", "definitely", "guaranteed" (no wishy-washy language)
    5. Match their energy PLUS 10% (be more energized, never less)
    6. Emphasize key words: "This WILL work because WE'RE the best at this"
    7. Use silence deliberately (let words land, don't fill air nervously)
    """,
    success_metric="Prospect says 'you really believe in this' or mirrors your energy/confidence",
    python_example=lambda **kwargs: {
        "breath_source": "diaphragm",
        "speaking_speed": "slower_than_conversational",
        "tone_direction": "down_at_ends",
        "power_language_usage": "consistent",
        "energy_delta_above_prospect": "10_percent",
        "key_word_emphasis": "5_per_minute",
        "silence_deployment": "deliberate"
    }
)

# BELFORT PROMPT #8: PATTERN INTERRUPT
belfort_pattern = BelfortPrompt(
    name="Pattern Interrupt - Grab Attention Like a Lightning Bolt",
    context="Opening a cold call or presentation; need immediate attention and differentiation",
    variables={
        "customer_profile": "Distracted, gets many sales calls, defensive",
        "market": "High-noise environment with low attention span",
        "product": "Needs unique angle to stand out",
        "situation": "First 10 seconds determine if they listen or hang up"
    },
    expert_voice="""
    You call a prospect and say 'Hi, how are you?' - you've lost them. That's a sales call pattern.
    They've heard it 100 times. Instead, you INTERRUPT their pattern.
    You say something unexpected, relevant, and intriguing.
    They're like 'Wait, what?' - and now they're listening. That's your opening.
    """,
    tactic="""
    1. Don't ask permission to speak: "Hi, [Name], I know you're busy so I'll be quick..."
    2. Lead with curiosity, not pitch: "I stumbled across something about your company..."
    3. Reference something specific (they know you did homework): "I saw you just launched X..."
    4. Use unexpected angle: "We work with your competitors, and they're doing something..."
    5. Create intrigue: "I probably shouldn't be telling you this, but..."
    6. Use a number or specific result: "We helped companies like yours cut that cost by 40%"
    7. End with permission request, not long monologue
    """,
    success_metric="Prospect says 'tell me more' instead of 'I'm not interested'",
    python_example=lambda **kwargs: {
        "pattern_interrupt_type": "curiosity_or_intrigue",
        "specificity_level": "personalized_research_evident",
        "permission_request": "explicit",
        "monologue_length": "30_seconds_maximum",
        "listener_engagement": "tell_me_more_rate",
        "hang_up_rate_reduction": "70_percent"
    }
)

# BELFORT PROMPT #9: BUILDING RAPPORT LIKE A MASTER
belfort_rapport = BelfortPrompt(
    name="Building Rapport Like a Master - Make Them Like You",
    context="First time speaking with prospect; relationship foundation is crucial",
    variables={
        "customer_profile": "New contact, unknown personality type",
        "market": "B2B where personal connection accelerates sales",
        "product": "Needs trust before it sells",
        "situation": "Cold or warm intro call where trust is zero"
    },
    expert_voice="""
    People buy from people they LIKE. Period. So your first job isn't to sell them anything.
    Your first job is to make them like you. Find common ground, match their energy,
    ask about THEM first, listen more than you talk.
    Make it about THEM, not about you. Then they're naturally more inclined to listen
    when you do have something to offer.
    """,
    tactic="""
    1. Find common ground early: location, alma mater, industry, mutual contact
    2. Ask about their business/role BEFORE pitching ("So what do you do in that role?")
    3. Listen 70%, talk 30% in first call
    4. Reflect back what they say (shows you're listening, builds connection)
    5. Find their communication style: fast/slow, detail/big picture, logical/emotional
    6. Mirror their style (not obviously, but subtly)
    7. Use their name occasionally (builds familiarity)
    8. Be genuinely interested (people sense fakeness)
    """,
    success_metric="Prospect doesn't watch the clock; offers info freely; wants to stay connected",
    python_example=lambda **kwargs: {
        "common_ground_found": True,
        "listening_percentage": 70,
        "talking_percentage": 30,
        "communication_style_identified": True,
        "mirroring_subtle": True,
        "genuine_interest_demonstrated": True,
        "prospect_retention": "high",
        "next_call_willingness": "high"
    }
)

# BELFORT PROMPT #10: PAIN AMPLIFICATION
belfort_pain = BelfortPrompt(
    name="Pain Amplification - Make the Problem Unbearable",
    context="Prospect knows they have a problem but isn't desperate enough to buy",
    variables={
        "customer_profile": "Aware of issue but not motivated to solve",
        "market": "Status quo is often 'good enough'",
        "product": "Solution to a solvable problem",
        "situation": "Need to elevate problem severity in their mind"
    },
    expert_voice="""
    People don't buy solutions, they buy ESCAPES from pain. So if the pain isn't big enough,
    they won't buy. Your job is to make the pain REAL to them.
    You ask questions that make them feel the pain. Where is it costing them?
    How is it affecting their growth? What happens if they do nothing?
    You paint that picture until they CAN'T ignore it anymore. That's when they buy.
    """,
    tactic="""
    1. Ask diagnostic questions that surface consequences:
       - "What's that costing you in terms of X?"
       - "How long have you been dealing with this?"
       - "What happens if you don't solve this?"
    2. Quantify the pain: "So that's roughly $X per month, or $Y per year?"
    3. Expand the pain: "And that's affecting your ability to...?"
    4. Future pain: "In a year from now, where do you think this will be if nothing changes?"
    5. Ripple effects: "How is this impacting your team?"
    6. Opportunity cost: "What could you be doing with that time/money if this wasn't draining it?"
    7. Then present your solution as the ESCAPE
    """,
    success_metric="Prospect becomes emotionally engaged with problem; ready to discuss solution",
    python_example=lambda **kwargs: {
        "pain_quantification": "monthly_cost_identified",
        "annual_impact": kwargs.get("yearly_loss", 100000),
        "ripple_effects_identified": 3,
        "future_projection": "one_year",
        "emotional_engagement_level": "high",
        "readiness_for_solution": "immediate",
        "escape_positioning": "clear"
    }
)

# BELFORT PROMPT #11: CLOSING PSYCHOLOGY
belfort_close_psychology = BelfortPrompt(
    name="Closing Psychology - The Art of the Ask",
    context="Ready to close but nervous about asking; timing and psychology are critical",
    variables={
        "customer_profile": "Ready to buy but hasn't said yes yet",
        "market": "High-ticket sales where close matters",
        "product": "Significant investment requiring affirmation",
        "situation": "Prospect is at 90% yes; just need to close"
    },
    expert_voice="""
    Most salespeople fail at closing because they get NERVOUS. They sense the moment is near
    and they back off. They ask permission instead of taking control.
    The close is just the natural progression of the conversation. If you've done everything right,
    the close is EASY. You don't ask 'will you do this' - you ask 'how are we implementing this'.
    That's the difference between amateurs and closers.
    """,
    tactic="""
    1. Watch for buying signals: leaning in, asking about details, mentioning timeline
    2. When you see them, STOP selling and start closing
    3. Use silence strategically: after a strong point, let them speak
    4. Ask closing questions that assume yes:
       - "When would you want to start?" not "Do you want to start?"
       - "Which package makes more sense for you?" not "Are you interested?"
    5. Don't over-explain at the close - less is more
    6. Get them to verbally commit: "So we're doing this?" "Absolutely"
    7. Immediately move to logistics (lock it in)
    """,
    success_metric="Prospect verbally commits; deal is closed in one call instead of multiple",
    python_example=lambda **kwargs: {
        "buying_signals_monitored": True,
        "signal_count_to_close": 3,
        "sales_stop_point": "identified",
        "silence_deployment": "strategic",
        "assumption_level": "high",
        "verbal_commitment_obtained": True,
        "logistics_locked_in": "same_call"
    }
)

# BELFORT PROMPT #12: HANDLING "I NEED TO THINK ABOUT IT"
belfort_think = BelfortPrompt(
    name="Handling 'I Need to Think About It' - Convert the Stall",
    context="Prospect asks for time to think instead of deciding; classic objection",
    variables={
        "customer_profile": "Indecisive or wants to consult others",
        "market": "Complex sales with multiple decision-makers",
        "product": "Significant commitment requiring consideration",
        "situation": "Prospect stalling instead of closing"
    },
    expert_voice="""
    'I need to think about it' is one of the most dangerous phrases in sales.
    Because they're not going to think about it - they're going to forget about it.
    Or they're going to talk themselves out of it. Or they're going to get a bad recommendation.
    So when you hear that phrase, you PROBE it. You find out what the REAL concern is.
    Then you address it right there, and you close.
    """,
    tactic="""
    1. Don't accept the stall: "I get that - most people like to think things through"
    2. Probe the real concern: "What specifically do you want to think about?"
    3. They'll usually say price, fit, or need to consult someone
    4. Address it immediately: "Good news - we can handle that right now"
    5. If it's someone else: "Great, let's get them on the call. They're going to want to..."
    6. If it's price: "The only way the price works is if we get you started this week"
    7. Offer to think about it together: "Let's think through this right now while it's fresh"
    """,
    success_metric="Prospect either closes or schedules follow-up with real next step",
    python_example=lambda **kwargs: {
        "stall_detection": "immediate",
        "real_concern_uncovered": True,
        "concern_type": kwargs.get("likely_concern", "price_or_approval"),
        "same_call_resolution": "attempted",
        "escalation_if_needed": "executive_to_join",
        "fake_stall_conversion_rate": "65_percent"
    }
)

# BELFORT PROMPT #13: MULTI-THREADED SELLING
belfort_multithreading = BelfortPrompt(
    name="Multi-Threaded Selling - Don't Rely on One Person",
    context="One contact can't close deal alone; need multiple stakeholders involved",
    variables={
        "customer_profile": "Part of larger buying committee",
        "market": "Enterprise sales with multiple approval levels",
        "product": "Requires multiple department stakeholder approval",
        "situation": "One contact is champion but needs allies"
    },
    expert_voice="""
    Smart salespeople don't build one relationship in an account - they build MANY.
    Because you never know who's going to have the final say. Is it the end-user, the CFO,
    the CIO, or the CEO? So you build relationships with ALL of them.
    You make sure that NO MATTER who gets asked for their opinion, you've already got them on your side.
    That's not manipulation, that's strategy.
    """,
    tactic="""
    1. Map the organizational chart: who influences the decision?
    2. Get your champion to introduce you to 2-3 other stakeholders
    3. Tailor your message to each: CFO wants ROI, CIO wants integration, CEO wants competitive advantage
    4. Have your champion endorse you to each: "They're the ones who helped us think this through"
    5. Build consensus before the final decision
    6. Have your champion gather input from others, then report back
    7. Be the person who makes everyone look good in the evaluation
    """,
    success_metric="Deal closes even if one stakeholder goes quiet; multiple people want it",
    python_example=lambda **kwargs: {
        "stakeholder_count": 3,
        "champion_identified": True,
        "champion_endorsement": "active",
        "multiple_relationships_built": True,
        "customized_messaging": "each_stakeholder",
        "consensus_level_pre_close": "80_percent",
        "stakeholder_turnover_risk": "mitigated"
    }
)

# BELFORT PROMPT #14: MANAGING BUYER'S REMORSE
belfort_remorse = BelfortPrompt(
    name="Managing Buyer's Remorse - Lock in the Deal",
    context="Deal is close to closing but prospect is showing cold feet; need to finalize",
    variables={
        "customer_profile": "Second-guessing decision at last minute",
        "market": "High-ticket where doubt is common",
        "product": "Significant commitment causing hesitation",
        "situation": "Prospect wavering at the finish line"
    },
    expert_voice="""
    The MOMENT they agree is when the doubt creeps in. They start thinking
    'Wait, did I just commit to that?' That's buyer's remorse, and it kills deals.
    So immediately after the agreement, you BUILD CONFIDENCE. You remind them why it's right.
    You give them social proof. You get them excited about moving forward.
    You lock in the deal before doubt wins.
    """,
    tactic="""
    1. Immediately after yes: "Great decision - here's why this is going to work so well..."
    2. Remind them of the COST of NOT doing this: "The alternative was..."
    3. Provide social proof: "Companies like X did this and saw Y results"
    4. Get them excited about outcomes: "In 30 days, you're going to see Z improve"
    5. Have them visualize success: "Picture your team when they see how much this streamlines..."
    6. Move immediately to logistics (no time for doubt to settle)
    7. Get written agreement if possible (psychology of commitment)
    """,
    success_metric="Prospect stays enthusiastic; doesn't come back with doubts; closes fast",
    python_example=lambda **kwargs: {
        "buyer_remorse_monitoring": True,
        "immediate_confidence_building": True,
        "cost_of_not_doing_reminder": "stark",
        "social_proof_provided": "same_call",
        "success_visualization": "detailed",
        "logistics_speed": "immediate",
        "written_confirmation": "yes_response_rate_increase"
    }
)

# BELFORT PROMPT #15: PHONE GAME MASTERY
belfort_phone_game = BelfortPrompt(
    name="Phone Game Mastery - The Call Is Everything",
    context="Phone sales where voice is your entire presence; need to sound like a pro",
    variables={
        "customer_profile": "Phone-only interaction, no video or in-person",
        "market": "Inside sales, phone-driven",
        "product": "Selling over the phone",
        "situation": "Remote sales where call quality determines outcome"
    },
    expert_voice="""
    On the phone, your VOICE is everything. You don't have body language, handshake, or presence.
    You have TONE, ENERGY, and WORDS. That's it.
    So you master all three. You sound like the most confident, successful person they've talked to all day.
    You sound like someone who's MADE it. That carries over the phone and makes you credible.
    """,
    tactic="""
    1. Clear your space of distractions (you can't be focused if you're not)
    2. Stand up when you call (changes your energy and tonality)
    3. Smile when you speak (it comes through in your voice)
    4. Speak with PACE control: speed up during high-energy moments, slow down at important points
    5. Use pauses deliberately (let words land)
    6. Eliminate filler words: "um", "like", "you know" (sounds inexperienced)
    7. Breathe deeply (calm, centered, authoritative)
    8. Read the room: if they're quiet, are they engaged or uninterested? Adjust energy accordingly
    """,
    success_metric="Prospect says 'I'd buy from you just based on how you sound' or doesn't ask for call back",
    python_example=lambda **kwargs: {
        "physical_preparation": "standing",
        "energy_level": "highest",
        "tonality_control": "mastered",
        "pace_variation": "intentional",
        "filler_words": "eliminated",
        "breathing_technique": "diaphragmatic",
        "engagement_reading": "real_time_adjustment"
    }
)

# BELFORT PROMPT #16: OVERCOMING PRICE OBJECTIONS LIKE A BOSS
belfort_price_overcome = BelfortPrompt(
    name="Overcoming Price Objections Like a Boss",
    context="Price objection is raised; prospect says it's too expensive",
    variables={
        "customer_profile": "Price-conscious or budget-constrained",
        "market": "Competitive with lower-price alternatives",
        "product": "Premium positioning but price resistance",
        "situation": "Most common objection: 'Your price is too high'"
    },
    expert_voice="""
    'Your price is too high' is not REALLY a price objection. It's a VALUE objection.
    They don't see why it's worth that much. So you don't defend the price,
    you BUILD THE VALUE. You show them what they get, what others pay, what they save.
    Then the price doesn't matter anymore because the value eclipses it.
    """,
    tactic="""
    1. Don't apologize for price: "Yeah, we're not the cheapest..."
    2. Immediately add value: "...but here's what you get..."
    3. Break down total cost of ownership: "Over 3 years, that's only $X per month"
    4. Compare to alternatives: "Competitor charges $Y but doesn't include Z"
    5. Quantify ROI: "This pays for itself in 6 months, then savings flow to your bottom line"
    6. Social proof: "Companies paying similar amounts save an average of $Z"
    7. Urgency: "Pricing increases if we wait" or "Can't guarantee this price next quarter"
    """,
    success_metric="Prospect stops talking about price; moves to discussing implementation",
    python_example=lambda **kwargs: {
        "value_building_approach": "immediate",
        "cost_breakdown_provided": True,
        "total_cost_of_ownership": "3_year",
        "roi_payback_period": "6_months",
        "competitor_comparison": "favorable",
        "pricing_scarcity": "real_deadline",
        "price_objection_elimination_rate": "75_percent"
    }
)

# BELFORT PROMPT #17: FOLLOW-UP FURY
belfort_followup = BelfortPrompt(
    name="Follow-Up Fury - Never Let Deals Die",
    context="Prospect said 'let me think about it' or 'I'll circle back'; need persistent follow-up",
    variables={
        "customer_profile": "Said yes-ish but not committed",
        "market": "Deal stalls are common",
        "product": "Needs momentum and repeated exposure",
        "situation": "After initial pitch, prospect went silent"
    },
    expert_voice="""
    Persistence separates the winners from the losers. Most salespeople follow up once or twice and give up.
    That's QUIT energy. Winners follow up 7-10 times because they know the deal dies if they don't keep it alive.
    Each follow-up is different, though. You're not nagging, you're providing value and keeping it warm.
    That's how deals that looked dead suddenly come back to life.
    """,
    tactic="""
    1. First follow-up (2 days after): "Quick thought I had while thinking about your situation..."
    2. Second (5 days): Send an article/insight relevant to their problem
    3. Third (10 days): "Wanted to reconnect, thoughts since we last talked?"
    4. Fourth (15 days): Introduce them to a customer with similar challenge
    5. Fifth (20 days): New angle: "Realized we didn't discuss X, which might solve Y for you"
    6. Sixth (25 days): "Other companies in your space are now using this, thought of you"
    7. Each follow-up: valuable, not salesy, easy to say yes to
    """,
    success_metric="Dead deal resurfaces; prospect re-engages; deal closes from follow-up persistence",
    python_example=lambda **kwargs: {
        "followup_count": 6,
        "followup_frequency_days": [2, 5, 10, 15, 20, 25],
        "value_provided_each": True,
        "persistence_quality": "high",
        "resurrection_rate": "35_percent",
        "average_days_to_close": 30
    }
)

# BELFORT PROMPT #18: CREATING URGENCY THROUGH FEAR OF LOSS
belfort_fomo = BelfortPrompt(
    name="Creating Urgency Through Fear of Loss (FOMO)",
    context="Prospect is interested but not moving; need to create fear of missing opportunity",
    variables={
        "customer_profile": "Interested but not urgent",
        "market": "Competitive with others choosing similar solutions",
        "product": "Limited availability or time-sensitive advantage",
        "situation": "Need to shift from 'thinking' to 'doing' urgently"
    },
    expert_voice="""
    Fear of loss is 10x more powerful than desire for gain. People will run from losses
    faster than they'll run toward gains. So you make the LOSS real.
    Not fake urgency, REAL things they're losing by waiting: market position, competitive advantage,
    time, money. Make it FEEL like if they wait, someone else wins and they lose.
    """,
    tactic="""
    1. Emphasize competitive moves: "Your competitors are already..."
    2. Show opportunity cost: "While you're evaluating, they're getting results"
    3. Reference limited time: "This Q, not next Q" or "This offer expires Friday"
    4. Create market movement narrative: "The market's moving toward X, those who lead get advantage"
    5. Mention deal velocity: "Three deals closing this week alone"
    6. Make staying same = losing: "Cost of status quo is now higher than our cost"
    7. End with commitment demand: "So we need to know by X date to fit you in"
    """,
    success_metric="Prospect accelerates timeline; says yes to avoid missing opportunity",
    python_example=lambda **kwargs: {
        "loss_framing": "explicit",
        "competitive_threat": "mentioned",
        "opportunity_cost_quantified": True,
        "time_limit": "friday_deadline",
        "market_movement_sense": "urgent",
        "deal_velocity_social_proof": "real_deals_closing",
        "decision_deadline": "explicit",
        "urgency_response_rate": "60_percent"
    }
)

# Export all Belfort prompts
BELFORT_PROMPTS = [
    belfort_straight_line,
    belfort_qualification,
    belfort_emotion,
    belfort_objection_crush,
    belfort_assumptive,
    belfort_urgency,
    belfort_tonality,
    belfort_pattern,
    belfort_rapport,
    belfort_pain,
    belfort_close_psychology,
    belfort_think,
    belfort_multithreading,
    belfort_remorse,
    belfort_phone_game,
    belfort_price_overcome,
    belfort_followup,
    belfort_fomo
]

__all__ = ["BELFORT_PROMPTS", "BelfortPrompt"]
