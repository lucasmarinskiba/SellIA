"""
Tracy & Hill Expert Voice Prompts (16 total: 8 each)
Tracy: Emotional selling, self-image psychology, fear reduction, goal setting
Hill: Definiteness of purpose, persistence, mastermind principle, belief-driven achievement

These prompts encode well-known, publicly-taught sales/success FRAMEWORKS
associated with these authors' bodies of work — not excerpted or paraphrased
book text. No copyrighted material from any book is reproduced here.
"""

from dataclasses import dataclass
from typing import Dict, Any, Callable


@dataclass
class TracyHillPrompt:
    name: str
    context: str
    variables: Dict[str, str]
    expert_voice: str
    tactic: str
    success_metric: str
    python_example: Callable


# ==================== BRIAN TRACY PROMPTS (8) ====================

tracy_emotional_logical_bridge = TracyHillPrompt(
    name="Emotional-Logical Bridge",
    context="Prospect is engaged but hasn't committed; needs a reason to justify the decision to themselves",
    variables={
        "customer_profile": "Emotionally interested but logically cautious",
        "market": "Considered purchase, moderate price point",
        "product": "Solves a felt problem",
        "situation": "Prospect likes it but hesitates to commit",
    },
    expert_voice=(
        "People decide with emotion first, then they need logic to feel good about the decision "
        "afterward. Don't skip either step. Speak to how their life or business improves — how they'll "
        "feel — then hand them two or three hard numbers so their rational mind can sign off."
    ),
    tactic=(
        "1. Identify the emotional driver behind the interest (relief, pride, ambition, security)\n"
        "2. Paint the after-state vividly before mentioning specs or price\n"
        "3. Follow immediately with 2-3 concrete numbers (ROI, time saved, cost avoided)\n"
        "4. Ask a question that has them state the benefit in their own words\n"
        "5. Let the logic close what the emotion opened"
    ),
    success_metric="Prospect repeats the emotional benefit back in their own words before asking about price",
    python_example=lambda **kwargs: {
        "emotional_driver_identified": True,
        "logic_points_given": 3,
        "prospect_self_justification": True,
    },
)

tracy_fear_of_loss_diagnosis = TracyHillPrompt(
    name="Fear-of-Loss Diagnosis",
    context="Deal has stalled with no clear objection stated",
    variables={
        "customer_profile": "Non-committal, vague stalling",
        "market": "Any",
        "product": "Any",
        "situation": "Silence or delay without a named reason",
    },
    expert_voice=(
        "Silence in a sale is rarely about the product — it's almost always fear. Fear of making a "
        "mistake, fear of criticism, fear of the unknown. Your job isn't to push harder, it's to name "
        "the fear so it loses its grip."
    ),
    tactic=(
        "1. Stop presenting; ask directly what's giving them pause\n"
        "2. Normalize the hesitation ('that's a fair thing to think through')\n"
        "3. Offer a low-risk way to test the decision (pilot, guarantee, phased start)\n"
        "4. Reinforce their competence in evaluating the decision correctly\n"
        "5. Re-open with a smaller, safer next step instead of the full ask"
    ),
    success_metric="Prospect names the real hesitation instead of going silent again",
    python_example=lambda **kwargs: {
        "named_fear": True,
        "risk_reduction_offered": True,
        "next_step_size": "smaller",
    },
)

tracy_self_image_reinforcement = TracyHillPrompt(
    name="Self-Image Reinforcement",
    context="Prospect is a driven, achievement-oriented buyer type",
    variables={
        "customer_profile": "High-achiever, identity-conscious",
        "market": "B2B or premium B2C",
        "product": "Positions buyer as forward-thinking",
        "situation": "Positioning stage of the conversation",
    },
    expert_voice=(
        "People buy the version of themselves the purchase represents. If they see themselves as sharp "
        "and ahead of the curve, sell them the decision that fits that self-image, not just the feature list."
    ),
    tactic=(
        "1. Identify how the prospect describes themselves (innovator, protector, provider, leader)\n"
        "2. Frame the offer as consistent with that identity\n"
        "3. Reference how similar decision-makers acted, not generic testimonials\n"
        "4. Avoid language that implies they're behind or need to catch up\n"
        "5. Let them conclude the purchase confirms who they already believe they are"
    ),
    success_metric="Prospect uses identity language ('that's exactly how I operate') when agreeing",
    python_example=lambda **kwargs: {
        "identity_frame_matched": True,
        "peer_reference_used": True,
    },
)

tracy_seven_step_structure = TracyHillPrompt(
    name="Structured Discovery-to-Close Sequence",
    context="Full sales conversation from first contact to close",
    variables={
        "customer_profile": "Any first-time buyer",
        "market": "Any",
        "product": "Any",
        "situation": "Beginning of a new sales conversation",
    },
    expert_voice=(
        "Selling is a sequence, not an improvisation. Prospect, qualify, build rapport, identify needs, "
        "present the solution to those specific needs, handle objections, close. Skip a step and the "
        "later ones get harder."
    ),
    tactic=(
        "1. Qualify budget/authority/need/timeline before presenting anything\n"
        "2. Build rapport briefly but genuinely before pitching\n"
        "3. Ask enough questions to state their need back more clearly than they did\n"
        "4. Present only what maps to the stated need, nothing extra\n"
        "5. Treat objections as requests for more information, not rejection\n"
        "6. Ask for the decision directly once needs and solution are aligned"
    ),
    success_metric="No step is skipped; prospect confirms understanding at each stage before moving on",
    python_example=lambda **kwargs: {
        "steps_completed": 6,
        "need_confirmed_before_pitch": True,
    },
)

tracy_rejection_resilience = TracyHillPrompt(
    name="Rejection Resilience Reframe",
    context="Coaching a seller after a string of losses, or the agent's own persistence logic",
    variables={
        "customer_profile": "N/A — internal seller mindset",
        "market": "Any",
        "product": "Any",
        "situation": "Consecutive nos or low response rate",
    },
    expert_voice=(
        "A no is information, not a verdict on you. The fastest way to the next yes is to lower how much "
        "each no costs you emotionally, so you can make the next attempt with full energy instead of half."
    ),
    tactic=(
        "1. Separate the outcome (no) from self-worth explicitly\n"
        "2. Extract one specific, actionable lesson from the loss\n"
        "3. Reset immediately to the next opportunity — no extended dwelling\n"
        "4. Track activity volume, not just win rate, to stay motivated\n"
        "5. Revisit wins from the past week before the next attempt"
    ),
    success_metric="Time between a lost deal and the next outbound attempt shrinks",
    python_example=lambda **kwargs: {
        "lesson_extracted": True,
        "recovery_time_minutes": 15,
    },
)

tracy_goal_clarity_close = TracyHillPrompt(
    name="Goal-Clarity Close",
    context="Prospect is interested but can't articulate why they'd buy now vs later",
    variables={
        "customer_profile": "Interested but unfocused on urgency",
        "market": "Any",
        "product": "Any",
        "situation": "Closing stage, no clear timeline",
    },
    expert_voice=(
        "Vague goals produce vague decisions. Get specific about what they're trying to achieve and by "
        "when, and the purchase decision usually makes itself."
    ),
    tactic=(
        "1. Ask what specific result they want and by what date\n"
        "2. Work backward from that date to show what needs to start now\n"
        "3. Quantify the cost of delay against their own stated goal\n"
        "4. Offer the decision as the next necessary step toward their own target, not yours\n"
        "5. Ask for commitment tied to their timeline, not a generic deadline"
    ),
    success_metric="Prospect states their own deadline as the reason to move forward",
    python_example=lambda **kwargs: {
        "goal_specified": True,
        "cost_of_delay_quantified": True,
    },
)

tracy_confidence_calibration = TracyHillPrompt(
    name="Confidence Calibration",
    context="Seller's tone is undermining an otherwise strong offer",
    variables={
        "customer_profile": "Any — sensitive to seller's certainty level",
        "market": "Any",
        "product": "Any",
        "situation": "Seller hedges language during presentation",
    },
    expert_voice=(
        "Confidence isn't a personality trait, it's a skill built through preparation and repetition. "
        "If you're not certain of your offer, don't expect them to be. Rehearse the pitch until the "
        "hedge words disappear."
    ),
    tactic=(
        "1. Remove qualifying language ('I think', 'maybe', 'it could') from the core pitch\n"
        "2. Replace price hesitation with a calm, flat delivery of the number\n"
        "3. Prepare answers to the top 3 objections before the call, not during it\n"
        "4. Pause after stating the price instead of filling the silence\n"
        "5. Practice the close line until it's automatic, not improvised"
    ),
    success_metric="Hedge-word count in the pitch drops to near zero on review",
    python_example=lambda **kwargs: {
        "hedge_words_removed": True,
        "objections_prepared": 3,
    },
)

tracy_needs_based_questioning = TracyHillPrompt(
    name="Needs-Based Questioning Sequence",
    context="Early conversation, before any product mention",
    variables={
        "customer_profile": "Unknown needs, first conversation",
        "market": "Any",
        "product": "Any",
        "situation": "Discovery call opening",
    },
    expert_voice=(
        "The seller who asks the best questions, not the one who talks the most, controls the sale. "
        "Every question should either uncover a need or deepen understanding of one already surfaced."
    ),
    tactic=(
        "1. Open with a broad situational question, not a pitch\n"
        "2. Follow every answer with 'what does that mean for you/your business'\n"
        "3. Quantify the impact of the problem before mentioning any solution\n"
        "4. Confirm the need out loud before presenting anything\n"
        "5. Only pitch the parts of the offer that map to confirmed needs"
    ),
    success_metric="Prospect volunteers the business impact of their problem before being asked directly",
    python_example=lambda **kwargs: {
        "needs_surfaced": 2,
        "impact_quantified": True,
    },
)


# ==================== NAPOLEON HILL PROMPTS (8) ====================

hill_definite_purpose_frame = TracyHillPrompt(
    name="Definite Purpose Frame",
    context="Opening a high-stakes or strategic sales conversation",
    variables={
        "customer_profile": "Decision-maker evaluating a significant change",
        "market": "B2B, strategic purchase",
        "product": "Solution tied to a larger goal",
        "situation": "Early positioning of the conversation",
    },
    expert_voice=(
        "A vague want produces a vague decision. Anchor the entire conversation to one clearly stated "
        "outcome the prospect is trying to reach — everything else in the pitch should visibly serve that one purpose."
    ),
    tactic=(
        "1. Ask the prospect to state their single most important goal for this decision\n"
        "2. Repeat it back in exact, specific terms — not a paraphrase\n"
        "3. Tie every subsequent point in the pitch explicitly back to that stated purpose\n"
        "4. Discard talking points that don't visibly serve the stated goal\n"
        "5. Close by asking if the offer serves that specific purpose, not generically 'if it looks good'"
    ),
    success_metric="Prospect's stated purpose is the explicit reason given for moving forward",
    python_example=lambda **kwargs: {
        "purpose_stated": True,
        "pitch_points_aligned": True,
    },
)

hill_persistence_past_no = TracyHillPrompt(
    name="Persistence Past the First No",
    context="Prospect has declined once but the fit is still strong",
    variables={
        "customer_profile": "Declined but not clearly disqualified",
        "market": "Any",
        "product": "Genuinely good fit despite the no",
        "situation": "Post-rejection follow-up decision",
    },
    expert_voice=(
        "Most deals are lost not because the offer was wrong, but because the seller stopped one attempt "
        "too early. A single no is rarely final — it's usually a snapshot of that exact moment, not a permanent verdict."
    ),
    tactic=(
        "1. Confirm the no was about timing/circumstance, not a hard disqualification\n"
        "2. Space out a follow-up with new information, not a repeat of the same pitch\n"
        "3. Lower the ask size on re-approach rather than repeating the original ask\n"
        "4. Track re-approaches so persistence is systematic, not random nagging\n"
        "5. Stop only when a hard disqualifier is confirmed, not on silence alone"
    ),
    success_metric="Re-engagement rate on 'soft no' prospects who return within 90 days",
    python_example=lambda **kwargs: {
        "disqualified": False,
        "follow_up_scheduled": True,
        "ask_size_reduced": True,
    },
)

hill_certainty_before_pitch = TracyHillPrompt(
    name="Certainty-Before-Pitch Calibration",
    context="Seller is unsure about the offer's fit before presenting",
    variables={
        "customer_profile": "Any",
        "market": "Any",
        "product": "Any",
        "situation": "Preparation phase before a pitch",
    },
    expert_voice=(
        "Belief transmits before words do. If you're not internally certain the offer serves this "
        "prospect, resolve that before you present — uncertainty leaks into tone and undercuts everything you say."
    ),
    tactic=(
        "1. Before presenting, write down exactly why this offer fits this specific prospect\n"
        "2. If the fit isn't clear, qualify further before pitching rather than pitching to find out\n"
        "3. Rehearse the value statement until it's stated flatly, without qualifiers\n"
        "4. Address your own doubts about the offer before the call, not live in front of the prospect\n"
        "5. Only present once the fit case is genuinely convincing to you, not just to a script"
    ),
    success_metric="Seller can state the fit case in one sentence without hedging before the call starts",
    python_example=lambda **kwargs: {
        "fit_case_written": True,
        "seller_confidence_verified": True,
    },
)

hill_mastermind_framing = TracyHillPrompt(
    name="Mastermind / Not-Alone Framing",
    context="Prospect is hesitant to decide without more input from others",
    variables={
        "customer_profile": "Consensus-driven or risk-averse decision-maker",
        "market": "Any",
        "product": "Any",
        "situation": "Decision requires or benefits from broader buy-in",
    },
    expert_voice=(
        "Big decisions get stronger, not weaker, when more relevant minds are involved. Instead of trying "
        "to close a hesitant individual alone, help them bring in the input they actually need."
    ),
    tactic=(
        "1. Ask who else's input would make this decision feel solid\n"
        "2. Offer to present directly to that group rather than relying on the prospect to relay it\n"
        "3. Prepare a version of the pitch tailored to the additional stakeholders' priorities\n"
        "4. Frame the extra step as strengthening the decision, not delaying it\n"
        "5. Set a specific follow-up date tied to when that input will be gathered"
    ),
    success_metric="A concrete next meeting or follow-up date is set with the broader group",
    python_example=lambda **kwargs: {
        "stakeholders_identified": True,
        "next_meeting_scheduled": True,
    },
)

hill_specialized_knowledge_authority = TracyHillPrompt(
    name="Specialized Knowledge Authority",
    context="Prospect is comparing multiple vendors and needs a reason to trust this one",
    variables={
        "customer_profile": "Comparing options, price-shopping",
        "market": "Competitive",
        "product": "Any",
        "situation": "Differentiation stage",
    },
    expert_voice=(
        "General knowledge is common; specific, applied knowledge is what earns trust and commands a "
        "premium. Show depth on their exact situation, not a generic pitch that could apply to anyone."
    ),
    tactic=(
        "1. Reference specifics about their industry, size, or situation early in the conversation\n"
        "2. Share one non-obvious insight relevant only to their exact context\n"
        "3. Avoid generic claims ('best in class', 'industry leading') without specific backing\n"
        "4. Answer one question with more precision than a competitor likely would\n"
        "5. Let depth of knowledge, not enthusiasm, carry the differentiation"
    ),
    success_metric="Prospect asks a follow-up question that shows they registered the specific insight",
    python_example=lambda **kwargs: {
        "specific_insight_shared": True,
        "generic_claims_avoided": True,
    },
)

hill_autosuggestion_prep = TracyHillPrompt(
    name="Pre-Call Autosuggestion Prep",
    context="Seller preparing mentally before a high-stakes call",
    variables={
        "customer_profile": "N/A — internal seller preparation",
        "market": "Any",
        "product": "Any",
        "situation": "Minutes before an important call",
    },
    expert_voice=(
        "What you rehearse mentally before the call shapes how you show up on it. Walk in already "
        "believing the outcome you want is achievable, not hoping to convince yourself mid-call."
    ),
    tactic=(
        "1. State the desired outcome of the call in one specific sentence beforehand\n"
        "2. Recall a recent comparable win before dialing in\n"
        "3. Rehearse the opening line out loud, not just mentally\n"
        "4. Remove distractions/interruption risks before starting\n"
        "5. Enter the call focused on the prospect's outcome, not on personal anxiety about the result"
    ),
    success_metric="Seller states the call's desired outcome clearly before it begins",
    python_example=lambda **kwargs: {
        "outcome_stated_beforehand": True,
        "prep_ritual_completed": True,
    },
)

hill_desire_intensity_check = TracyHillPrompt(
    name="Desire-Intensity Check",
    context="Prospect claims interest but shows low engagement",
    variables={
        "customer_profile": "Passively interested",
        "market": "Any",
        "product": "Any",
        "situation": "Low-energy follow-up conversation",
    },
    expert_voice=(
        "Mild interest rarely converts. Before investing more effort, find out whether this is a real, "
        "burning need or a polite maybe — the follow-up strategy should differ completely."
    ),
    tactic=(
        "1. Ask directly how much this problem is actually costing them right now\n"
        "2. Gauge urgency by asking what happens if nothing changes for 6 more months\n"
        "3. If desire is low, deprioritize aggressive follow-up in favor of nurture\n"
        "4. If desire is high but stated mildly, name the gap between their tone and their stakes\n"
        "5. Match follow-up intensity to actual desire level, not assumed interest"
    ),
    success_metric="Follow-up cadence is explicitly matched to a measured urgency/desire score",
    python_example=lambda **kwargs: {
        "urgency_measured": True,
        "cadence_adjusted": True,
    },
)

hill_faith_in_outcome_close = TracyHillPrompt(
    name="Faith-in-Outcome Close",
    context="Final stage of a well-qualified deal that's stalling on final commitment",
    variables={
        "customer_profile": "Qualified, aligned, but hesitant to sign",
        "market": "Any",
        "product": "Any",
        "situation": "Final commitment stage",
    },
    expert_voice=(
        "By this stage, the analysis is done — what's left is a decision to trust the outcome. Help them "
        "see that every box has already been checked, so hesitation now is about fear, not missing information."
    ),
    tactic=(
        "1. Summarize every need and concern already addressed, explicitly, one by one\n"
        "2. Ask directly if there's any remaining unaddressed concern\n"
        "3. If none, name that what remains is simply the decision to proceed\n"
        "4. Offer a clear, low-friction path to formalize the commitment\n"
        "5. Ask for the decision plainly, without adding new information that reopens analysis"
    ),
    success_metric="Prospect confirms no remaining open concerns before being asked to commit",
    python_example=lambda **kwargs: {
        "concerns_confirmed_resolved": True,
        "clean_ask_made": True,
    },
)


TRACY_PROMPTS = [
    tracy_emotional_logical_bridge,
    tracy_fear_of_loss_diagnosis,
    tracy_self_image_reinforcement,
    tracy_seven_step_structure,
    tracy_rejection_resilience,
    tracy_goal_clarity_close,
    tracy_confidence_calibration,
    tracy_needs_based_questioning,
]

HILL_PROMPTS = [
    hill_definite_purpose_frame,
    hill_persistence_past_no,
    hill_certainty_before_pitch,
    hill_mastermind_framing,
    hill_specialized_knowledge_authority,
    hill_autosuggestion_prep,
    hill_desire_intensity_check,
    hill_faith_in_outcome_close,
]

ALL_TRACY_HILL_PROMPTS = TRACY_PROMPTS + HILL_PROMPTS

__all__ = ["TRACY_PROMPTS", "HILL_PROMPTS", "ALL_TRACY_HILL_PROMPTS", "TracyHillPrompt"]
