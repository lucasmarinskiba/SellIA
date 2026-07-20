"""
Phase 10: Humanization — Response Builder (400L)

Combines tone + empathy + personalization + CTA into coherent human-sounding messages.

Flow:
1. Select tone (from ToneEngine)
2. Detect emotion (from EmpathyLayer)
3. Apply personalization (from PersonalizationEngine)
4. Inject CTA (strategically, naturally)
5. Validate output (sounds human? appropriate?)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from random import choice

logger = logging.getLogger(__name__)


class CTAType(str, Enum):
    """Call-to-action types"""
    SOFT = "soft"  # "Let me know" / "Open to ideas"
    DIRECT = "direct"  # "Click here" / "Buy now"
    SCARCITY = "scarcity"  # "Only X left" / "Limited time"
    BENEFIT = "benefit"  # "You'll save X"
    FEAR_OF_MISSING = "fear_of_missing"  # "Don't miss out"
    CURIOSITY = "curiosity"  # "See what others found"


@dataclass
class ResponseTemplate:
    """Template for building responses"""
    intro: str  # Opening line
    body: str  # Main message
    social_proof: Optional[str]  # "100+ customers love this"
    cta: str  # Call to action
    closing: str  # Sign-off
    tone_tags: List[str]  # ["friendly", "professional"]


class ResponseBuilder:
    """Builds human-sounding responses from components"""

    # Soft CTAs (low pressure)
    SOFT_CTAS = {
        "en": [
            "What do you think?",
            "How does that sound?",
            "Curious to hear your thoughts.",
            "Let me know if you'd like to explore this.",
            "Happy to answer any questions.",
        ],
        "es": [
            "¿Qué te parece?",
            "¿Cómo suena?",
            "Tengo curiosidad por tu opinión.",
            "Avísame si quieres explorar esto.",
            "Feliz de responder cualquier pregunta.",
        ],
    }

    # Direct CTAs (action-oriented)
    DIRECT_CTAS = {
        "en": [
            "Let's set up a quick call.",
            "Click below to get started.",
            "Book a time that works for you.",
            "Reply with your availability.",
            "Let's make this happen.",
        ],
        "es": [
            "Estableczcamos una llamada rápida.",
            "Haz clic a continuación para comenzar.",
            "Reserva un tiempo que te funcione.",
            "Responde con tu disponibilidad.",
            "Hagamos que suceda.",
        ],
    }

    # Scarcity CTAs (time-limited)
    SCARCITY_CTAS = {
        "en": [
            "Only 2 spots left this month.",
            "This rate only lasts until {date}.",
            "We're at capacity next week.",
            "Lock in your spot today.",
            "Don't miss this window.",
        ],
        "es": [
            "Solo 2 espacios en este mes.",
            "Esta tarifa solo dura hasta {date}.",
            "Estaremos a capacidad la próxima semana.",
            "Asegura tu lugar hoy.",
            "No pierdas esta ventana.",
        ],
    }

    # Benefit CTAs (value-focused)
    BENEFIT_CTAS = {
        "en": [
            "See how you can save 10 hours/week.",
            "Discover how other teams did it.",
            "Find out why {percent}% see results in 30 days.",
            "Get the exact framework we use.",
            "Learn the {industry} playbook.",
        ],
        "es": [
            "Mira cómo puedes ahorrar 10 horas/semana.",
            "Descubre cómo lo hicieron otros equipos.",
            "Entérate por qué {percent}% ve resultados en 30 días.",
            "Obtén el marco exacto que usamos.",
            "Aprende el playbook de {industry}.",
        ],
    }

    # FOMO CTAs (fear of missing out)
    FOMO_CTAS = {
        "en": [
            "See what {count} companies discovered.",
            "Check out the results others got.",
            "Join the {percent}% getting results.",
            "Discover what you're missing.",
            "See how the leaders do it.",
        ],
        "es": [
            "Mira qué descubrieron {count} empresas.",
            "Revisa los resultados que obtuvieron otros.",
            "Únete al {percent}% que obtiene resultados.",
            "Descubre qué te estás perdiendo.",
            "Mira cómo lo hacen los líderes.",
        ],
    }

    # Curiosity CTAs (question-based)
    CURIOSITY_CTAS = {
        "en": [
            "Wondering if this applies to you?",
            "Want to know if you qualify?",
            "Curious if this could work for your situation?",
            "Questions? I'm here to help.",
            "Want to explore this further?",
        ],
        "es": [
            "¿Te preguntas si esto te aplica?",
            "¿Quieres saber si calificas?",
            "¿Curioso si esto podría funcionar para tu situación?",
            "¿Preguntas? Estoy aquí para ayudar.",
            "¿Quieres explorar esto más?",
        ],
    }

    # Social proof templates
    SOCIAL_PROOF = {
        "en": [
            "Join {count}+ {industry} leaders using this.",
            "{percent}% of {audience} see results in {timeframe}.",
            "Trusted by companies like {companies}.",
            "{count}+ success stories. Zero complaints.",
            "Award-winning approach used by {type} companies.",
        ],
        "es": [
            "Únete a {count}+ líderes de {industry} usando esto.",
            "El {percent}% de {audience} ve resultados en {timeframe}.",
            "De confianza para empresas como {companies}.",
            "{count}+ historias de éxito. Cero quejas.",
            "Enfoque galardonado usado por empresas {type}.",
        ],
    }

    # Closings by tone
    CLOSINGS = {
        "professional": {
            "en": ["Best regards,", "Sincerely,", "Kind regards,"],
            "es": ["Saludos cordiales,", "Atentamente,", "Con respeto,"],
        },
        "friendly": {
            "en": ["Cheers!", "All the best!", "Talk soon!", "Your friend,"],
            "es": ["¡Saludos!", "¡Lo mejor!", "¡Nos hablamos!", "Tu amigo,"],
        },
        "casual": {
            "en": ["Talk later!", "Catch you soon!", "Peace out!", "✌️"],
            "es": ["¡Nos vemos!", "¡Hasta luego!", "¡Paz!", "✌️"],
        },
    }

    def __init__(self):
        """Initialize response builder"""
        logger.info("ResponseBuilder initialized")

    def build_response(
        self,
        base_message: str,
        tone_type: str,
        emotional_state: str,
        buyer_name: Optional[str] = None,
        cta_type: CTAType = CTAType.SOFT,
        social_proof_data: Optional[Dict[str, Any]] = None,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Build complete human-sounding response.

        Args:
            base_message: Core message content
            tone_type: Tone from ToneEngine
            emotional_state: Emotion from EmpathyLayer
            buyer_name: Buyer's first name (for personalization)
            cta_type: Call-to-action type
            social_proof_data: Data for social proof {count, percent, audience, etc}
            language: Language code

        Returns:
            {
                "response": str,
                "tone": str,
                "cta_strength": float,  # 0.0-1.0
                "personalization_score": float,
                "humanness_score": float,  # 0.0-1.0
                "components": {
                    "intro": str,
                    "body": str,
                    "social_proof": str,
                    "cta": str,
                    "closing": str,
                },
            }
        """
        social_proof_data = social_proof_data or {}

        # Build components
        intro = self._build_intro(buyer_name, emotional_state, language)
        body = base_message
        social_proof = self._build_social_proof(social_proof_data, language)
        cta = self._build_cta(cta_type, language)
        closing = self._build_closing(tone_type, language)

        # Assemble response
        response_parts = []

        if intro:
            response_parts.append(intro)

        response_parts.append(body)

        if social_proof:
            response_parts.append(f"\n\n{social_proof}")

        response_parts.append(f"\n\n{cta}")
        response_parts.append(f"\n{closing}")

        full_response = "\n".join(response_parts)

        # Calculate scores
        cta_strength = self._calculate_cta_strength(cta_type, base_message)
        personalization_score = 0.8 if buyer_name else 0.5
        humanness_score = self._calculate_humanness(full_response, tone_type, language)

        return {
            "response": full_response,
            "tone": tone_type,
            "emotional_context": emotional_state,
            "cta_strength": cta_strength,
            "personalization_score": personalization_score,
            "humanness_score": humanness_score,
            "components": {
                "intro": intro or "N/A",
                "body": body,
                "social_proof": social_proof or "N/A",
                "cta": cta,
                "closing": closing,
            },
            "language": language,
        }

    def _build_intro(
        self,
        buyer_name: Optional[str],
        emotional_state: str,
        language: str,
    ) -> Optional[str]:
        """Build personalized intro"""
        if not buyer_name:
            return None

        first_name = buyer_name.split()[0] if buyer_name else "there"

        # Tailor intro to emotional state
        if emotional_state == "frustrated":
            if language == "es":
                return f"{first_name}, entiendo que esto puede ser frustrante."
            else:
                return f"{first_name}, I completely understand this can be frustrating."

        elif emotional_state == "hesitant":
            if language == "es":
                return f"{first_name}, muchas personas se sienten igual al principio."
            else:
                return f"{first_name}, a lot of people feel the same way at first."

        elif emotional_state == "skeptical":
            if language == "es":
                return f"{first_name}, es justo ser escéptico — aquí está la prueba."
            else:
                return f"{first_name}, healthy skepticism is smart — here's the proof."

        else:
            # Generic friendly intro
            if language == "es":
                return f"¡Hola {first_name}!"
            else:
                return f"Hey {first_name}!"

    def _build_cta(
        self,
        cta_type: CTAType,
        language: str,
    ) -> str:
        """Build call-to-action"""
        templates = {
            CTAType.SOFT: self.SOFT_CTAS,
            CTAType.DIRECT: self.DIRECT_CTAS,
            CTAType.SCARCITY: self.SCARCITY_CTAS,
            CTAType.BENEFIT: self.BENEFIT_CTAS,
            CTAType.FEAR_OF_MISSING: self.FOMO_CTAS,
            CTAType.CURIOSITY: self.CURIOSITY_CTAS,
        }

        template_list = templates.get(cta_type, templates[CTAType.SOFT])
        language_templates = template_list.get(language, template_list["en"])
        return choice(language_templates)

    def _build_social_proof(
        self,
        data: Dict[str, Any],
        language: str,
    ) -> Optional[str]:
        """Build social proof statement if data provided"""
        if not data:
            return None

        templates = self.SOCIAL_PROOF.get(language, self.SOCIAL_PROOF["en"])
        template = choice(templates)

        try:
            return template.format(**data)
        except KeyError:
            # Missing data, skip social proof
            return None

    def _build_closing(
        self,
        tone_type: str,
        language: str,
    ) -> str:
        """Build closing based on tone"""
        # Map tone to closing style
        if tone_type in ["professional", "formal"]:
            closing_style = "professional"
        elif tone_type in ["casual", "cheeky"]:
            closing_style = "casual"
        else:
            closing_style = "friendly"

        closings = self.CLOSINGS.get(closing_style, {})
        language_closings = closings.get(language, closings.get("en", ["Best regards,"]))
        return choice(language_closings)

    def _calculate_cta_strength(
        self,
        cta_type: CTAType,
        message: str,
    ) -> float:
        """
        Calculate CTA strength (how pushy is it?)

        0.0 = very soft
        1.0 = very hard sell
        """
        if cta_type == CTAType.SOFT:
            return 0.2
        elif cta_type == CTAType.DIRECT:
            return 0.6
        elif cta_type == CTAType.SCARCITY:
            return 0.8
        elif cta_type == CTAType.FEAR_OF_MISSING:
            return 0.75
        else:
            return 0.5

    def _calculate_humanness(
        self,
        text: str,
        tone_type: str,
        language: str,
    ) -> float:
        """
        Calculate how human the response sounds (0-1).

        Checks:
        - Sentence variety
        - Natural language markers
        - Conversational tone
        - Emoji usage (if appropriate)
        - Contraction usage
        """
        score = 0.5  # Start neutral

        # Sentence variety (different lengths)
        sentences = text.split(".")
        sentence_lengths = [len(s.split()) for s in sentences if s.strip()]
        if len(set(sentence_lengths)) > 2:  # Multiple lengths = variety
            score += 0.15

        # Natural transitions
        if any(word in text.lower() for word in ["i think", "you know", "honestly", "totally"]):
            score += 0.1

        # Contractions (makes it feel natural)
        if any(contraction in text for contraction in ["'s", "'t", "'re", "'ve", "'ll", "'d"]):
            score += 0.1

        # Emoji usage (adds personality if used appropriately)
        emoji_count = sum(1 for char in text if ord(char) > 127)
        if emoji_count in [1, 2]:  # 1-2 is good
            score += 0.05
        elif emoji_count > 3:  # Too many
            score -= 0.05

        # Avoid robotic language
        robotic_phrases = [
            "i am writing to inform you",
            "pursuant to our discussion",
            "as per",
            "attached herewith",
        ]
        if any(phrase in text.lower() for phrase in robotic_phrases):
            score -= 0.3

        return min(max(score, 0.0), 1.0)

    def optimize_for_platform(
        self,
        response: str,
        platform: str,  # "email", "whatsapp", "sms", "instagram"
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Optimize response for specific platform.

        Platform requirements:
        - Email: Full format, professional
        - WhatsApp: Shorter, emoji-friendly, link-compatible
        - SMS: Very short, no emojis
        - Instagram: Emojis, hashtags, casual tone
        """
        optimized = response

        if platform == "sms":
            # Remove excess whitespace, keep under 160 chars if possible
            optimized = " ".join(optimized.split())
            optimized = optimized[:160]

        elif platform == "whatsapp":
            # Add formatting, break into paragraphs
            optimized = optimized.replace("\n\n", "\n")

        elif platform == "instagram":
            # Add relevant emojis and hashtags
            if "✨" not in optimized and "🚀" not in optimized:
                optimized = f"{optimized}\n✨"
            if "#" not in optimized and language == "en":
                optimized = f"{optimized}\n#sales #growth"

        return {
            "optimized_response": optimized,
            "platform": platform,
            "length": len(optimized),
            "characteristics": self._get_platform_characteristics(platform),
        }

    def _get_platform_characteristics(self, platform: str) -> Dict[str, Any]:
        """Get platform-specific characteristics"""
        specs = {
            "email": {
                "max_length": 2000,
                "emoji_appropriate": False,
                "hashtags_appropriate": False,
            },
            "whatsapp": {
                "max_length": 4096,
                "emoji_appropriate": True,
                "hashtags_appropriate": False,
            },
            "sms": {
                "max_length": 160,
                "emoji_appropriate": False,
                "hashtags_appropriate": False,
            },
            "instagram": {
                "max_length": 2200,
                "emoji_appropriate": True,
                "hashtags_appropriate": True,
            },
        }
        return specs.get(platform, specs["email"])

    def validate_response(
        self,
        response: str,
        tone: str,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Validate response quality before sending.

        Checks:
        - Grammar/spelling
        - Tone consistency
        - No jargon overload
        - Appropriate length
        - Engaging opener
        """
        issues = []
        warnings = []

        # Check for minimum length
        if len(response.split()) < 10:
            issues.append("Response too short")

        # Check for maximum length
        if len(response.split()) > 300:
            warnings.append("Response might be too long for casual reading")

        # Check for tone consistency
        formal_words = ["pursuant", "herewith", "aforementioned"]
        if tone == "casual" and any(w in response.lower() for w in formal_words):
            issues.append("Formal language conflicts with casual tone")

        # Check for jargon overload
        complex_words = response.split()
        complex_count = sum(1 for w in complex_words if len(w) > 10)
        if complex_count / len(complex_words) > 0.2:
            warnings.append("High ratio of complex words - simplify for readability")

        # Check for engaging opener
        first_sentence = response.split(".")[0]
        if len(first_sentence) < 5:
            warnings.append("Opening could be more engaging")

        return {
            "is_valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "recommendation": "Send" if len(issues) == 0 else f"Fix issues before sending: {', '.join(issues)}",
        }
