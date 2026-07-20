"""
Phase 10: Humanization — Tone Engine (600L)

Manages 10+ distinct communication tones across markets/industries:
1. Formal — Professional, structured, serious
2. Casual — Relaxed, conversational, approachable
3. Friendly — Warm, personable, emotionally engaging
4. Professional — Business-focused, credible, expert
5. Cheeky — Playful, witty, bold
6. Educational — Informative, teaching-focused
7. Urgent — Time-sensitive, action-oriented
8. Luxe — Premium, exclusive, aspirational
9. Discount — Value-focused, deal-oriented
10. Empathetic — Understanding, supportive, listening

Market/Industry Context:
- Hispanic market (es_MX, es_ES, es_AR)
- English (en_US, en_UK)
- Real estate, SaaS, E-commerce, Services
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


class ToneType(str, Enum):
    """10 core tone types"""
    FORMAL = "formal"
    CASUAL = "casual"
    FRIENDLY = "friendly"
    PROFESSIONAL = "professional"
    CHEEKY = "cheeky"
    EDUCATIONAL = "educational"
    URGENT = "urgent"
    LUXE = "luxe"
    DISCOUNT = "discount"
    EMPATHETIC = "empathetic"


class Market(str, Enum):
    """Market regions"""
    LATIN_AMERICA = "es_MX"  # Mexico
    SPAIN = "es_ES"
    ARGENTINA = "es_AR"
    USA = "en_US"
    UK = "en_UK"


class Industry(str, Enum):
    """Industry types"""
    REAL_ESTATE = "real_estate"
    SAAS = "saas"
    ECOMMERCE = "ecommerce"
    SERVICES = "services"
    RETAIL = "retail"


@dataclass
class ToneProfile:
    """Definition of a tone"""
    tone_type: ToneType
    market: Market
    industry: Industry

    # Tone characteristics
    formality_level: float  # 0.0 (very casual) to 1.0 (very formal)
    energy_level: float  # 0.0 (calm) to 1.0 (high energy)
    humor_appropriate: bool
    emoji_density: float  # 0.0 (none) to 1.0 (heavy)

    # Vocabulary patterns
    vocabulary_markers: List[str] = field(default_factory=list)
    forbidden_words: List[str] = field(default_factory=list)

    # Sentence structure
    avg_sentence_length: int = 12  # Average words per sentence
    use_contractions: bool = True
    use_exclamation: bool = False

    # Greeting/closing patterns
    greeting_templates: List[str] = field(default_factory=list)
    closing_templates: List[str] = field(default_factory=list)

    # Emoji preferences
    preferred_emojis: List[str] = field(default_factory=list)

    # Created metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    confidence_score: float = 0.8


class ToneEngine:
    """Manages communication tones across markets and industries."""

    # FORMAL TONE — Professional, structured, business
    FORMAL_PROFILES = {
        Market.LATIN_AMERICA: ToneProfile(
            tone_type=ToneType.FORMAL,
            market=Market.LATIN_AMERICA,
            industry=Industry.REAL_ESTATE,
            formality_level=0.95,
            energy_level=0.3,
            humor_appropriate=False,
            emoji_density=0.0,
            vocabulary_markers=[
                "le presentamos", "cordialmente", "con gusto",
                "profesional", "confidencial", "propiedad premium"
            ],
            forbidden_words=["hey", "dude", "lol", "jaja"],
            avg_sentence_length=16,
            use_contractions=False,
            use_exclamation=False,
            greeting_templates=[
                "Estimado/a {name},",
                "Le saludamos cordialmente,",
                "Nos complace saludarle,",
            ],
            closing_templates=[
                "Quedo a su disposición.",
                "Atentamente,",
                "Saludos cordiales,",
            ],
            preferred_emojis=[],
        ),
    }

    # CASUAL TONE — Relaxed, conversational, approachable
    CASUAL_PROFILES = {
        Market.USA: ToneProfile(
            tone_type=ToneType.CASUAL,
            market=Market.USA,
            industry=Industry.ECOMMERCE,
            formality_level=0.2,
            energy_level=0.7,
            humor_appropriate=True,
            emoji_density=0.3,
            vocabulary_markers=[
                "hey", "cool", "awesome", "totally", "basically",
                "super easy", "no problem", "what's up"
            ],
            forbidden_words=["endeavor", "facilitate", "pursuant"],
            avg_sentence_length=10,
            use_contractions=True,
            use_exclamation=True,
            greeting_templates=[
                "Hey {name}!",
                "What's up {name}!",
                "Hey there!",
                "Yo {name}!",
            ],
            closing_templates=[
                "Catch you later!",
                "Talk soon!",
                "All the best!",
                "Cheers!",
            ],
            preferred_emojis=["😊", "👍", "🚀", "💪", "🎉"],
        ),
    }

    # FRIENDLY TONE — Warm, personable, emotionally engaging
    FRIENDLY_PROFILES = {
        Market.LATIN_AMERICA: ToneProfile(
            tone_type=ToneType.FRIENDLY,
            market=Market.LATIN_AMERICA,
            industry=Industry.SERVICES,
            formality_level=0.4,
            energy_level=0.8,
            humor_appropriate=True,
            emoji_density=0.4,
            vocabulary_markers=[
                "con cariño", "para ti", "querido/a", "amigo/a",
                "te encantará", "seguro que te gusta"
            ],
            forbidden_words=["indiferente", "insignificante"],
            avg_sentence_length=11,
            use_contractions=True,
            use_exclamation=True,
            greeting_templates=[
                "¡Hola {name}! 😊",
                "¡Qué tal {name}!",
                "¡Amigo/a {name}!",
            ],
            closing_templates=[
                "¡Un abrazo grande!",
                "¡Con cariño!",
                "¡Que te vaya bien!",
            ],
            preferred_emojis=["😊", "❤️", "🤗", "✨", "🌟"],
        ),
    }

    # PROFESSIONAL TONE — Business-focused, credible, expert
    PROFESSIONAL_PROFILES = {
        Market.USA: ToneProfile(
            tone_type=ToneType.PROFESSIONAL,
            market=Market.USA,
            industry=Industry.SAAS,
            formality_level=0.85,
            energy_level=0.5,
            humor_appropriate=False,
            emoji_density=0.05,
            vocabulary_markers=[
                "streamline", "optimize", "leverage", "stakeholder",
                "innovative", "scalable", "enterprise-grade"
            ],
            forbidden_words=["gonna", "kinda", "thingy"],
            avg_sentence_length=14,
            use_contractions=False,
            use_exclamation=False,
            greeting_templates=[
                "Dear {name},",
                "Hello {name},",
                "Greetings,",
            ],
            closing_templates=[
                "Best regards,",
                "Sincerely,",
                "Kind regards,",
            ],
            preferred_emojis=["💼"],
        ),
    }

    # CHEEKY TONE — Playful, witty, bold
    CHEEKY_PROFILES = {
        Market.USA: ToneProfile(
            tone_type=ToneType.CHEEKY,
            market=Market.USA,
            industry=Industry.ECOMMERCE,
            formality_level=0.1,
            energy_level=0.95,
            humor_appropriate=True,
            emoji_density=0.6,
            vocabulary_markers=[
                "literally", "honestly", "plot twist", "ngl",
                "same energy", "no cap", "periodt", "vibes"
            ],
            forbidden_words=["boring", "forgettable"],
            avg_sentence_length=9,
            use_contractions=True,
            use_exclamation=True,
            greeting_templates=[
                "Yo {name}! 👀",
                "Oop, {name}!",
                "{name}, listen up!",
            ],
            closing_templates=[
                "That's facts.",
                "End of thread. 🎤",
                "And that's the tea ☕",
            ],
            preferred_emojis=["😏", "🔥", "✨", "💅", "😎"],
        ),
    }

    # EDUCATIONAL TONE — Informative, teaching-focused
    EDUCATIONAL_PROFILES = {
        Market.USA: ToneProfile(
            tone_type=ToneType.EDUCATIONAL,
            market=Market.USA,
            industry=Industry.SAAS,
            formality_level=0.65,
            energy_level=0.6,
            humor_appropriate=True,
            emoji_density=0.2,
            vocabulary_markers=[
                "let's learn", "here's how", "important to understand",
                "key points", "breakdown", "pro tip", "best practice"
            ],
            forbidden_words=["you wouldn't understand"],
            avg_sentence_length=13,
            use_contractions=True,
            use_exclamation=False,
            greeting_templates=[
                "Quick lesson for {name}:",
                "Here's what {name} should know:",
                "Let's break this down:",
            ],
            closing_templates=[
                "Hope this helps!",
                "Now you're equipped with knowledge.",
                "Feel free to reach out with questions.",
            ],
            preferred_emojis=["📚", "💡", "🎓", "🔍"],
        ),
    }

    # URGENT TONE — Time-sensitive, action-oriented
    URGENT_PROFILES = {
        Market.USA: ToneProfile(
            tone_type=ToneType.URGENT,
            market=Market.USA,
            industry=Industry.ECOMMERCE,
            formality_level=0.5,
            energy_level=1.0,
            humor_appropriate=False,
            emoji_density=0.3,
            vocabulary_markers=[
                "immediately", "don't miss out", "limited time",
                "act now", "today only", "last chance", "hurry"
            ],
            forbidden_words=["maybe", "eventually", "later"],
            avg_sentence_length=8,
            use_contractions=True,
            use_exclamation=True,
            greeting_templates=[
                "⚠️ {name}!",
                "URGENT: {name}",
                "Action needed: {name}",
            ],
            closing_templates=[
                "Act now!",
                "This won't wait.",
                "Time is running out!",
            ],
            preferred_emojis=["⚠️", "🔴", "⏰", "🚨", "💨"],
        ),
    }

    # LUXE TONE — Premium, exclusive, aspirational
    LUXE_PROFILES = {
        Market.LATIN_AMERICA: ToneProfile(
            tone_type=ToneType.LUXE,
            market=Market.LATIN_AMERICA,
            industry=Industry.REAL_ESTATE,
            formality_level=0.9,
            energy_level=0.4,
            humor_appropriate=False,
            emoji_density=0.1,
            vocabulary_markers=[
                "exquisito", "exclusivo", "elegancia", "prestigio",
                "obra maestra", "incomparable", "distinguido"
            ],
            forbidden_words=["barato", "ordinario"],
            avg_sentence_length=15,
            use_contractions=False,
            use_exclamation=False,
            greeting_templates=[
                "Distinguido/a {name},",
                "Estimado/a cliente de clase elite,",
                "Le invitamos,",
            ],
            closing_templates=[
                "Esperamos servirle con excelencia.",
                "Su satisfacción es nuestra misión.",
                "Hasta pronto.",
            ],
            preferred_emojis=["💎", "✨", "👑"],
        ),
    }

    # DISCOUNT TONE — Value-focused, deal-oriented
    DISCOUNT_PROFILES = {
        Market.USA: ToneProfile(
            tone_type=ToneType.DISCOUNT,
            market=Market.USA,
            industry=Industry.ECOMMERCE,
            formality_level=0.3,
            energy_level=0.8,
            humor_appropriate=True,
            emoji_density=0.4,
            vocabulary_markers=[
                "save", "deal", "unbeatable", "value", "steal",
                "bargain", "score", "bang for your buck"
            ],
            forbidden_words=["premium pricing"],
            avg_sentence_length=10,
            use_contractions=True,
            use_exclamation=True,
            greeting_templates=[
                "{name}, check out these deals!",
                "Heads up, {name}!",
                "{name}, you don't want to miss this!",
            ],
            closing_templates=[
                "Grab yours before they're gone!",
                "Stock up today!",
                "Best deal of the season!",
            ],
            preferred_emojis=["💰", "🛍️", "💯", "🔥"],
        ),
    }

    # EMPATHETIC TONE — Understanding, supportive, listening
    EMPATHETIC_PROFILES = {
        Market.LATIN_AMERICA: ToneProfile(
            tone_type=ToneType.EMPATHETIC,
            market=Market.LATIN_AMERICA,
            industry=Industry.SERVICES,
            formality_level=0.5,
            energy_level=0.4,
            humor_appropriate=False,
            emoji_density=0.2,
            vocabulary_markers=[
                "entiendo", "comprendo", "te acompañamos", "sentimos",
                "estamos aquí para ti", "te escuchamos"
            ],
            forbidden_words=["tu culpa"],
            avg_sentence_length=12,
            use_contractions=True,
            use_exclamation=False,
            greeting_templates=[
                "Entiendo tu situación, {name}",
                "Estamos contigo, {name}",
                "Te escuchamos, {name}",
            ],
            closing_templates=[
                "Estamos aquí para ayudarte.",
                "Cuenta con nosotros.",
                "Tu bienestar es importante.",
            ],
            preferred_emojis=["❤️", "🤝", "🌟", "💙"],
        ),
    }

    # Registry of all tone profiles
    TONE_REGISTRY: Dict[Tuple[ToneType, Market, Industry], ToneProfile] = {}

    def __init__(self):
        """Initialize tone engine with all profiles"""
        self._register_profiles()
        logger.info("ToneEngine initialized with all tone profiles")

    def _register_profiles(self) -> None:
        """Register all tone profiles"""
        for profile in self.FORMAL_PROFILES.values():
            self._register(profile)
        for profile in self.CASUAL_PROFILES.values():
            self._register(profile)
        for profile in self.FRIENDLY_PROFILES.values():
            self._register(profile)
        for profile in self.PROFESSIONAL_PROFILES.values():
            self._register(profile)
        for profile in self.CHEEKY_PROFILES.values():
            self._register(profile)
        for profile in self.EDUCATIONAL_PROFILES.values():
            self._register(profile)
        for profile in self.URGENT_PROFILES.values():
            self._register(profile)
        for profile in self.LUXE_PROFILES.values():
            self._register(profile)
        for profile in self.DISCOUNT_PROFILES.values():
            self._register(profile)
        for profile in self.EMPATHETIC_PROFILES.values():
            self._register(profile)

    def _register(self, profile: ToneProfile) -> None:
        """Register a tone profile"""
        key = (profile.tone_type, profile.market, profile.industry)
        self.TONE_REGISTRY[key] = profile

    def get_tone_profile(
        self,
        tone_type: ToneType,
        market: Market,
        industry: Industry,
    ) -> Optional[ToneProfile]:
        """
        Get tone profile by type, market, and industry.
        Falls back to available profiles if exact match not found.

        Returns:
            ToneProfile or None if not found
        """
        key = (tone_type, market, industry)
        if key in self.TONE_REGISTRY:
            return self.TONE_REGISTRY[key]

        # Fallback: any tone + market
        for profile in self.TONE_REGISTRY.values():
            if profile.tone_type == tone_type and profile.market == market:
                return profile

        # Fallback: any tone + industry
        for profile in self.TONE_REGISTRY.values():
            if profile.tone_type == tone_type and profile.industry == industry:
                return profile

        # Fallback: just the tone type
        for profile in self.TONE_REGISTRY.values():
            if profile.tone_type == tone_type:
                return profile

        return None

    def suggest_tone(
        self,
        buyer_sentiment: str,
        buyer_urgency: str,
        market: Market,
        industry: Industry,
    ) -> ToneType:
        """
        Suggest best tone based on buyer state.

        Args:
            buyer_sentiment: "positive", "neutral", "negative"
            buyer_urgency: "low", "medium", "high"
            market: Market region
            industry: Industry type

        Returns:
            Recommended ToneType
        """
        # Map sentiment + urgency → tone
        if buyer_urgency == "high":
            return ToneType.URGENT

        if buyer_sentiment == "negative":
            return ToneType.EMPATHETIC

        if market == Market.USA and industry == Industry.ECOMMERCE:
            return ToneType.CASUAL

        if market == Market.LATIN_AMERICA and industry == Industry.REAL_ESTATE:
            if buyer_sentiment == "positive":
                return ToneType.LUXE
            return ToneType.FORMAL

        if industry == Industry.SAAS:
            return ToneType.PROFESSIONAL

        # Default
        return ToneType.FRIENDLY

    def apply_tone(
        self,
        message: str,
        tone_profile: ToneProfile,
    ) -> Dict[str, Any]:
        """
        Apply tone profile to message.

        Returns:
            {
                "toned_message": str,
                "tone_type": str,
                "formality_level": float,
                "confidence": float,
                "modifications": [list of changes],
            }
        """
        modifications = []

        # Adjust vocabulary based on formality
        words = message.split()
        toned_words = []

        for word in words:
            if tone_profile.formality_level > 0.8:
                # Use formal vocabulary
                formal_alternatives = {
                    "hey": "hello",
                    "cool": "excellent",
                    "awesome": "outstanding",
                }
                if word.lower() in formal_alternatives:
                    toned_words.append(formal_alternatives[word.lower()])
                    modifications.append(f"'{word}' → '{formal_alternatives[word.lower()]}'")
                else:
                    toned_words.append(word)
            else:
                toned_words.append(word)

        toned_message = " ".join(toned_words)

        # Add emoji if appropriate
        if tone_profile.emoji_density > 0.3 and tone_profile.preferred_emojis:
            toned_message = f"{toned_message} {tone_profile.preferred_emojis[0]}"
            modifications.append(f"Added emoji: {tone_profile.preferred_emojis[0]}")

        return {
            "toned_message": toned_message,
            "tone_type": tone_profile.tone_type.value,
            "formality_level": tone_profile.formality_level,
            "energy_level": tone_profile.energy_level,
            "confidence": tone_profile.confidence_score,
            "modifications": modifications,
        }

    def get_all_tones(self) -> List[Dict[str, Any]]:
        """Get all available tones"""
        tones = []
        seen = set()
        for profile in self.TONE_REGISTRY.values():
            if profile.tone_type.value not in seen:
                tones.append({
                    "tone": profile.tone_type.value,
                    "formality": profile.formality_level,
                    "energy": profile.energy_level,
                    "humor_appropriate": profile.humor_appropriate,
                })
                seen.add(profile.tone_type.value)
        return tones

    def measure_tone_match(
        self,
        text: str,
        tone_profile: ToneProfile,
    ) -> float:
        """
        Measure how well text matches a tone profile (0-1).

        Checks:
        - Formality markers present
        - Forbidden words absent
        - Sentence length
        - Emoji presence/absence
        """
        score = 0.5  # Start at neutral

        text_lower = text.lower()

        # Vocabulary match
        vocabulary_matches = sum(1 for marker in tone_profile.vocabulary_markers if marker in text_lower)
        score += min(vocabulary_matches * 0.05, 0.3)

        # Forbidden words
        forbidden_count = sum(1 for word in tone_profile.forbidden_words if word in text_lower)
        score -= min(forbidden_count * 0.1, 0.2)

        # Sentence length check
        sentences = text.split(".")
        avg_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
        if abs(avg_length - tone_profile.avg_sentence_length) < 3:
            score += 0.1

        # Contraction check
        if tone_profile.use_contractions and ("'t" in text or "'re" in text):
            score += 0.05

        # Emoji check
        emoji_count = sum(1 for char in text if ord(char) > 127)
        if tone_profile.emoji_density > 0.3 and emoji_count > 0:
            score += 0.1
        elif tone_profile.emoji_density < 0.1 and emoji_count == 0:
            score += 0.1

        return min(max(score, 0.0), 1.0)
