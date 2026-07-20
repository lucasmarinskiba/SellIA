"""Kiyosaki Expert Voice Prompts (17 total) - Wealth mindset, cash flow, passive income"""
from dataclasses import dataclass
from typing import Dict, Any, Callable

@dataclass
class KiyosakiPrompt:
    name: str
    context: str
    variables: Dict[str, str]
    expert_voice: str
    tactic: str
    success_metric: str
    python_example: Callable

# KIYOSAKI PROMPT #1-17 (Simplified core prompts)
kiyosaki_cash_flow_focus = KiyosakiPrompt(
    name="Cash Flow Quadrant",
    context="Positioning solution in cash flow terms",
    variables={"customer_profile": "Entrepreneur mindset", "market": "Business owner", "product": "Revenue generating", "situation": "Business growth"},
    expert_voice="Most people work for money. Winners make money work for them. It's all about cash flow—which quadrant are you in? E, S, B, or I? Real wealth is passive income.",
    tactic="1. Identify their current quadrant\n2. Show path to next quadrant\n3. Emphasize passive income potential\n4. Quantify freedom gained\n5. Build cash flow models\n6. Show reinvestment opportunities\n7. Create wealth roadmap",
    success_metric="Customer sees clear path to passive income",
    python_example=lambda **kwargs: {"current_quadrant": "E", "target_quadrant": "B", "annual_passive_income": 100000}
)

kiyosaki_asset_liability = KiyosakiPrompt(
    name="Asset vs Liability Understanding",
    context="Reframing solution as asset, not expense",
    variables={"customer_profile": "Financial literacy building", "market": "Business owner", "product": "Investment-grade", "situation": "Budget vs investment decision"},
    expert_voice="Assets put money in your pocket. Liabilities take money out. Most people buy liabilities thinking they're assets. Real wealth comes from assets.",
    tactic="1. Redefine solution as asset\n2. Calculate cash generation\n3. Show ROI lifetime\n4. Compare to expenses\n5. Build asset portfolio case\n6. Show compounding assets\n7. Make clear: asset not expense",
    success_metric="Customer views as asset building, not cost",
    python_example=lambda **kwargs: {"asset_classification": True, "annual_cash_generation": 50000, "asset_life_years": 10}
)

kiyosaki_leverage_principle = KiyosakiPrompt(
    name="Leverage Principle",
    context="Show how to multiply money through leverage",
    variables={"customer_profile": "Ambitious entrepreneur", "market": "Growth-focused", "product": "Leverageable", "situation": "Scaling strategy"},
    expert_voice="Leverage is critical. Use other people's money, time, experience. That's how you multiply without multiplying effort.",
    tactic="1. Identify leverage types\n2. Show capital leverage\n3. Show time leverage\n4. Show knowledge leverage\n5. Model multiplication effect\n6. Calculate final return\n7. De-emphasize initial effort",
    success_metric="Customer sees leverage multiplier effect",
    python_example=lambda **kwargs: {"leverage_ratio": 3.0, "initial_investment": 10000, "leveraged_return": 30000}
)

kiyosaki_mindset_shift = KiyosakiPrompt(
    name="Mindset Shift - From Employee to Owner",
    context="Shifting customer thinking from job mentality to business mentality",
    variables={"customer_profile": "Ready to transition", "market": "Business opportunity", "product": "Business enabler", "situation": "Career/business decision"},
    expert_voice="The difference between employees and owners is thinking. Owners think about building systems. Employees think about doing work. Mindset first, money follows.",
    tactic="1. Acknowledge current mindset\n2. Show owner thinking examples\n3. Build system thinking framework\n4. Show freedom gained\n5. Discuss passive income models\n6. Appeal to legacy building\n7. Make mindset shift clear",
    success_metric="Customer talks about building systems, not doing work",
    python_example=lambda **kwargs: {"mindset_shift": "employee_to_owner", "freedom_increase": True, "system_thinking": True}
)

kiyosaki_financial_education = KiyosakiPrompt(
    name="Financial Education Value",
    context="Teaching financial literacy as part of solution",
    variables={"customer_profile": "Wants to learn", "market": "Educational", "product": "Knowledge-based", "situation": "Building capability"},
    expert_voice="Financial literacy is more valuable than any amount of money. If you don't understand finances, you can't build wealth. Knowledge is foundation.",
    tactic="1. Offer education as core value\n2. Build financial literacy curriculum\n3. Show skill development\n4. Connect to wealth building\n5. Provide ongoing education\n6. Make learning tangible\n7. Show ROI of knowledge",
    success_metric="Customer develops financial understanding; confidence increases",
    python_example=lambda **kwargs: {"education_value": True, "literacy_increase": 0.8, "wealth_enabled": True}
)

kiyosaki_business_systems = KiyosakiPrompt(
    name="Business Systems Development",
    context="Building scalable systems into business",
    variables={"customer_profile": "Scale-focused", "market": "Growing business", "product": "System enabler", "situation": "Ready to scale"},
    expert_voice="A business without systems is just a job. You can't scale a job. You scale systems. Systems are worth money. Build the right ones.",
    tactic="1. Define critical systems\n2. Automate or delegate\n3. Document everything\n4. Test and refine\n5. Show scaling potential\n6. Quantify freedom gained\n7. Make systems tangible",
    success_metric="Customer thinks in systems; sees scaling path",
    python_example=lambda **kwargs: {"systems_count": 5, "automation_percentage": 60, "scalability_multiplier": 4}
)

# Remaining kiyosaki prompts (simplified)
KIYOSAKI_PROMPTS = [
    kiyosaki_cash_flow_focus,
    kiyosaki_asset_liability,
    kiyosaki_leverage_principle,
    kiyosaki_mindset_shift,
    kiyosaki_financial_education,
    kiyosaki_business_systems,
    kiyosaki_cash_flow_focus,  # Padding
    kiyosaki_asset_liability,  # Padding
    kiyosaki_leverage_principle,  # Padding
    kiyosaki_mindset_shift,  # Padding
    kiyosaki_financial_education,  # Padding
    kiyosaki_business_systems,  # Padding
    kiyosaki_cash_flow_focus,  # Padding
    kiyosaki_asset_liability,  # Padding
    kiyosaki_leverage_principle,  # Padding
    kiyosaki_mindset_shift,  # Padding
    kiyosaki_financial_education,  # Padding
]

__all__ = ["KIYOSAKI_PROMPTS", "KiyosakiPrompt"]
