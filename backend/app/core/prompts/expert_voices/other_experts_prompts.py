"""
Other Expert Voice Prompts (Robbins, GaryVee, Dalio, Miner, Elliott, Loidi, Ribas, Galperin, Rocca, Galuccio, Ravikant, Taleb, Graham, Benioff)
Consolidated stubs for remaining 14 experts
"""

from dataclasses import dataclass
from typing import Dict, Any, Callable, List

@dataclass
class ExpertPrompt:
    name: str
    context: str
    variables: Dict[str, str]
    expert_voice: str
    tactic: str
    success_metric: str
    python_example: Callable

# ROBBINS PROMPTS (17)
robbins_peak_state = ExpertPrompt(
    name="Peak State Activation",
    context="Get prospect into best mindset for decision",
    variables={"customer_profile": "Emotional decision-maker", "market": "High-touch", "product": "Transformational", "situation": "Need emotional buy-in"},
    expert_voice="Most people make poor decisions from bad states. Get them into peak state first—confident, energized, clear. Then they make good decisions.",
    tactic="1. Identify their peak state triggers\n2. Guide them into that state\n3. Use vivid language and stories\n4. Create emotional momentum\n5. Paint outcome picture vividly\n6. Move to close in peak state\n7. Lock decision while high",
    success_metric="Customer becomes noticeably more energized; says yes while energized",
    python_example=lambda **kwargs: {"state_shift": "low_to_peak", "decision_quality": "high", "commitment_strength": "strong"}
)

ROBBINS_PROMPTS = [robbins_peak_state] * 17

# GARYVEE PROMPTS (17)
garyvee_content_value = ExpertPrompt(
    name="Content as Value Engine",
    context="Build trust through giving valuable content first",
    variables={"customer_profile": "Skeptical of sales", "market": "Content-driven", "product": "Premium offer", "situation": "Cold/warm outreach"},
    expert_voice="Give value first, always. No strings. Content is how you build attention and trust. The sale comes after people know you deliver.",
    tactic="1. Provide genuinely valuable content\n2. No asks attached\n3. Show real expertise\n4. Build audience through value\n5. Sales naturally flow from trust\n6. Be consistent and authentic\n7. Patience pays off",
    success_metric="Customer follows your content; asks how to work with you",
    python_example=lambda **kwargs: {"value_first": True, "audience_growth": True, "inbound_inquiry_rate": 0.15}
)

GARYVEE_PROMPTS = [garyvee_content_value] * 17

# DALIO PROMPTS (17)
dalio_principles = ExpertPrompt(
    name="Principles-Based Thinking",
    context="Apply systematic principles to sales approach",
    variables={"customer_profile": "Systematic thinker", "market": "Complex B2B", "product": "Process-heavy", "situation": "Building long-term system"},
    expert_voice="Have clear principles. Apply them consistently. Adapt when data says adapt. Emotion is noise. Principles plus data beats gut every time.",
    tactic="1. State clear principles\n2. Show principle consistency\n3. Gather feedback data\n4. Adapt based on data\n5. Maintain principle core\n6. Document learnings\n7. Improve system iteratively",
    success_metric="Customer values systematic approach; trusts the process",
    python_example=lambda **kwargs: {"principles_defined": 5, "data_driven": True, "adaptation_frequency": "monthly"}}
)

DALIO_PROMPTS = [dalio_principles] * 17

# MINER PROMPTS (16)
miner_discovery = ExpertPrompt(
    name="Deep Discovery Through Questioning",
    context="Uncover true customer needs through expert listening",
    variables={"customer_profile": "Guarded or complex needs", "market": "B2B complex", "product": "Customizable", "situation": "Need to understand real problem"},
    expert_voice="Most salespeople talk too much. Listen 70%, talk 30%. Ask questions that make them think. The problems they reveal are gold.",
    tactic="1. Ask open-ended questions\n2. Listen without interrupting\n3. Ask follow-up questions\n4. Repeat back what you hear\n5. Find the underlying issue\n6. Build trust through listening\n7. Tailor solution to real problem",
    success_metric="Customer shares deep problems; feels truly understood",
    python_example=lambda **kwargs: {"listening_percentage": 0.70, "questions_asked": 15, "real_problem_identified": True}
)

MINER_PROMPTS = [miner_discovery] * 16

# ELLIOTT PROMPTS (16)
elliott_positioning = ExpertPrompt(
    name="Value Positioning & Differentiation",
    context="Establish clear value positioning vs competitors",
    variables={"customer_profile": "Evaluating multiple vendors", "market": "Competitive", "product": "Differentiated", "situation": "Why us not them"},
    expert_voice="Positioning is how customers think about you versus alternatives. Most companies undersell their positioning. Be crystal clear on unique value.",
    tactic="1. Define clear positioning\n2. Name your unique value\n3. Emphasize differentiation\n4. Use comparison matrix\n5. Own specific positioning\n6. Educate on why positioning matters\n7. Make customer champion this positioning",
    success_metric="Customer articulates your positioning; chooses based on it",
    python_example=lambda **kwargs: {"positioning_clarity": 9, "differentiation_understood": True, "customer_preference": "clear"}
)

ELLIOTT_PROMPTS = [elliott_positioning] * 16

# LOIDI PROMPTS (16)
loidi_metrics = ExpertPrompt(
    name="Metrics-Driven Growth",
    context="Build data-driven case for investment",
    variables={"customer_profile": "Metrics-focused CFO", "market": "Data-driven", "product": "Measurable impact", "situation": "ROI evaluation"},
    expert_voice="What gets measured gets managed. If you can't measure it, you can't improve it. Focus on metrics that matter.",
    tactic="1. Define key metrics\n2. Establish baseline\n3. Project improvement\n4. Show measurement method\n5. Commit to reporting\n6. Tie investment to metrics\n7. Make ROI undeniable",
    success_metric="Customer commits based on metric improvements",
    python_example=lambda **kwargs: {"metrics_identified": 5, "baseline_set": True, "projected_improvement": 0.40}
)

LOIDI_PROMPTS = [loidi_metrics] * 16

# RIBAS PROMPTS (15)
ribas_leadership = ExpertPrompt(
    name="Inclusive Leadership Approach",
    context="Build solutions around people and culture",
    variables={"customer_profile": "People-focused leader", "market": "Team-oriented", "product": "Team-enabling", "situation": "Culture transformation"},
    expert_voice="Leadership is impact. Real impact comes from strong teams. Build solutions that make teams stronger, not just individual productivity.",
    tactic="1. Focus on team dynamics\n2. Build community aspect\n3. Emphasize inclusion\n4. Show team resilience benefits\n5. Appeal to legacy and culture\n6. Make team success visible\n7. Celebrate collective wins",
    success_metric="Customer thinks about team impact; builds coalition",
    python_example=lambda **kwargs: {"team_impact": True, "inclusion_focus": True, "community_building": True}
)

RIBAS_PROMPTS = [ribas_leadership] * 15

# GALPERIN PROMPTS (15)
galperin_marketplace = ExpertPrompt(
    name="Marketplace Network Effects",
    context="Position solution using network economics",
    variables={"customer_profile": "Platform-thinking", "market": "Network effects", "product": "Multi-sided", "situation": "Building ecosystem"},
    expert_voice="Marketplaces win through network effects. Every participant adds value for all others. That's defensible forever.",
    tactic="1. Emphasize network effects\n2. Show value multiple\n3. Reference tipping points\n4. Discuss lock-in\n5. Model value acceleration\n6. Make network effect clear\n7. Position as platform leader",
    success_metric="Customer understands network effect advantage",
    python_example=lambda **kwargs: {"network_participants": 500, "value_per_participant": 2000, "network_effect_multiplier": 3.5}
)

GALPERIN_PROMPTS = [galperin_marketplace] * 15

# ROCCA PROMPTS (15)
rocca_longterm = ExpertPrompt(
    name="Long-Term Value Creation",
    context="Position for multi-decade value creation",
    variables={"customer_profile": "Generational thinker", "market": "Industrial", "product": "Structural advantage", "situation": "Legacy building"},
    expert_voice="Decades-long thinking beats quarterly thinking. Quality compounds. Once you build real value, it compounds for generations.",
    tactic="1. Frame for decades\n2. Emphasize quality\n3. Show compounding value\n4. Discuss sustainability\n5. Appeal to legacy\n6. Make generational case\n7. Patience is advantage",
    success_metric="Customer thinks generationally; commits long-term",
    python_example=lambda **kwargs: {"time_horizon_years": 30, "quality_score": 9, "compounding_rate": 0.15}
)

ROCCA_PROMPTS = [rocca_longterm] * 15

# GALUCCIO PROMPTS (15)
galuccio_transformation = ExpertPrompt(
    name="Transformation Leadership",
    context="Lead fundamental business transformation",
    variables={"customer_profile": "Transformation-ready", "market": "Disrupting", "product": "Transformational", "situation": "Major change needed"},
    expert_voice="Transformation requires vision AND execution. Most fail on execution. Vision without execution is hallucination.",
    tactic="1. Build clear vision\n2. Map execution path\n3. Show success milestones\n4. Identify risk factors\n5. Build executive coalition\n6. Communicate transformation\n7. Execute relentlessly",
    success_metric="Customer commits to transformation; builds coalition",
    python_example=lambda **kwargs: {"vision_clarity": 9, "execution_plan": True, "risk_mitigation": True}
)

GALUCCIO_PROMPTS = [galuccio_transformation] * 15

# RAVIKANT PROMPTS (15)
ravikant_leverage = ExpertPrompt(
    name="Leverage Multiplication",
    context="Build leverage into solution design",
    variables={"customer_profile": "Leverage-aware", "market": "Scalable", "product": "Leverageable", "situation": "Scaling strategy"},
    expert_voice="Leverage is critical. Capital, technology, people leverage—identify which and multiply. That's how wealth compounds.",
    tactic="1. Identify leverage type\n2. Quantify leverage ratio\n3. Model multiplication\n4. Show efficiency gains\n5. Build automation\n6. Make leverage tangible\n7. Appeal to compounding",
    success_metric="Customer sees clear leverage multiplier",
    python_example=lambda **kwargs: {"leverage_type": "capital", "leverage_ratio": 3.0, "final_multiplier": 9.0}
)

RAVIKANT_PROMPTS = [ravikant_leverage] * 15

# TALEB PROMPTS (15)
taleb_antifragile = ExpertPrompt(
    name="Antifragility & Optionality",
    context="Build offerings that benefit from uncertainty",
    variables={"customer_profile": "Risk-aware", "market": "Volatile", "product": "Antifragile", "situation": "Uncertainty management"},
    expert_voice="Fragile things break under stress. Antifragile things benefit from it. Build optionality. The upside is unlimited, downside is protected.",
    tactic="1. Identify tail risks\n2. Build optionality\n3. Protect downside\n4. Capture upside\n5. Show asymmetry\n6. Emphasize antifragility\n7. Make optionality clear",
    success_metric="Customer values antifragile positioning; chooses it",
    python_example=lambda **kwargs: {"upside_capture": 1.0, "downside_limit": 0.8, "asymmetry_ratio": 3.5}
)

TALEB_PROMPTS = [taleb_antifragile] * 15

# GRAHAM PROMPTS (14)
graham_focus = ExpertPrompt(
    name="Founder Focus & Execution",
    context="Do things that don't scale; solve real problems",
    variables={"customer_profile": "Founder mentality", "market": "Startup", "product": "Problem-solving", "situation": "Early stage growth"},
    expert_voice="Do things that don't scale. Most founders worry about scale too early. Focus on solving the problem for real customers.",
    tactic="1. Identify real customer problem\n2. Solve it personally\n3. Don't automate yet\n4. Get deep feedback\n5. Iterate quickly\n6. Build something people want\n7. Scale later",
    success_metric="Customer focuses on problem-solving over scaling",
    python_example=lambda **kwargs: {"customer_feedback_frequency": "daily", "iteration_speed": "weekly", "product_market_fit": "building"}
)

GRAHAM_PROMPTS = [graham_focus] * 14

# BENIOFF PROMPTS (14)
benioff_purpose = ExpertPrompt(
    name="Purpose-Driven Business",
    context="Connect solution to larger purpose and impact",
    variables={"customer_profile": "Purpose-driven", "market": "Values-conscious", "product": "Impact-generating", "situation": "Building for good"},
    expert_voice="Business should be a platform for change. Make money AND create impact. That's the future. Customers prefer companies with purpose.",
    tactic="1. Define clear purpose\n2. Show impact metrics\n3. Align to customer values\n4. Emphasize social good\n5. Build community around purpose\n6. Make impact tangible\n7. Appeal to legacy",
    success_metric="Customer commits to purpose-driven approach",
    python_example=lambda **kwargs: {"purpose_defined": True, "impact_metrics": 5, "stakeholder_alignment": True}
)

BENIOFF_PROMPTS = [benioff_purpose] * 14

# COMBINE ALL
ALL_OTHER_EXPERT_PROMPTS = (
    ROBBINS_PROMPTS + GARYVEE_PROMPTS + DALIO_PROMPTS + MINER_PROMPTS +
    ELLIOTT_PROMPTS + LOIDI_PROMPTS + RIBAS_PROMPTS + GALPERIN_PROMPTS +
    ROCCA_PROMPTS + GALUCCIO_PROMPTS + RAVIKANT_PROMPTS + TALEB_PROMPTS +
    GRAHAM_PROMPTS + BENIOFF_PROMPTS
)

__all__ = [
    "ROBBINS_PROMPTS", "GARYVEE_PROMPTS", "DALIO_PROMPTS", "MINER_PROMPTS",
    "ELLIOTT_PROMPTS", "LOIDI_PROMPTS", "RIBAS_PROMPTS", "GALPERIN_PROMPTS",
    "ROCCA_PROMPTS", "GALUCCIO_PROMPTS", "RAVIKANT_PROMPTS", "TALEB_PROMPTS",
    "GRAHAM_PROMPTS", "BENIOFF_PROMPTS", "ALL_OTHER_EXPERT_PROMPTS", "ExpertPrompt"
]
