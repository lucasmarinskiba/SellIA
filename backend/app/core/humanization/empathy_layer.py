"""
Phase 10: Humanization — Empathy Layer (400L)

Detects buyer emotions and responds with appropriate empathy:
- Objection handling (acknowledges concern, provides reassurance)
- Urgency detection (recognizes time pressure, validates fears)
- Indecision support (helps with decision-making, removes friction)
- Frustration response (validates emotion, offers solutions)
- Skepticism management (builds trust, provides proof)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class EmotionalState(str, Enum):
    """Detected buyer emotional states"""
    CONFIDENT = "confident"  # Ready to buy
    CURIOUS = "curious"  # Exploring options
    HESITANT = "hesitant"  # Unsure about decision
    FRUSTRATED = "frustrated"  # Pain point triggered
    SKEPTICAL = "skeptical"  # Doubts about offer
    OBJECTING = "objecting"  # Active resistance
    URGENT = "urgent"  # Time pressure
    OVERWHELMED = "overwhelmed"  # Too many options


class EmpathyResponse(str, Enum):
    """Types of empathetic responses"""
    VALIDATE = "validate"  # Acknowledge emotion
    CLARIFY = "clarify"  # Ask clarifying questions
    REASSURE = "reassure"  # Provide confidence
    EDUCATE = "educate"  # Share knowledge
    OFFER_SOLUTION = "offer_solution"  # Propose fix
    BUILD_TRUST = "build_trust"  # Prove credibility
    LIGHTEN = "lighten"  # Add humor/lightness
    LISTEN = "listen"  # Show you understand


@dataclass
class EmpathySignal:
    """Detected emotional signal in buyer communication"""
    emotional_state: EmotionalState
    trigger_words: List[str] = field(default_factory=list)
    confidence: float = 0.8
    urgency_level: int = 5  # 1-10
    detected_at: datetime = field(default_factory=datetime.utcnow)
    raw_context: str = ""


@dataclass
class EmpathyScript:
    """Template for empathetic response"""
    emotional_state: EmotionalState
    response_type: EmpathyResponse
    templates: List[str] = field(default_factory=list)
    follow_up_action: Optional[str] = None


class EmpathyLayer:
    """Detects and responds to buyer emotions with empathy."""

    # EMOTION DETECTION SIGNALS
    CONFIDENCE_SIGNALS = {
        "en": ["ready to buy", "let's do it", "when can you", "how much", "sign me up"],
        "es": ["listo para comprar", "vamos", "cuándo puedes", "cuánto cuesta", "inscríbeme"],
    }

    CURIOUS_SIGNALS = {
        "en": ["tell me more", "how does it", "what about", "can you explain", "interested"],
        "es": ["cuéntame más", "cómo funciona", "qué tal si", "puedes explicar", "interesado"],
    }

    HESITANT_SIGNALS = {
        "en": ["not sure", "let me think", "i need to", "maybe later", "still considering"],
        "es": ["no estoy seguro", "déjame pensar", "necesito", "quizás después", "aún considerando"],
    }

    FRUSTRATED_SIGNALS = {
        "en": ["frustrated", "annoyed", "fed up", "tired of", "doesn't work", "problem"],
        "es": ["frustrado", "molesto", "harto", "cansado de", "no funciona", "problema"],
    }

    SKEPTICAL_SIGNALS = {
        "en": ["sounds too good", "don't believe", "seems fake", "proof", "guarantee"],
        "es": ["suena demasiado bien", "no creo", "parece falso", "prueba", "garantía"],
    }

    OBJECTION_SIGNALS = {
        "en": ["but", "however", "problem is", "concern", "issue", "won't work"],
        "es": ["pero", "sin embargo", "el problema es", "preocupación", "problema", "no funcionará"],
    }

    URGENT_SIGNALS = {
        "en": ["asap", "urgent", "today", "today only", "limited time", "last chance"],
        "es": ["lo antes posible", "urgente", "hoy", "solo hoy", "tiempo limitado", "última oportunidad"],
    }

    OVERWHELMED_SIGNALS = {
        "en": ["too much", "options", "confused", "hard to choose", "information overload"],
        "es": ["demasiado", "opciones", "confundido", "difícil elegir", "sobrecarga de información"],
    }

    # EMPATHETIC RESPONSE TEMPLATES
    VALIDATION_TEMPLATES = {
        "en": [
            "I totally get that feeling.",
            "That's a completely valid concern.",
            "Your hesitation makes sense.",
            "I understand your perspective.",
            "That's a fair point to consider.",
        ],
        "es": [
            "Totalmente entiendo esa sensación.",
            "Es una preocupación completamente válida.",
            "Tu hesitación tiene sentido.",
            "Entiendo tu perspectiva.",
            "Es un punto justo a considerar.",
        ],
    }

    REASSURANCE_TEMPLATES = {
        "en": [
            "Here's what puts most people at ease...",
            "Let me show you how we've solved this for others...",
            "The good news is...",
            "You're in good hands with...",
            "This is actually less risky than you might think...",
        ],
        "es": [
            "Esto es lo que tranquiliza a la mayoría...",
            "Déjame mostrarte cómo lo hemos resuelto para otros...",
            "La buena noticia es...",
            "Estás en buenas manos con...",
            "Esto es en realidad menos arriesgado de lo que podrías pensar...",
        ],
    }

    CLARIFICATION_TEMPLATES = {
        "en": [
            "Help me understand what's most important to you...",
            "To better address your concern, can you tell me...",
            "I want to make sure I get this right. You're saying...",
            "So if I'm hearing you correctly...",
            "What would it take to make this work for you?",
        ],
        "es": [
            "Ayúdame a entender qué es más importante para ti...",
            "Para abordar mejor tu preocupación, ¿puedes decirme...",
            "Quiero asegurarme de entender. Dices que...",
            "Entonces, si te estoy escuchando correctamente...",
            "¿Qué se necesitaría para que esto funcione para ti?",
        ],
    }

    TRUST_BUILDING_TEMPLATES = {
        "en": [
            "We've helped over {number} customers with similar concerns.",
            "Here are {count} case studies from businesses like yours...",
            "We're trusted by {companies}...",
            "Our satisfaction guarantee means...",
            "We've been doing this since {year}...",
        ],
        "es": [
            "Hemos ayudado a más de {number} clientes con preocupaciones similares.",
            "Aquí hay {count} estudios de casos de empresas como la tuya...",
            "Somos de confianza para {companies}...",
            "Nuestra garantía de satisfacción significa...",
            "Llevamos haciendo esto desde {year}...",
        ],
    }

    # Solution offering templates
    SOLUTION_TEMPLATES = {
        "en": [
            "Here's exactly how we'd solve this...",
            "What if we approached it this way...",
            "I have an idea that might work...",
            "Most clients in your situation go with...",
            "The quickest solution would be...",
        ],
        "es": [
            "Así es exactamente como lo resolveríamos...",
            "¿Qué tal si lo abordamos de esta forma...",
            "Tengo una idea que podría funcionar...",
            "La mayoría de clientes en tu situación eligen...",
            "La solución más rápida sería...",
        ],
    }

    # Lighten the mood templates
    LIGHTEN_TEMPLATES = {
        "en": [
            "Don't worry, we make this super easy.",
            "Here's the good news — we handle all the hard part.",
            "You're overthinking this (and that's okay!).",
            "This is honestly simpler than it sounds.",
            "The best part? You don't need to do much.",
        ],
        "es": [
            "No te preocupes, hacemos esto muy fácil.",
            "Aquí está la buena noticia — nosotros manejamos la parte difícil.",
            "Estás pensando demasiado en esto (¡y está bien!).",
            "Esto es honestamente más simple de lo que suena.",
            "¿La mejor parte? No necesitas hacer mucho.",
        ],
    }

    def __init__(self):
        """Initialize empathy layer"""
        logger.info("EmpathyLayer initialized")

    def detect_emotion(
        self,
        text: str,
        language: str = "en",
    ) -> EmpathySignal:
        """
        Detect buyer emotional state from text.

        Args:
            text: Buyer message
            language: Language code (en, es)

        Returns:
            EmpathySignal with detected emotion and confidence
        """
        text_lower = text.lower()

        # Check confidence
        confidence_matches = sum(
            1 for signal in self.CONFIDENCE_SIGNALS.get(language, [])
            if signal in text_lower
        )
        if confidence_matches > 0:
            return EmpathySignal(
                emotional_state=EmotionalState.CONFIDENT,
                trigger_words=[s for s in self.CONFIDENCE_SIGNALS.get(language, []) if s in text_lower],
                confidence=0.9,
                urgency_level=2,
                raw_context=text[:100],
            )

        # Check curious
        curious_matches = sum(
            1 for signal in self.CURIOUS_SIGNALS.get(language, [])
            if signal in text_lower
        )
        if curious_matches > 0:
            return EmpathySignal(
                emotional_state=EmotionalState.CURIOUS,
                trigger_words=[s for s in self.CURIOUS_SIGNALS.get(language, []) if s in text_lower],
                confidence=0.85,
                urgency_level=3,
                raw_context=text[:100],
            )

        # Check hesitant
        hesitant_matches = sum(
            1 for signal in self.HESITANT_SIGNALS.get(language, [])
            if signal in text_lower
        )
        if hesitant_matches > 0:
            return EmpathySignal(
                emotional_state=EmotionalState.HESITANT,
                trigger_words=[s for s in self.HESITANT_SIGNALS.get(language, []) if s in text_lower],
                confidence=0.8,
                urgency_level=6,
                raw_context=text[:100],
            )

        # Check frustrated
        frustrated_matches = sum(
            1 for signal in self.FRUSTRATED_SIGNALS.get(language, [])
            if signal in text_lower
        )
        if frustrated_matches > 0:
            return EmpathySignal(
                emotional_state=EmotionalState.FRUSTRATED,
                trigger_words=[s for s in self.FRUSTRATED_SIGNALS.get(language, []) if s in text_lower],
                confidence=0.85,
                urgency_level=7,
                raw_context=text[:100],
            )

        # Check skeptical
        skeptical_matches = sum(
            1 for signal in self.SKEPTICAL_SIGNALS.get(language, [])
            if signal in text_lower
        )
        if skeptical_matches > 0:
            return EmpathySignal(
                emotional_state=EmotionalState.SKEPTICAL,
                trigger_words=[s for s in self.SKEPTICAL_SIGNALS.get(language, []) if s in text_lower],
                confidence=0.8,
                urgency_level=5,
                raw_context=text[:100],
            )

        # Check objections
        objection_matches = sum(
            1 for signal in self.OBJECTION_SIGNALS.get(language, [])
            if signal in text_lower
        )
        if objection_matches > 0:
            return EmpathySignal(
                emotional_state=EmotionalState.OBJECTING,
                trigger_words=[s for s in self.OBJECTION_SIGNALS.get(language, []) if s in text_lower],
                confidence=0.82,
                urgency_level=7,
                raw_context=text[:100],
            )

        # Check urgent
        urgent_matches = sum(
            1 for signal in self.URGENT_SIGNALS.get(language, [])
            if signal in text_lower
        )
        if urgent_matches > 0:
            return EmpathySignal(
                emotional_state=EmotionalState.URGENT,
                trigger_words=[s for s in self.URGENT_SIGNALS.get(language, []) if s in text_lower],
                confidence=0.88,
                urgency_level=9,
                raw_context=text[:100],
            )

        # Check overwhelmed
        overwhelmed_matches = sum(
            1 for signal in self.OVERWHELMED_SIGNALS.get(language, [])
            if signal in text_lower
        )
        if overwhelmed_matches > 0:
            return EmpathySignal(
                emotional_state=EmotionalState.OVERWHELMED,
                trigger_words=[s for s in self.OVERWHELMED_SIGNALS.get(language, []) if s in text_lower],
                confidence=0.8,
                urgency_level=6,
                raw_context=text[:100],
            )

        # Default: neutral/curious
        return EmpathySignal(
            emotional_state=EmotionalState.CURIOUS,
            trigger_words=[],
            confidence=0.5,
            urgency_level=4,
            raw_context=text[:100],
        )

    def generate_empathetic_response(
        self,
        emotional_signal: EmpathySignal,
        language: str = "en",
        buyer_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate empathetic response based on emotional state.

        Args:
            emotional_signal: Detected emotion
            language: Language code
            buyer_context: Additional context (objection, concern, etc.)

        Returns:
            {
                "response": str,
                "emotional_state": str,
                "response_type": str,
                "confidence": float,
                "next_action": str,
            }
        """
        buyer_context = buyer_context or {}

        # Route to appropriate response
        if emotional_signal.emotional_state == EmotionalState.CONFIDENT:
            response_type = EmpathyResponse.LIGHTEN
            templates = self.LIGHTEN_TEMPLATES.get(language, self.LIGHTEN_TEMPLATES["en"])
            next_action = "Move to closing"

        elif emotional_signal.emotional_state == EmotionalState.CURIOUS:
            response_type = EmpathyResponse.EDUCATE
            templates = self.SOLUTION_TEMPLATES.get(language, self.SOLUTION_TEMPLATES["en"])
            next_action = "Provide more info"

        elif emotional_signal.emotional_state == EmotionalState.HESITANT:
            response_type = EmpathyResponse.VALIDATE
            templates = self.VALIDATION_TEMPLATES.get(language, self.VALIDATION_TEMPLATES["en"])
            next_action = "Ask clarifying questions"

        elif emotional_signal.emotional_state == EmotionalState.FRUSTRATED:
            response_type = EmpathyResponse.VALIDATE
            templates = self.VALIDATION_TEMPLATES.get(language, self.VALIDATION_TEMPLATES["en"])
            next_action = "Offer immediate solution"

        elif emotional_signal.emotional_state == EmotionalState.SKEPTICAL:
            response_type = EmpathyResponse.BUILD_TRUST
            templates = self.TRUST_BUILDING_TEMPLATES.get(language, self.TRUST_BUILDING_TEMPLATES["en"])
            next_action = "Provide proof/credentials"

        elif emotional_signal.emotional_state == EmotionalState.OBJECTING:
            response_type = EmpathyResponse.CLARIFY
            templates = self.CLARIFICATION_TEMPLATES.get(language, self.CLARIFICATION_TEMPLATES["en"])
            next_action = "Address specific objection"

        elif emotional_signal.emotional_state == EmotionalState.URGENT:
            response_type = EmpathyResponse.OFFER_SOLUTION
            templates = self.SOLUTION_TEMPLATES.get(language, self.SOLUTION_TEMPLATES["en"])
            next_action = "Fast-track to decision"

        elif emotional_signal.emotional_state == EmotionalState.OVERWHELMED:
            response_type = EmpathyResponse.CLARIFY
            templates = self.CLARIFICATION_TEMPLATES.get(language, self.CLARIFICATION_TEMPLATES["en"])
            next_action = "Simplify options"

        else:
            response_type = EmpathyResponse.LIGHTEN
            templates = self.LIGHTEN_TEMPLATES.get(language, self.LIGHTEN_TEMPLATES["en"])
            next_action = "Continue conversation"

        # Select template
        from random import choice
        response = choice(templates)

        return {
            "response": response,
            "emotional_state": emotional_signal.emotional_state.value,
            "response_type": response_type.value,
            "confidence": emotional_signal.confidence,
            "urgency_level": emotional_signal.urgency_level,
            "next_action": next_action,
            "trigger_words": emotional_signal.trigger_words,
        }

    def handle_objection(
        self,
        objection: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Handle specific objections with empathy.

        Common objections:
        - "Too expensive" → value argument
        - "Need to think about it" → scarcity/urgency
        - "Already using competitor" → differentiation
        - "No time now" → time-saving benefits
        """
        objection_lower = objection.lower()

        # Map objections to responses
        if any(word in objection_lower for word in ["expensive", "expensive", "expensive", "price"]):
            if language == "es":
                response = "Entiendo tu preocupación sobre el precio. Piensa en esto como una inversión que se paga por sí sola en {timeframe}."
            else:
                response = "I get it — price matters. Think of this as an investment that pays for itself in {timeframe}."
            objection_type = "price"

        elif any(word in objection_lower for word in ["think", "let me think", "consider", "consider"]):
            if language == "es":
                response = "Claro, tómate tu tiempo. Aquí está el detalle: los mejores clientes actúan rápido. Te dejo este acceso especial por {duration}."
            else:
                response = "Of course, take your time. Here's the thing: best clients usually move fast. I'll hold this special offer for {duration}."
            objection_type = "hesitation"

        elif any(word in objection_lower for word in ["competitor", "already", "use", "using"]):
            if language == "es":
                response = "Interesante — muchos clientes nuestros antes usaban {competitor}. La diferencia clave es {differentiation}."
            else:
                response = "I hear you — many of our best customers used {competitor} first. Here's the key difference: {differentiation}."
            objection_type = "competitor"

        elif any(word in objection_lower for word in ["time", "busy", "no time", "can't"]):
            if language == "es":
                response = "Totalmente entiendo. Por eso nuestro sistema ahorra exactamente {time_saved} de tu tiempo cada semana."
            else:
                response = "Totally get it. That's exactly why our system saves {time_saved} of your time every week."
            objection_type = "time"

        else:
            if language == "es":
                response = "Entiendo tu preocupación. ¿Qué es lo que más te preocupa específicamente?"
            else:
                response = "I understand your concern. What's the main thing holding you back?"
            objection_type = "unknown"

        return {
            "response": response,
            "objection_type": objection_type,
            "confidence": 0.75,
            "requires_context": any(x in response for x in ["{", "}"]),
        }

    def build_urgency_empathetically(
        self,
        reason: str = "limited_spots",
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Create urgency without being pushy — respects buyer emotions.

        Reasons:
        - limited_spots: Only X slots left
        - time_limited: Offer expires soon
        - price_increase: Price goes up soon
        - stock_limited: Limited inventory

        Returns:
            Empathetic urgency message
        """
        if reason == "limited_spots":
            if language == "es":
                templates = [
                    "Solo quedan 2 espacios en esta cohorte. Muchos esperan hasta el último momento.",
                    "Tenemos capacidad limitada este mes. Si esperas, podría ser en {months}.",
                ]
            else:
                templates = [
                    "Only 2 spots left in this cohort. Most people wait until the last second.",
                    "We have limited capacity this month. If you wait, it'll be {months} before the next opening.",
                ]

        elif reason == "time_limited":
            if language == "es":
                templates = [
                    "Este precio especial termina en {time}. Después volverá al precio regular.",
                    "Estoy siendo transparente: este acceso vip expira en {date}.",
                ]
            else:
                templates = [
                    "This special pricing ends in {time}. After that, it's back to regular price.",
                    "Being transparent: this VIP access expires {date}.",
                ]

        elif reason == "price_increase":
            if language == "es":
                templates = [
                    "Solo te avisamos: el precio sube en {date}. Los que se deciden ahora ahorran {amount}.",
                    "Sin presión, pero: después de {date}, es {amount} más.",
                ]
            else:
                templates = [
                    "Just so you know: price increases on {date}. Everyone who decides now saves {amount}.",
                    "No pressure, but: after {date}, it's {amount} more.",
                ]

        elif reason == "stock_limited":
            if language == "es":
                templates = [
                    "Están a punto de agotarse. No quiero que te quedes sin tu opción.",
                    "Stock limitado en nuestro almacén. Si esperas, podría no disponible.",
                ]
            else:
                templates = [
                    "Stock is running low. I'd hate for you to miss out.",
                    "Limited inventory. If you wait, this might not be available.",
                ]

        else:
            templates = ["Espero que te unas pronto." if language == "es" else "Hope you join soon."]

        from random import choice
        message = choice(templates)

        return {
            "message": message,
            "urgency_type": reason,
            "tone": "urgent_but_respectful",
            "requires_context": any(x in message for x in ["{", "}"]),
        }
