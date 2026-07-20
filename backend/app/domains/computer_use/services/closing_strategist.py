"""Sales Closer — Master closing techniques from top entrepreneurs.

Strategist para cerrar ventas con técnicas probadas:
- Donald Trump: Directness, Scarcity, Power Position
- Alex Hormozi: Value Ladder, Urgency, Risk Reversal
- Russell Brunson: Story, Emotional Hooks, FOMO
- Gary Vee: Authenticity, Relationship, Long-term
- Tony Robbins: Pattern Interrupt, Emotional Reframe
"""

import logging
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ClosingTechnique(str, Enum):
    """Técnicas de cierre disponibles."""
    TRUMP_DIRECT = "trump_direct"  # Directness + confidence
    TRUMP_SCARCITY = "trump_scarcity"  # Limited time / limited quantity
    HORMOZI_VALUE_LADDER = "hormozi_value_ladder"  # Build value incrementally
    HORMOZI_URGENCY = "hormozi_urgency"  # Time constraint
    HORMOZI_RISK_REVERSAL = "hormozi_risk_reversal"  # Money-back guarantee
    BRUNSON_STORY = "brunson_story"  # Emotional narrative
    BRUNSON_FOMO = "brunson_fomo"  # Fear of missing out
    ROBBINS_PATTERN_INTERRUPT = "robbins_pattern_interrupt"  # Break state → action
    ROBBINS_EMOTIONAL_REFRAME = "robbins_emotional_reframe"  # Change perspective
    GARY_VEE_AUTHENTIC = "gary_vee_authentic"  # Real talk + relationship
    ASSUMPTIVE_CLOSE = "assumptive_close"  # Act like sale is done
    TAKE_IT_OR_LEAVE_IT = "take_it_or_leave_it"  # Final offer


class BuyerPersonality(str, Enum):
    """Tipología de comprador."""
    ANALYTICAL = "analytical"  # Data-driven, risk-averse
    DRIVER = "driver"  # Results-focused, impatient
    EXPRESSIVE = "expressive"  # Emotional, relationship-focused
    AMIABLE = "amiable"  # Harmony-seeking, consensus-builder


class SalesSignal:
    """Señal de compra detectada."""

    def __init__(self, signal_type: str, confidence: float, urgency_level: int = 1):
        self.signal_type = signal_type  # price_inquiry, timeline, objection_raised, etc
        self.confidence = confidence  # 0-1
        self.urgency_level = urgency_level  # 1-10
        self.detected_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal_type": self.signal_type,
            "confidence": self.confidence,
            "urgency_level": self.urgency_level,
            "detected_at": self.detected_at.isoformat(),
        }


class ClosingStrategist:
    """Strategist para cerrar ventas."""

    # Técnicas por personalidad de comprador
    TECHNIQUE_BY_PERSONALITY = {
        BuyerPersonality.ANALYTICAL: [
            ClosingTechnique.HORMOZI_RISK_REVERSAL,  # Remove risk
            ClosingTechnique.HORMOZI_VALUE_LADDER,  # Build case
            ClosingTechnique.TRUMP_DIRECT,  # Direct facts
        ],
        BuyerPersonality.DRIVER: [
            ClosingTechnique.TRUMP_SCARCITY,  # Limited time
            ClosingTechnique.HORMOZI_URGENCY,  # Act now
            ClosingTechnique.ROBBINS_PATTERN_INTERRUPT,  # Shock into action
        ],
        BuyerPersonality.EXPRESSIVE: [
            ClosingTechnique.BRUNSON_STORY,  # Emotional narrative
            ClosingTechnique.BRUNSON_FOMO,  # Others getting it
            ClosingTechnique.ROBBINS_EMOTIONAL_REFRAME,  # Feel better
        ],
        BuyerPersonality.AMIABLE: [
            ClosingTechnique.GARY_VEE_AUTHENTIC,  # Real talk
            ClosingTechnique.HORMOZI_VALUE_LADDER,  # Show care
            ClosingTechnique.ASSUMPTIVE_CLOSE,  # Gentle assumption
        ],
    }

    # Template de cierre por técnica
    CLOSING_TEMPLATES = {
        ClosingTechnique.TRUMP_DIRECT: """
You know what? This is exactly what you need. I've seen hundreds of people in your situation.
The ones who took action? They're killing it. The ones who waited? They're still stuck.

This offer ends {deadline}. Let's do this.
""",

        ClosingTechnique.TRUMP_SCARCITY: """
I've got {count} spots left. My best clients are already in.

I could hold one for you, but only if you decide today.

What do you say?
""",

        ClosingTechnique.HORMOZI_VALUE_LADDER: """
Look, I get it. Big decision.

Here's what we'll do:
1. {step1} - You'll see immediate value
2. {step2} - You'll make this back
3. {step3} - You'll be ahead

Start with step 1. Prove it to yourself.
""",

        ClosingTechnique.HORMOZI_URGENCY: """
I'm gonna be honest with you.

This price goes up {when}. Not trying to pressure you,
just giving you the facts.

If this is something you want, now's the time.
""",

        ClosingTechnique.HORMOZI_RISK_REVERSAL: """
Here's my promise: If you don't see {result} within {timeframe},
I'll give you your money back. No questions.

That's how confident I am.

Let's get started?
""",

        ClosingTechnique.BRUNSON_STORY: """
You remind me of my client {name}. She was in your exact position.
Skeptical, worried, wondering if this was real.

Then she took action. And {result}.

That could be your story.
""",

        ClosingTechnique.BRUNSON_FOMO: """
Honestly? I wasn't even going to tell you about this.

But I know you. You're someone who seizes opportunities.

My other clients already jumped on this.
And {result_example}.

You in?
""",

        ClosingTechnique.ROBBINS_PATTERN_INTERRUPT: """
STOP. Real talk for a second.

You came to me because you wanted change, right?

Change only happens when you make a decision.

This is that moment.

What's it gonna be?
""",

        ClosingTechnique.ROBBINS_EMOTIONAL_REFRAME: """
Forget about the money for a second. Think about how you'll FEEL
6 months from now if you did this.

Actually did it. Took action. Got results.

Now imagine if you don't.

Which version of you do you want to be?
""",

        ClosingTechnique.GARY_VEE_AUTHENTIC: """
I'm not gonna BS you. This isn't for everyone.

But I think it IS for you. And here's why: {reason}.

I genuinely believe you're gonna crush this.

Let's make it happen.
""",

        ClosingTechnique.ASSUMPTIVE_CLOSE: """
Awesome. So we're doing this.

Quick question for the paperwork: What's your best email?

I'm gonna send over the details in {time}.
""",

        ClosingTechnique.TAKE_IT_OR_LEAVE_IT: """
Here's the deal. Final offer.

{offer_summary}

Decision time. Yes or no?
""",
    }

    def __init__(self):
        self.logger = logger

    async def detect_closing_moment(
        self,
        conversation_history: List[Dict[str, str]],
        customer_profile: Dict[str, Any],
    ) -> tuple[bool, List[SalesSignal]]:
        """
        Detecta si es momento de cerrar.

        Retorna: (is_closing_moment, signals_detected)
        """
        signals = []

        if not conversation_history:
            return False, signals

        # Analizar últimos mensajes
        last_messages = conversation_history[-5:]
        combined_text = " ".join([msg.get("content", "").lower() for msg in last_messages])

        # SIGNAL 1: Pregunta de precio
        if any(word in combined_text for word in ["precio", "costo", "cuánto", "how much", "cost"]):
            signals.append(SalesSignal("price_inquiry", 0.9, urgency_level=8))

        # SIGNAL 2: Timeline mencionado
        if any(word in combined_text for word in ["cuándo", "when", "entrega", "delivery", "implementación"]):
            signals.append(SalesSignal("timeline_inquiry", 0.85, urgency_level=7))

        # SIGNAL 3: Objeción levantada (signo positivo = está considerando)
        if any(word in combined_text for word in ["pero", "pero", "sin embargo", "aunque", "mi preocupación"]):
            signals.append(SalesSignal("objection_raised", 0.8, urgency_level=9))

        # SIGNAL 4: Palabras de compromiso
        if any(word in combined_text for word in ["me interesa", "suena bien", "podríamos", "looks good"]):
            signals.append(SalesSignal("commitment_interest", 0.85, urgency_level=8))

        # SIGNAL 5: Multiple questions = high intent
        question_count = combined_text.count("?")
        if question_count >= 2:
            signals.append(SalesSignal("high_intent_questions", 0.7, urgency_level=7))

        # SIGNAL 6: Long messages = engaged
        avg_msg_length = sum(len(msg.get("content", "")) for msg in last_messages) / len(last_messages)
        if avg_msg_length > 100:
            signals.append(SalesSignal("high_engagement", 0.6, urgency_level=6))

        # CLOSING MOMENT: Si hay múltiples señales o al menos una fuerte
        is_moment = (
            len(signals) >= 2
            or any(s.urgency_level >= 8 for s in signals)
        )

        return is_moment, signals

    async def select_closing_technique(
        self,
        buyer_personality: Optional[BuyerPersonality] = None,
        signals: Optional[List[SalesSignal]] = None,
        product_type: Optional[str] = None,
    ) -> ClosingTechnique:
        """
        Selecciona técnica de cierre óptima.

        Considera: personalidad comprador, señales, tipo de producto.
        """
        signals = signals or []

        # Si personalidad no conocida → asumir driver (predeterminado)
        if not buyer_personality:
            buyer_personality = BuyerPersonality.DRIVER

        # Obtener técnicas candidatas por personalidad
        candidate_techniques = self.TECHNIQUE_BY_PERSONALITY.get(buyer_personality, [])

        # Si hay señal de urgencia alta → usar scarcity/urgency
        if any(s.urgency_level >= 9 for s in signals):
            if ClosingTechnique.TRUMP_SCARCITY in candidate_techniques:
                return ClosingTechnique.TRUMP_SCARCITY
            if ClosingTechnique.HORMOZI_URGENCY in candidate_techniques:
                return ClosingTechnique.HORMOZI_URGENCY

        # Si hay objeción → usar risk reversal o emotional reframe
        if any(s.signal_type == "objection_raised" for s in signals):
            if ClosingTechnique.HORMOZI_RISK_REVERSAL in candidate_techniques:
                return ClosingTechnique.HORMOZI_RISK_REVERSAL

        # Default: primera técnica candidata
        return candidate_techniques[0] if candidate_techniques else ClosingTechnique.TRUMP_DIRECT

    async def generate_closing_message(
        self,
        technique: ClosingTechnique,
        customer_name: str,
        product_info: Dict[str, Any],
        offer_deadline: Optional[datetime] = None,
        objections: Optional[List[str]] = None,
    ) -> str:
        """Genera mensaje de cierre personalizado."""
        template = self.CLOSING_TEMPLATES.get(technique, "")

        if not template:
            return f"I think this is a great fit for you, {customer_name}. Let's make it happen."

        # Variables a reemplazar
        replacements = {
            "{deadline}": (offer_deadline + timedelta(hours=24)).strftime("%A at %I:%M %p") if offer_deadline else "tomorrow",
            "{count}": product_info.get("count", "5"),
            "{step1}": product_info.get("step1", "Get started"),
            "{step2}": product_info.get("step2", "See results"),
            "{step3}": product_info.get("step3", "Scale up"),
            "{when}": product_info.get("price_increase_when", "Friday"),
            "{result}": product_info.get("result", "achieved amazing results"),
            "{timeframe}": product_info.get("timeframe", "30 days"),
            "{name}": product_info.get("story_character", "Sarah"),
            "{result_example}": product_info.get("result_example", "doubled their revenue"),
            "{reason}": product_info.get("reason", "you're coachable"),
            "{time}": product_info.get("delivery_time", "2 hours"),
            "{offer_summary}": product_info.get("offer_summary", "Full access + support"),
        }

        message = template
        for key, value in replacements.items():
            message = message.replace(key, str(value))

        return message.strip()

    async def handle_objection(
        self,
        objection: str,
        product_info: Dict[str, Any],
    ) -> str:
        """Maneja objeción con técnicas de Hormozi/Trump."""
        objection_lower = objection.lower()

        # OBJECIÓN: "Es muy caro"
        if any(word in objection_lower for word in ["caro", "expensive", "precio", "cost"]):
            return f"""
I get it. But think about it this way:

What's the cost of NOT doing this?

In 6 months, {product_info.get('cost_of_inaction', 'you could be ahead or still stuck in the same place')}.

The investment pays for itself {product_info.get('payback_timeframe', 'within 30 days')}.

Worth it?
"""

        # OBJECIÓN: "No tengo tiempo"
        if any(word in objection_lower for word in ["tiempo", "time", "ocupado", "busy"]):
            return f"""
Exactly. That's WHY you need this.

This isn't about adding MORE to your plate.
This is about doing LESS and getting MORE.

{product_info.get('time_savings', 'You save 10+ hours/week')}.

Time is your most valuable asset. Invest it wisely.
"""

        # OBJECIÓN: "No estoy seguro"
        if any(word in objection_lower for word in ["seguro", "sure", "confuso", "unsure", "duda"]):
            return f"""
That's actually healthy. Big decisions should feel weighty.

Here's what removes the doubt:

{product_info.get('risk_removal', 'Money-back guarantee for 30 days')}.

Zero risk. All upside.

You're safe. Let's do this.
"""

        # Default: Reframe + Scarcity
        return f"""
I appreciate your caution. That shows you think carefully.

But here's the thing: Every day you wait is a day someone else is getting ahead.

This opportunity is time-limited.

What would it take for you to say yes TODAY?
"""

    async def score_close_readiness(
        self,
        conversation_history: List[Dict[str, str]],
        customer_profile: Dict[str, Any],
        signals: List[SalesSignal],
    ) -> float:
        """
        Calcula readiness score para cerrar (0-1).

        0.0-0.3: No ready
        0.3-0.7: Maybe ready (need more conversation)
        0.7-1.0: Ready to close
        """
        score = 0.5  # base

        # Boost por señales de compra
        for signal in signals:
            score += signal.confidence * 0.15

        # Boost por engagement
        if conversation_history:
            avg_length = sum(len(msg.get("content", "")) for msg in conversation_history[-5:]) / 5
            if avg_length > 150:
                score += 0.15

        # Penalty si hay hesitación
        last_msg = conversation_history[-1].get("content", "").lower() if conversation_history else ""
        if any(word in last_msg for word in ["no sé", "maybe", "quizás", "think about"]):
            score -= 0.1

        return min(1.0, max(0.0, score))


def get_closing_strategist() -> ClosingStrategist:
    """Factory para obtener closing strategist."""
    return ClosingStrategist()
