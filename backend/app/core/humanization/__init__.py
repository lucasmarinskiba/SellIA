"""
Phase 10: Humanization Module (3,500L)

Complete humanization system for 24/7 autonomous sales execution.

Components:
1. tone_engine.py (600L) — 10 communication tones across markets/industries
2. empathy_layer.py (400L) — Emotional detection and empathetic responses
3. personalization.py (400L) — Name, history, preferences, urgency
4. response_builder.py (400L) — Combines tone + empathy + personalization
5. a_b_testing.py (300L) — Tone variation testing and optimization
6. tests (400L) — Comprehensive test suite

Target: >90% of messages rated "sounds human" in user testing.

Key Features:
- 10 distinct tones (formal, casual, friendly, professional, cheeky, educational, urgent, luxe, discount, empathetic)
- Emotional state detection (confident, curious, hesitant, frustrated, skeptical, objecting, urgent, overwhelmed)
- Multi-market support (Latin America, Spain, Argentina, USA, UK)
- Multi-industry support (Real Estate, SaaS, E-commerce, Services)
- Deep personalization (name, company, role, purchase history, preferences)
- A/B testing framework for continuous optimization
- Humanness scoring and validation
- Platform-specific optimization (Email, WhatsApp, SMS, Instagram)
"""

from .tone_engine import (
    ToneEngine,
    ToneType,
    Market,
    Industry,
    ToneProfile,
)

from .empathy_layer import (
    EmpathyLayer,
    EmotionalState,
    EmpathyResponse,
    EmpathySignal,
)

from .personalization import (
    PersonalizationEngine,
    BuyerProfile,
    PersonalizationContext,
    PersonalizationLevel,
)

from .response_builder import (
    ResponseBuilder,
    CTAType,
    ResponseTemplate,
)

from .a_b_testing import (
    ABTestingEngine,
    ABTest,
    Variant,
    ExperimentType,
)

__all__ = [
    # Tone Engine
    "ToneEngine",
    "ToneType",
    "Market",
    "Industry",
    "ToneProfile",
    # Empathy Layer
    "EmpathyLayer",
    "EmotionalState",
    "EmpathyResponse",
    "EmpathySignal",
    # Personalization
    "PersonalizationEngine",
    "BuyerProfile",
    "PersonalizationContext",
    "PersonalizationLevel",
    # Response Builder
    "ResponseBuilder",
    "CTAType",
    "ResponseTemplate",
    # A/B Testing
    "ABTestingEngine",
    "ABTest",
    "Variant",
    "ExperimentType",
]


def create_humanizer() -> "HumanizationOrchestrator":
    """
    Factory function to create fully initialized humanizer.

    Returns:
        HumanizationOrchestrator with all systems ready
    """
    return HumanizationOrchestrator()


class HumanizationOrchestrator:
    """
    Master orchestrator that combines all humanization components.

    Usage:
        humanizer = HumanizationOrchestrator()
        response = humanizer.build_human_message(
            base_message="Check out our new product",
            buyer_profile=profile,
            market=Market.USA,
            industry=Industry.ECOMMERCE,
            language="en",
        )
    """

    def __init__(self):
        """Initialize all humanization components"""
        self.tone_engine = ToneEngine()
        self.empathy_layer = EmpathyLayer()
        self.personalization_engine = PersonalizationEngine()
        self.response_builder = ResponseBuilder()
        self.testing_engine = ABTestingEngine()

    def build_human_message(
        self,
        base_message: str,
        buyer_profile: "BuyerProfile",
        market: Market,
        industry: Industry,
        language: str = "en",
    ) -> dict:
        """
        Build complete human-sounding message.

        Flow:
        1. Detect buyer emotion
        2. Select appropriate tone
        3. Apply personalization
        4. Build response with CTA
        5. Validate output

        Args:
            base_message: Core message content
            buyer_profile: Buyer information
            market: Market/region
            industry: Industry type
            language: Language code

        Returns:
            Complete response with all components
        """
        # Detect emotion
        emotion = self.empathy_layer.detect_emotion(base_message, language)

        # Suggest tone
        tone_type = self.tone_engine.suggest_tone(
            buyer_sentiment="neutral",
            buyer_urgency="medium" if emotion.urgency_level >= 7 else "low",
            market=market,
            industry=industry,
        )

        # Get tone profile
        tone_profile = self.tone_engine.get_tone_profile(tone_type, market, industry)

        # Generate empathetic response
        empathy_response = self.empathy_layer.generate_empathetic_response(
            emotion,
            language,
            {"tone": tone_type.value},
        )

        # Personalize message
        context = PersonalizationContext(
            buyer_profile=buyer_profile,
            message_type="initial",
        )
        personalized = self.personalization_engine.personalize_message(
            base_message,
            buyer_profile,
            context,
            language,
        )

        # Build final response
        response = self.response_builder.build_response(
            base_message=personalized["personalized_message"],
            tone_type=tone_type.value,
            emotional_state=emotion.emotional_state.value,
            buyer_name=buyer_profile.first_name,
            cta_type=CTAType.SOFT,
            language=language,
        )

        # Validate
        validation = self.response_builder.validate_response(
            response["response"],
            tone_type.value,
            language,
        )

        return {
            "response": response["response"],
            "tone": tone_type.value,
            "emotional_context": emotion.emotional_state.value,
            "personalization_score": personalized["confidence"],
            "humanness_score": response["humanness_score"],
            "validation": validation,
            "is_ready_to_send": validation["is_valid"],
        }

    def measure_humanness(
        self,
        text: str,
        tone: str,
        language: str = "en",
    ) -> float:
        """
        Measure how human a message sounds (0-1).

        Returns:
            Humanness score
        """
        return self.response_builder._calculate_humanness(text, tone, language)
