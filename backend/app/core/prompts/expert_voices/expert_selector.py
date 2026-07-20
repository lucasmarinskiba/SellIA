"""
Expert Selector - Intelligent Expert Voice Selection
Analyzes sales context and selects optimal expert(s) for maximum impact
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import asyncio

from prompt_registry import (
    ExpertType,
    SalesContext,
    EXPERT_METADATA,
    CONTEXT_RECOMMENDATIONS,
    get_best_experts_for_context
)


@dataclass
class SalesScenario:
    """Sales scenario for expert selection"""
    context: SalesContext
    customer_type: str  # "enterprise", "smb", "startup"
    objection_level: int  # 1-10
    deal_stage: str  # "awareness", "consideration", "decision"
    urgency: int  # 1-10
    customer_personality: str  # "analytical", "driver", "expressive", "amiable"
    price_sensitivity: int  # 1-10
    relationship_stage: str  # "cold", "warm", "established"
    competitive_pressure: int  # 1-10


@dataclass
class ExpertSelection:
    """Selected experts with reasoning"""
    primary_expert: ExpertType
    secondary_experts: List[ExpertType]
    reasoning: str
    scenario_fit_score: float
    recommended_tactics: List[str]


class ExpertSelector:
    """Intelligent expert selection engine"""

    def __init__(self):
        self.selection_history = []
        self.performance_data = {}

    async def select_experts(self, scenario: SalesScenario) -> ExpertSelection:
        """
        Select best experts for given sales scenario
        Uses multi-criteria evaluation
        """
        # Get initial candidates from context
        context_experts = CONTEXT_RECOMMENDATIONS.get(scenario.context, [])

        # Score each expert for this specific scenario
        expert_scores = {}
        for expert_type in context_experts:
            score = self._calculate_fit_score(expert_type, scenario)
            expert_scores[expert_type] = score

        # Sort by score
        sorted_experts = sorted(expert_scores.items(), key=lambda x: x[1], reverse=True)

        if not sorted_experts:
            # Fallback to generic expert selection
            sorted_experts = [(ExpertType.BELFORT, 0.5)]

        primary_expert = sorted_experts[0][0]
        secondary_experts = [e[0] for e in sorted_experts[1:3]]

        reasoning = self._generate_reasoning(primary_expert, scenario)
        tactics = self._extract_recommended_tactics(primary_expert, scenario)

        selection = ExpertSelection(
            primary_expert=primary_expert,
            secondary_experts=secondary_experts,
            reasoning=reasoning,
            scenario_fit_score=sorted_experts[0][1],
            recommended_tactics=tactics
        )

        # Log for performance tracking
        self.selection_history.append((scenario, selection))

        return selection

    def _calculate_fit_score(self, expert_type: ExpertType, scenario: SalesScenario) -> float:
        """
        Calculate how well expert fits scenario
        Uses 0-1 scale
        """
        score = 0.5  # Base score

        # Context fit (40% weight)
        if scenario.context in EXPERT_METADATA[expert_type].best_for:
            score += 0.4

        # Objection handling (15% weight)
        if scenario.objection_level > 5:
            if expert_type in [ExpertType.BELFORT, ExpertType.CARDONE, ExpertType.MINER]:
                score += 0.15

        # Deal stage fit (15% weight)
        if scenario.deal_stage == "decision":
            if expert_type in [ExpertType.BELFORT, ExpertType.CARDONE, ExpertType.TRUMP]:
                score += 0.15
        elif scenario.deal_stage == "awareness":
            if expert_type in [ExpertType.ELLIOTT, ExpertType.MINER, ExpertType.GARYVEE]:
                score += 0.15

        # Urgency fit (10% weight)
        if scenario.urgency > 7:
            if expert_type in [ExpertType.BELFORT, ExpertType.CARDONE, ExpertType.TRUMP]:
                score += 0.10

        # Customer personality fit (10% weight)
        if scenario.customer_personality == "analytical":
            if expert_type in [ExpertType.BUFFETT, ExpertType.DALIO, ExpertType.LOIDI]:
                score += 0.10
        elif scenario.customer_personality == "driver":
            if expert_type in [ExpertType.TRUMP, ExpertType.CARDONE, ExpertType.HORMOZI]:
                score += 0.10
        elif scenario.customer_personality == "expressive":
            if expert_type in [ExpertType.BELFORT, ExpertType.ROBBINS, ExpertType.GARYVEE]:
                score += 0.10
        elif scenario.customer_personality == "amiable":
            if expert_type in [ExpertType.MINER, ExpertType.RIBAS, ExpertType.ROBBINS]:
                score += 0.10

        # Price sensitivity fit (10% weight - conditional)
        if scenario.price_sensitivity > 7:
            if expert_type in [ExpertType.HORMOZI, ExpertType.KIYOSAKI, ExpertType.RAVIKANT]:
                score += 0.10
        elif scenario.price_sensitivity < 3:
            if expert_type in [ExpertType.TRUMP, ExpertType.BELFORT, ExpertType.CARDONE]:
                score += 0.10

        # Relationship stage fit (5% weight)
        if scenario.relationship_stage == "cold":
            if expert_type in [ExpertType.BELFORT, ExpertType.ELLIOTT]:
                score += 0.05
        elif scenario.relationship_stage == "established":
            if expert_type in [ExpertType.DALIO, ExpertType.BUFFETT, ExpertType.RIBAS]:
                score += 0.05

        # Competitive pressure fit (5% weight)
        if scenario.competitive_pressure > 7:
            if expert_type in [ExpertType.TRUMP, ExpertType.GARYVEE, ExpertType.CARDONE]:
                score += 0.05

        # Cap at 1.0
        return min(score, 1.0)

    def _generate_reasoning(self, expert_type: ExpertType, scenario: SalesScenario) -> str:
        """Generate reasoning for expert selection"""
        metadata = EXPERT_METADATA[expert_type]

        reasons = []

        # Context match
        if scenario.context in metadata.best_for:
            reasons.append(f"Excellent fit for {scenario.context.value} situations")

        # Deal stage
        if scenario.deal_stage == "decision" and expert_type in [
            ExpertType.BELFORT, ExpertType.CARDONE
        ]:
            reasons.append("Specializes in closing high-pressure decisions")

        # Objection level
        if scenario.objection_level > 6 and expert_type in [
            ExpertType.BELFORT, ExpertType.MINER
        ]:
            reasons.append("Expert in crushing objections and handling resistance")

        # Personality match
        if scenario.customer_personality == "analytical" and expert_type in [
            ExpertType.BUFFETT, ExpertType.DALIO
        ]:
            reasons.append("Matches analytical customer thinking style")

        # Urgency
        if scenario.urgency > 7 and expert_type in [ExpertType.BELFORT, ExpertType.CARDONE]:
            reasons.append("Specializes in high-urgency, time-pressured scenarios")

        if not reasons:
            reasons.append(f"Core expertise in {', '.join(metadata.primary_focus[:2])}")

        return ". ".join(reasons) + "."

    def _extract_recommended_tactics(
        self, expert_type: ExpertType, scenario: SalesScenario
    ) -> List[str]:
        """Extract recommended tactics for this expert in this scenario"""
        tactics = []

        expert_map = {
            ExpertType.TRUMP: [
                "Anchor aggressively at opening",
                "Establish dominance immediately",
                "Control the narrative",
                "Create perceived value through presentation"
            ],
            ExpertType.BELFORT: [
                "Keep conversation on straight line to close",
                "Build emotional connection",
                "Create urgency through scarcity",
                "Assumptive closing techniques"
            ],
            ExpertType.BUFFETT: [
                "Focus on long-term value creation",
                "Identify competitive advantages",
                "Emphasize margin of safety",
                "Let patience work in your favor"
            ],
            ExpertType.KIYOSAKI: [
                "Reframe around cash flow benefits",
                "Emphasize passive income potential",
                "Build wealth mindset messaging",
                "Show financial freedom angle"
            ],
            ExpertType.HORMOZI: [
                "Stack value in the offer design",
                "Optimize for customer acquisition cost",
                "Build compelling value proposition",
                "Create irresistible offer structure"
            ],
            ExpertType.CARDONE: [
                "Apply maximum closing pressure",
                "Create extreme urgency",
                "Push through all objections",
                "Volume and activity mindset"
            ],
            ExpertType.ROBBINS: [
                "Get prospect into peak state first",
                "Use NLP pacing and leading",
                "Create transformation narrative",
                "Build deep psychological connection"
            ],
            ExpertType.GARYVEE: [
                "Meet them on their platform",
                "Provide authentic value first",
                "Build attention through originality",
                "Play the long-term content game"
            ],
            ExpertType.DALIO: [
                "Apply principle-based thinking",
                "Radical transparency about challenges",
                "Systems and process orientation",
                "Adapt based on feedback loops"
            ],
            ExpertType.MINER: [
                "Deep discovery through expert listening",
                "Build genuine rapport first",
                "Find true underlying problems",
                "Create emotional connection"
            ],
            ExpertType.ELLIOTT: [
                "Lead with value messaging",
                "Establish clear positioning",
                "Build authority through education",
                "Differentiate on customer value"
            ],
            ExpertType.LOIDI: [
                "Focus on metrics and data",
                "Optimize customer acquisition",
                "Scale through proven systems",
                "Data-driven decision making"
            ],
            ExpertType.RIBAS: [
                "Build strong team alignment",
                "Create inclusive, empowering message",
                "Focus on sustainable growth",
                "Build community around solution"
            ],
            ExpertType.GALPERIN: [
                "Emphasize network effects",
                "Regional customization strategy",
                "Build long-term marketplace thinking",
                "Trust through execution excellence"
            ],
            ExpertType.ROCCA: [
                "Long-term value proposition",
                "Quality and sustainability focus",
                "Multi-stakeholder value creation",
                "Industrial thinking and patience"
            ],
            ExpertType.GALUCCIO: [
                "Navigate regulatory landscape",
                "Long-term transformation vision",
                "Manage political relationships",
                "Execute against strategic vision"
            ],
            ExpertType.RAVIKANT: [
                "Leverage creation and multiplication",
                "Wealth building framework",
                "First principles analysis",
                "Focus on leverage mechanisms"
            ],
            ExpertType.TALEB: [
                "Identify and manage tail risks",
                "Build optionality in offerings",
                "Antifragility mindset",
                "Skin in the game positioning"
            ],
            ExpertType.GRAHAM: [
                "Focus on real customer problems",
                "Ship and iterate quickly",
                "Do things that don't scale",
                "First principles product thinking"
            ],
            ExpertType.BENIOFF: [
                "Purpose-driven value message",
                "AI integration opportunities",
                "Social impact positioning",
                "Future-focused vision building"
            ]
        }

        base_tactics = expert_map.get(expert_type, [])

        # Filter tactics based on scenario
        if scenario.objection_level > 6:
            base_tactics = [t for t in base_tactics if "objection" in t.lower() or "crush" in t.lower()]

        if scenario.deal_stage == "decision":
            base_tactics = [t for t in base_tactics if "close" in t.lower() or "decision" in t.lower()]

        return base_tactics[:3] if base_tactics else ["Apply expert's core methodology"]

    def get_performance_analytics(self) -> Dict:
        """Get analytics on selection performance"""
        if not self.selection_history:
            return {"total_selections": 0}

        expert_usage = {}
        for scenario, selection in self.selection_history:
            expert = selection.primary_expert
            if expert not in expert_usage:
                expert_usage[expert] = 0
            expert_usage[expert] += 1

        return {
            "total_selections": len(self.selection_history),
            "expert_usage_distribution": {
                e.value: count for e, count in expert_usage.items()
            },
            "average_fit_score": sum(
                s.scenario_fit_score for _, s in self.selection_history
            ) / len(self.selection_history)
        }


async def demonstrate_selection():
    """Demonstrate expert selection"""
    selector = ExpertSelector()

    # Test scenario 1: High-pressure enterprise close
    scenario1 = SalesScenario(
        context=SalesContext.CLOSING,
        customer_type="enterprise",
        objection_level=8,
        deal_stage="decision",
        urgency=9,
        customer_personality="driver",
        price_sensitivity=3,
        relationship_stage="warm",
        competitive_pressure=9
    )

    selection1 = await selector.select_experts(scenario1)
    print(f"Scenario 1 - Enterprise Close:\n"
          f"  Primary: {selection1.primary_expert.value}\n"
          f"  Secondary: {[e.value for e in selection1.secondary_experts]}\n"
          f"  Fit Score: {selection1.scenario_fit_score:.2f}\n"
          f"  Reasoning: {selection1.reasoning}\n"
          f"  Tactics: {', '.join(selection1.recommended_tactics)}\n")

    # Test scenario 2: Building value for analytical customer
    scenario2 = SalesScenario(
        context=SalesContext.VALUE_PROPOSITION,
        customer_type="smb",
        objection_level=5,
        deal_stage="consideration",
        urgency=4,
        customer_personality="analytical",
        price_sensitivity=8,
        relationship_stage="cold",
        competitive_pressure=6
    )

    selection2 = await selector.select_experts(scenario2)
    print(f"Scenario 2 - Value Proposition (Analytical):\n"
          f"  Primary: {selection2.primary_expert.value}\n"
          f"  Secondary: {[e.value for e in selection2.secondary_experts]}\n"
          f"  Fit Score: {selection2.scenario_fit_score:.2f}\n"
          f"  Reasoning: {selection2.reasoning}\n")

    # Performance analytics
    analytics = selector.get_performance_analytics()
    print(f"\nPerformance Analytics:\n  {analytics}\n")


# Export main interface
__all__ = ["ExpertSelector", "SalesScenario", "ExpertSelection"]
