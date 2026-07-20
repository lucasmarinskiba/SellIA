"""
Expert Orchestrator - Execute Expert Voice Prompts
Orchestrates expert selection and prompt execution for sales conversations
Production-ready implementation with async support
"""

from typing import Optional, Dict, List, Any, Callable, AsyncGenerator
from dataclasses import dataclass
from enum import Enum
import asyncio
import json
from datetime import datetime

from prompt_registry import ExpertType, SalesContext
from expert_selector import ExpertSelector, SalesScenario, ExpertSelection


@dataclass
class PromptExecutionContext:
    """Context for prompt execution"""
    scenario: SalesScenario
    expert_selection: ExpertSelection
    customer_message: str
    conversation_history: List[Dict[str, str]]
    additional_context: Dict[str, Any]
    timestamp: datetime


@dataclass
class PromptExecutionResult:
    """Result of prompt execution"""
    expert_type: ExpertType
    expert_voice: str
    suggested_response: str
    tactical_approach: str
    success_metrics: List[str]
    confidence_score: float
    execution_time_ms: float
    metadata: Dict[str, Any]


class PromptExecutionMode(Enum):
    """How to execute the prompt"""
    PURE_VOICE = "pure_voice"  # Use expert voice directly
    HYBRID = "hybrid"  # Mix expert voice with brand voice
    FRAMEWORK_ONLY = "framework_only"  # Just the tactical framework


class ExpertOrchestrator:
    """
    Production orchestrator for expert voice execution
    Handles: selection, execution, validation, feedback
    """

    def __init__(self, execution_mode: PromptExecutionMode = PromptExecutionMode.HYBRID):
        self.selector = ExpertSelector()
        self.execution_mode = execution_mode
        self.execution_history = []
        self.performance_metrics = {}

    async def execute_expert_prompt(
        self,
        scenario: SalesScenario,
        customer_message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> PromptExecutionResult:
        """
        Execute expert prompt for sales situation
        Returns actionable response in expert voice
        """
        start_time = datetime.now()

        # Set defaults
        if conversation_history is None:
            conversation_history = []
        if additional_context is None:
            additional_context = {}

        try:
            # Step 1: Select best expert(s)
            expert_selection = await self.selector.select_experts(scenario)

            # Step 2: Build execution context
            context = PromptExecutionContext(
                scenario=scenario,
                expert_selection=expert_selection,
                customer_message=customer_message,
                conversation_history=conversation_history,
                additional_context=additional_context,
                timestamp=datetime.now()
            )

            # Step 3: Execute prompt
            result = await self._execute_prompt_internal(context)

            # Step 4: Measure execution
            execution_time_ms = (datetime.now() - start_time).total_seconds() * 1000

            # Step 5: Log execution
            self._log_execution(context, result, execution_time_ms)

            # Add timing to result
            result.execution_time_ms = execution_time_ms

            return result

        except Exception as e:
            raise PromptExecutionError(f"Failed to execute expert prompt: {str(e)}")

    async def _execute_prompt_internal(self, context: PromptExecutionContext) -> PromptExecutionResult:
        """Internal prompt execution"""

        expert_type = context.expert_selection.primary_expert
        tactics = context.expert_selection.recommended_tactics

        # Build the response based on expert and situation
        expert_voice = self._generate_expert_voice(expert_type, context)
        tactical_approach = self._build_tactical_response(expert_type, tactics, context)
        success_metrics = self._extract_success_metrics(expert_type, context)

        # Build suggested response
        if self.execution_mode == PromptExecutionMode.PURE_VOICE:
            suggested_response = expert_voice
        elif self.execution_mode == PromptExecutionMode.FRAMEWORK_ONLY:
            suggested_response = tactical_approach
        else:  # HYBRID
            suggested_response = self._hybrid_voice(expert_voice, tactical_approach, expert_type)

        # Calculate confidence score
        confidence_score = min(
            context.expert_selection.scenario_fit_score,
            1.0
        )

        # Build metadata
        metadata = {
            "expert_type": expert_type.value,
            "scenario_context": context.scenario.context.value,
            "customer_type": context.scenario.customer_type,
            "deal_stage": context.scenario.deal_stage,
            "conversation_turns": len(context.conversation_history),
            "secondary_experts": [e.value for e in context.expert_selection.secondary_experts],
            "reasoning": context.expert_selection.reasoning
        }

        return PromptExecutionResult(
            expert_type=expert_type,
            expert_voice=expert_voice,
            suggested_response=suggested_response,
            tactical_approach=tactical_approach,
            success_metrics=success_metrics,
            confidence_score=confidence_score,
            execution_time_ms=0,  # Will be set by caller
            metadata=metadata
        )

    def _generate_expert_voice(self, expert_type: ExpertType, context: PromptExecutionContext) -> str:
        """Generate response in expert's voice"""

        expert_voices = {
            ExpertType.TRUMP: self._trump_voice,
            ExpertType.BELFORT: self._belfort_voice,
            ExpertType.BUFFETT: self._buffett_voice,
            ExpertType.KIYOSAKI: self._kiyosaki_voice,
            ExpertType.HORMOZI: self._hormozi_voice,
            ExpertType.CARDONE: self._cardone_voice,
            ExpertType.ROBBINS: self._robbins_voice,
            ExpertType.GARYVEE: self._garyvee_voice,
            ExpertType.DALIO: self._dalio_voice,
            ExpertType.MINER: self._miner_voice,
            ExpertType.ELLIOTT: self._elliott_voice,
            ExpertType.LOIDI: self._loidi_voice,
            ExpertType.RIBAS: self._ribas_voice,
            ExpertType.GALPERIN: self._galperin_voice,
            ExpertType.ROCCA: self._rocca_voice,
            ExpertType.GALUCCIO: self._galuccio_voice,
            ExpertType.RAVIKANT: self._ravikant_voice,
            ExpertType.TALEB: self._taleb_voice,
            ExpertType.GRAHAM: self._graham_voice,
            ExpertType.BENIOFF: self._benioff_voice,
        }

        voice_generator = expert_voices.get(expert_type)
        if voice_generator:
            return voice_generator(context)
        return "Apply expert methodology to situation"

    def _build_tactical_response(
        self, expert_type: ExpertType, tactics: List[str], context: PromptExecutionContext
    ) -> str:
        """Build tactical approach for expert"""
        lines = ["TACTICAL APPROACH:", ""]

        for i, tactic in enumerate(tactics, 1):
            lines.append(f"{i}. {tactic}")

        return "\n".join(lines)

    def _extract_success_metrics(
        self, expert_type: ExpertType, context: PromptExecutionContext
    ) -> List[str]:
        """Extract success metrics for this situation"""

        default_metrics = [
            "Customer moves to next stage of buying process",
            "No additional objections raised",
            "Explicit commitment to next step obtained",
            "Customer tonality becomes more positive"
        ]

        # Context-specific metrics
        if context.scenario.deal_stage == "decision":
            return [
                "Verbal or written commitment secured",
                "Deal closes within 48 hours",
                "Customer stops comparing alternatives"
            ]
        elif context.scenario.deal_stage == "consideration":
            return [
                "Customer requests product demo",
                "Customer asks implementation questions",
                "Customer mentions specific use cases"
            ]
        else:  # awareness
            return [
                "Customer shows high engagement",
                "Customer asks discovery questions",
                "Customer schedules follow-up meeting"
            ]

    def _hybrid_voice(self, expert_voice: str, tactical: str, expert_type: ExpertType) -> str:
        """Mix expert voice with tactical approach"""
        return f"{expert_voice}\n\n{tactical}"

    # Expert voice generators (simplified for production)
    def _trump_voice(self, context: PromptExecutionContext) -> str:
        return "You need to control this negotiation from the start. Set the terms, anchor high, and make them react to YOUR number instead of offering theirs. That's dealmaking 101."

    def _belfort_voice(self, context: PromptExecutionContext) -> str:
        return "Keep them on the straight line toward yes. When they object, don't defend—isolate. Find out what the REAL objection is, then move right back to the close. Energy is everything."

    def _buffett_voice(self, context: PromptExecutionContext) -> str:
        return "Focus on the long-term value creation. What's the competitive advantage? What's your margin of safety? Price is secondary to value. Patience is your weapon."

    def _kiyosaki_voice(self, context: PromptExecutionContext) -> str:
        return "This is about building their wealth mindset. Show them the cash flow benefits, the passive income potential, the financial freedom angle. Money follows mindset."

    def _hormozi_voice(self, context: PromptExecutionContext) -> str:
        return "The offer is the business. Stack value relentlessly. What can you add that costs you nothing but looks like gold to them? That's irresistibility."

    def _cardone_voice(self, context: PromptExecutionContext) -> str:
        return "This deal closes NOW. Apply maximum pressure on all fronts. Create urgency, create scarcity, create fear of loss. 10X the normal intensity."

    def _robbins_voice(self, context: PromptExecutionContext) -> str:
        return "Get them into a peak state first. Use NLP. Paint a vivid picture of their transformation. Make them FEEL the success before they agree to it."

    def _garyvee_voice(self, context: PromptExecutionContext) -> str:
        return "Meet them where they are. Provide value upfront, no strings attached. Build attention through authenticity. Play the long game, not the short sale."

    def _dalio_voice(self, context: PromptExecutionContext) -> str:
        return "Radical transparency about what's happening. Use principles-based thinking. Adapt based on feedback. Systems thinking beats individual brilliance."

    def _miner_voice(self, context: PromptExecutionContext) -> str:
        return "Forget selling—focus on discovering. Listen 70% of the time. Find their real problem underneath the stated one. Connection before transaction."

    def _elliott_voice(self, context: PromptExecutionContext) -> str:
        return "Lead with value messaging. Position clearly against competitors. Your authority comes from education, not claims. Customers buy improved positions, not features."

    def _loidi_voice(self, context: PromptExecutionContext) -> str:
        return "What gets measured gets managed. Focus on unit economics and customer acquisition cost. Data beats intuition every single time."

    def _ribas_voice(self, context: PromptExecutionContext) -> str:
        return "Build real teams and communities. Leadership isn't position—it's impact. Sustainable growth requires inclusive thinking. People first, always."

    def _galperin_voice(self, context: PromptExecutionContext) -> str:
        return "Think marketplace economics. Network effects matter. Execute with excellence. Regional customization is key. Long-term thinking creates defensible advantages."

    def _rocca_voice(self, context: PromptExecutionContext) -> str:
        return "This is decades-long thinking, not quarterly. Quality never compromises. Stakeholder value extends beyond shareholders. That's how empires are built."

    def _galuccio_voice(self, context: PromptExecutionContext) -> str:
        return "Understand the regulatory and political landscape. Transformation requires vision AND execution. Long-term strategic patience with short-term intensity."

    def _ravikant_voice(self, context: PromptExecutionContext) -> str:
        return "Identify the leverage—is it technology, products, or capital? Leverage multiplies effort. Create systems that work at scale. That's how you build wealth."

    def _taleb_voice(self, context: PromptExecutionContext) -> str:
        return "Identify tail risks and opportunities. Build optionality into your offers. Antifragility beats fragility. Skin in the game shows you believe in it."

    def _graham_voice(self, context: PromptExecutionContext) -> str:
        return "Do things that don't scale. Build something people genuinely want. Ship fast, iterate faster. Focus beats everything else."

    def _benioff_voice(self, context: PromptExecutionContext) -> str:
        return "Lead with purpose and impact. AI is reshaping everything—position accordingly. Future-focused thinking attracts future customers."

    def _log_execution(
        self, context: PromptExecutionContext, result: PromptExecutionResult, execution_time_ms: float
    ):
        """Log execution for analytics"""
        log_entry = {
            "timestamp": context.timestamp.isoformat(),
            "expert_type": context.expert_selection.primary_expert.value,
            "scenario": context.scenario.context.value,
            "execution_time_ms": execution_time_ms,
            "confidence_score": result.confidence_score
        }
        self.execution_history.append(log_entry)

    def get_execution_analytics(self) -> Dict[str, Any]:
        """Get analytics on executions"""
        if not self.execution_history:
            return {"total_executions": 0}

        expert_usage = {}
        total_time = 0
        for log in self.execution_history:
            expert = log["expert_type"]
            expert_usage[expert] = expert_usage.get(expert, 0) + 1
            total_time += log["execution_time_ms"]

        return {
            "total_executions": len(self.execution_history),
            "expert_usage": expert_usage,
            "average_execution_time_ms": total_time / len(self.execution_history),
            "average_confidence": sum(
                log["confidence_score"] for log in self.execution_history
            ) / len(self.execution_history)
        }


class PromptExecutionError(Exception):
    """Error during prompt execution"""
    pass


async def demonstrate_orchestration():
    """Demonstrate orchestrator functionality"""
    orchestrator = ExpertOrchestrator(execution_mode=PromptExecutionMode.HYBRID)

    # Create a sales scenario
    scenario = SalesScenario(
        context=SalesContext.CLOSING,
        customer_type="enterprise",
        objection_level=7,
        deal_stage="decision",
        urgency=8,
        customer_personality="driver",
        price_sensitivity=4,
        relationship_stage="warm",
        competitive_pressure=8
    )

    # Execute prompt
    result = await orchestrator.execute_expert_prompt(
        scenario=scenario,
        customer_message="I think your price is still too high compared to alternatives",
        conversation_history=[
            {"role": "customer", "content": "Tell me more about ROI"},
            {"role": "sales", "content": "Here's how we deliver 3x ROI in 12 months..."}
        ],
        additional_context={
            "company_revenue": "10M",
            "key_pain_point": "operational_efficiency"
        }
    )

    print(f"ORCHESTRATION RESULT")
    print(f"=" * 50)
    print(f"Expert Selected: {result.expert_type.value}")
    print(f"Confidence Score: {result.confidence_score:.2f}")
    print(f"Execution Time: {result.execution_time_ms:.2f}ms")
    print(f"\nEXPERT VOICE:")
    print(f"{result.expert_voice}")
    print(f"\nTACTICAL APPROACH:")
    print(f"{result.tactical_approach}")
    print(f"\nSUCCESS METRICS:")
    for metric in result.success_metrics:
        print(f"  - {metric}")
    print(f"\nMETADATA:")
    print(f"  {result.metadata}")

    # Analytics
    analytics = orchestrator.get_execution_analytics()
    print(f"\nANALYTICS:")
    print(f"  Total Executions: {analytics['total_executions']}")
    print(f"  Avg Execution Time: {analytics['average_execution_time_ms']:.2f}ms")


# Export main interface
__all__ = [
    "ExpertOrchestrator",
    "PromptExecutionContext",
    "PromptExecutionResult",
    "PromptExecutionMode",
    "PromptExecutionError"
]


# If run directly, demonstrate functionality
if __name__ == "__main__":
    asyncio.run(demonstrate_orchestration())
