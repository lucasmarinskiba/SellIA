"""Lead Scoring Service — Automatic Hot/Warm/Cold classification.

Scoring factors:
- Engagement (message frequency, response time)
- Intent signals (buying keywords, questions)
- Buyer personality (driver > analytical > expressive > amiable)
- Pipeline stage (awareness → closure)
- Time decay (older leads = colder)
- Product fit (based on context)
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class LeadTemperature(str, Enum):
    """Temperatura del lead."""
    HOT = "hot"  # 70-100: ready to close
    WARM = "warm"  # 40-69: interested, nurturing
    COLD = "cold"  # 0-39: early stage


class LeadScoreBreakdown:
    """Desglose de scoring."""

    def __init__(self):
        self.engagement_score = 0.0  # 0-25 pts
        self.intent_score = 0.0  # 0-30 pts
        self.personality_score = 0.0  # 0-15 pts
        self.stage_score = 0.0  # 0-20 pts
        self.recency_score = 0.0  # 0-10 pts
        self.total_score = 0.0  # 0-100 pts

    def to_dict(self) -> Dict[str, float]:
        return {
            "engagement": self.engagement_score,
            "intent": self.intent_score,
            "personality": self.personality_score,
            "stage": self.stage_score,
            "recency": self.recency_score,
            "total": self.total_score,
        }


class LeadScore:
    """Score completo de un lead."""

    def __init__(
        self,
        lead_id: str,
        lead_name: str,
        score: float,
        temperature: LeadTemperature,
        breakdown: LeadScoreBreakdown,
    ):
        self.lead_id = lead_id
        self.lead_name = lead_name
        self.score = score  # 0-100
        self.temperature = temperature
        self.breakdown = breakdown
        self.scored_at = datetime.utcnow()
        self.next_action = self._recommend_action()

    def _recommend_action(self) -> str:
        """Recomienda acción basada en temperature."""
        if self.temperature == LeadTemperature.HOT:
            return "close_now"  # Sales closer
        elif self.temperature == LeadTemperature.WARM:
            return "nurture_with_value"  # Follow-up con valor
        else:
            return "re_engage_gently"  # Retarget

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lead_id": self.lead_id,
            "lead_name": self.lead_name,
            "score": self.score,
            "temperature": self.temperature.value,
            "breakdown": self.breakdown.to_dict(),
            "next_action": self.next_action,
            "scored_at": self.scored_at.isoformat(),
        }


class LeadScoringService:
    """Servicio de scoring de leads."""

    # Engagement thresholds
    HIGH_ENGAGEMENT = 5  # 5+ messages
    MEDIUM_ENGAGEMENT = 2  # 2-4 messages
    LOW_ENGAGEMENT = 0  # 0-1 messages

    # Intent keywords by strength
    STRONG_INTENT_KEYWORDS = {
        "es": ["compramos", "cuando entran", "confirmen", "facturación", "contrato", "cierre"],
        "en": ["when do we", "confirm the order", "invoice", "contract", "close"],
    }

    MEDIUM_INTENT_KEYWORDS = {
        "es": ["interesa", "podríamos", "cuándo", "precio", "detalles"],
        "en": ["interested", "how much", "when", "details", "next steps"],
    }

    WEAK_INTENT_KEYWORDS = {
        "es": ["qué es", "cómo funciona", "información"],
        "en": ["what is", "how does", "more info", "tell me about"],
    }

    def __init__(self):
        self.logger = logger

    async def score_lead(
        self,
        lead_id: str,
        lead_name: str,
        conversation_history: List[Dict[str, str]],
        customer_profile: Dict[str, Any],
        product_info: Optional[Dict[str, Any]] = None,
    ) -> LeadScore:
        """
        Calcula score completo del lead.

        Retorna: LeadScore con breakdown + recomendación.
        """
        breakdown = LeadScoreBreakdown()

        # 1. Engagement score (0-25)
        breakdown.engagement_score = self._calculate_engagement_score(conversation_history)

        # 2. Intent score (0-30)
        breakdown.intent_score = self._calculate_intent_score(conversation_history)

        # 3. Personality score (0-15)
        breakdown.personality_score = self._calculate_personality_score(conversation_history)

        # 4. Stage score (0-20)
        breakdown.stage_score = self._calculate_stage_score(conversation_history)

        # 5. Recency score (0-10)
        breakdown.recency_score = self._calculate_recency_score(conversation_history)

        # Total
        breakdown.total_score = (
            breakdown.engagement_score
            + breakdown.intent_score
            + breakdown.personality_score
            + breakdown.stage_score
            + breakdown.recency_score
        )

        # Classify temperature
        if breakdown.total_score >= 70:
            temperature = LeadTemperature.HOT
        elif breakdown.total_score >= 40:
            temperature = LeadTemperature.WARM
        else:
            temperature = LeadTemperature.COLD

        score = LeadScore(
            lead_id=lead_id,
            lead_name=lead_name,
            score=breakdown.total_score,
            temperature=temperature,
            breakdown=breakdown,
        )

        self.logger.info(
            f"Lead scored: {lead_name} | "
            f"score={score.score:.0f} | "
            f"temp={temperature.value} | "
            f"action={score.next_action}"
        )

        return score

    def _calculate_engagement_score(self, conversation_history: List[Dict[str, str]]) -> float:
        """Calcula engagement basado en frecuencia + velocidad."""
        if not conversation_history:
            return 0.0

        num_messages = len(conversation_history)

        # Mensajes = puntos
        if num_messages >= self.HIGH_ENGAGEMENT:
            engagement = 20.0  # Max
        elif num_messages >= self.MEDIUM_ENGAGEMENT:
            engagement = 12.0
        else:
            engagement = 5.0

        # Penalty si hay gaps largos (mensajes esporádicos)
        timestamps = [msg.get("timestamp") for msg in conversation_history if msg.get("timestamp")]
        if len(timestamps) >= 2:
            # Si todos los msgs están en mismo día = high engagement
            # Si dispersos en varios días = lower
            days_span = self._estimate_days_span(timestamps)
            if days_span > 7:
                engagement *= 0.7  # 30% penalty para leads dispersos
            elif days_span > 3:
                engagement *= 0.85  # 15% penalty

        return min(25.0, engagement)

    def _calculate_intent_score(self, conversation_history: List[Dict[str, str]]) -> float:
        """Calcula intent basado en keywords."""
        if not conversation_history:
            return 0.0

        combined_text = " ".join([msg.get("content", "").lower() for msg in conversation_history])

        score = 0.0

        # Strong intent
        strong_keywords = (
            self.STRONG_INTENT_KEYWORDS.get("es", [])
            + self.STRONG_INTENT_KEYWORDS.get("en", [])
        )
        strong_count = sum(1 for kw in strong_keywords if kw in combined_text)
        score += strong_count * 10  # 10 pts per strong keyword

        # Medium intent
        medium_keywords = (
            self.MEDIUM_INTENT_KEYWORDS.get("es", [])
            + self.MEDIUM_INTENT_KEYWORDS.get("en", [])
        )
        medium_count = sum(1 for kw in medium_keywords if kw in combined_text)
        score += medium_count * 5  # 5 pts per medium keyword

        # Weak intent (negative signal if ONLY weak)
        weak_keywords = (
            self.WEAK_INTENT_KEYWORDS.get("es", [])
            + self.WEAK_INTENT_KEYWORDS.get("en", [])
        )
        weak_count = sum(1 for kw in weak_keywords if kw in combined_text)
        if weak_count > 0 and strong_count == 0 and medium_count == 0:
            score += weak_count * 1  # Only 1 pt if no stronger signals

        return min(30.0, score)

    def _calculate_personality_score(self, conversation_history: List[Dict[str, str]]) -> float:
        """Calcula personality score (drivers = mejor compradores)."""
        if not conversation_history:
            return 7.5  # Neutral

        combined_text = " ".join([msg.get("content", "").lower() for msg in conversation_history])

        # Driver personality (high buying intent, results-focused)
        if any(word in combined_text for word in ["rápido", "ahora", "inmediato", "hoy", "asap", "urgent"]):
            return 15.0  # Max

        # Analytical (needs more info, slower)
        if any(word in combined_text for word in ["detalles", "cómo funciona", "specifics", "details"]):
            return 10.0

        # Expressive (emotional, relationship-driven)
        if any(word in combined_text for word in ["siento", "creo", "feel", "think", "love"]):
            return 12.0

        # Default neutral
        return 7.5

    def _calculate_stage_score(self, conversation_history: List[Dict[str, str]]) -> float:
        """Calcula stage score (closure > negotiation > consideration > awareness)."""
        if not conversation_history:
            return 0.0

        combined_text = " ".join([msg.get("content", "").lower() for msg in conversation_history])

        # Closure signals
        if any(word in combined_text for word in ["confirmo", "adelante", "let's do", "confirmamos"]):
            return 20.0  # Max

        # Negotiation signals
        if any(word in combined_text for word in ["precio", "términos", "payment", "terms"]):
            return 15.0

        # Consideration signals
        if any(word in combined_text for word in ["interesa", "podría", "might", "interested"]):
            return 10.0

        # Awareness only
        return 5.0

    def _calculate_recency_score(self, conversation_history: List[Dict[str, str]]) -> float:
        """Calcula recency score (leads recientes = más hot)."""
        if not conversation_history:
            return 0.0

        # Asumir último mensaje = más reciente
        last_msg = conversation_history[-1]
        last_timestamp = last_msg.get("timestamp")

        if not last_timestamp:
            return 5.0  # Neutral si no hay timestamp

        # Parse timestamp (asumiendo ISO format)
        try:
            last_date = datetime.fromisoformat(last_timestamp)
            days_ago = (datetime.utcnow() - last_date).days

            if days_ago == 0:  # Today
                return 10.0  # Max
            elif days_ago <= 1:  # Yesterday
                return 8.0
            elif days_ago <= 3:  # Within 3 days
                return 6.0
            elif days_ago <= 7:  # Within week
                return 3.0
            else:  # Older than week
                return 0.0

        except Exception:
            return 5.0

    def _estimate_days_span(self, timestamps: List[str]) -> int:
        """Estima días entre primer y último mensaje."""
        if len(timestamps) < 2:
            return 0

        try:
            first_date = datetime.fromisoformat(timestamps[0])
            last_date = datetime.fromisoformat(timestamps[-1])
            return (last_date - first_date).days
        except Exception:
            return 0

    async def get_leads_by_temperature(
        self,
        leads: List[LeadScore],
        temperature: LeadTemperature,
    ) -> List[LeadScore]:
        """Filtra leads por temperatura."""
        return [lead for lead in leads if lead.temperature == temperature]

    async def prioritize_leads(self, leads: List[LeadScore]) -> List[LeadScore]:
        """Ordena leads por priority (hot → warm → cold, y dentro de cada grupo por score)."""
        temp_order = {LeadTemperature.HOT: 0, LeadTemperature.WARM: 1, LeadTemperature.COLD: 2}

        return sorted(
            leads,
            key=lambda l: (temp_order[l.temperature], -l.score),
        )


def get_lead_scoring_service() -> LeadScoringService:
    return LeadScoringService()
