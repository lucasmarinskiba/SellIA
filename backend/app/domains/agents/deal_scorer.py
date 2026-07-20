"""Predictive Deal Scorer

Calculates a 0-100 deal score based on 8 weighted factors
using conversation data, memory, and emotions.
"""

import uuid
from typing import Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.core.logger import get_logger
from app.domains.channels.models import Conversation, Message
from app.domains.memory.models import ConversationMemoryChunk, CustomerMemory
from app.domains.crm.models import Deal, LeadStage

try:
    from app.domains.emotion.models import EmotionDetection
except ImportError:
    EmotionDetection = None

logger = get_logger(__name__)

# Business-type-adaptive weights for deal scoring
DEFAULT_WEIGHTS = {
    "engagement_rate": 0.20,
    "objection_handling": 0.20,
    "emotional_positivity": 0.15,
    "tool_usage": 0.10,
    "customer_profile_match": 0.10,
    "conversation_stage": 0.10,
    "response_consistency": 0.10,
    "price_sensitivity": 0.05,
}

BUSINESS_TYPE_WEIGHTS = {
    "services": {
        "engagement_rate": 0.25,
        "objection_handling": 0.25,
        "emotional_positivity": 0.15,
        "tool_usage": 0.05,
        "customer_profile_match": 0.15,
        "conversation_stage": 0.10,
        "response_consistency": 0.05,
        "price_sensitivity": 0.00,
    },
    "consulting": {
        "engagement_rate": 0.20,
        "objection_handling": 0.25,
        "emotional_positivity": 0.15,
        "tool_usage": 0.05,
        "customer_profile_match": 0.20,
        "conversation_stage": 0.10,
        "response_consistency": 0.05,
        "price_sensitivity": 0.00,
    },
    "software": {
        "engagement_rate": 0.15,
        "objection_handling": 0.20,
        "emotional_positivity": 0.10,
        "tool_usage": 0.20,
        "customer_profile_match": 0.20,
        "conversation_stage": 0.10,
        "response_consistency": 0.05,
        "price_sensitivity": 0.00,
    },
    "physical_products": {
        "engagement_rate": 0.15,
        "objection_handling": 0.15,
        "emotional_positivity": 0.10,
        "tool_usage": 0.20,
        "customer_profile_match": 0.05,
        "conversation_stage": 0.10,
        "response_consistency": 0.10,
        "price_sensitivity": 0.15,
    },
    "digital_products": {
        "engagement_rate": 0.15,
        "objection_handling": 0.15,
        "emotional_positivity": 0.10,
        "tool_usage": 0.20,
        "customer_profile_match": 0.10,
        "conversation_stage": 0.10,
        "response_consistency": 0.10,
        "price_sensitivity": 0.10,
    },
    "food_beverage": {
        "engagement_rate": 0.20,
        "objection_handling": 0.10,
        "emotional_positivity": 0.15,
        "tool_usage": 0.15,
        "customer_profile_match": 0.05,
        "conversation_stage": 0.10,
        "response_consistency": 0.10,
        "price_sensitivity": 0.15,
    },
    "fashion_beauty": {
        "engagement_rate": 0.15,
        "objection_handling": 0.10,
        "emotional_positivity": 0.20,
        "tool_usage": 0.20,
        "customer_profile_match": 0.05,
        "conversation_stage": 0.10,
        "response_consistency": 0.10,
        "price_sensitivity": 0.10,
    },
    "health_wellness": {
        "engagement_rate": 0.20,
        "objection_handling": 0.20,
        "emotional_positivity": 0.20,
        "tool_usage": 0.05,
        "customer_profile_match": 0.15,
        "conversation_stage": 0.10,
        "response_consistency": 0.10,
        "price_sensitivity": 0.00,
    },
    "home_decor": {
        "engagement_rate": 0.15,
        "objection_handling": 0.10,
        "emotional_positivity": 0.10,
        "tool_usage": 0.20,
        "customer_profile_match": 0.05,
        "conversation_stage": 0.10,
        "response_consistency": 0.10,
        "price_sensitivity": 0.20,
    },
    "handcraft": {
        "engagement_rate": 0.20,
        "objection_handling": 0.15,
        "emotional_positivity": 0.20,
        "tool_usage": 0.10,
        "customer_profile_match": 0.10,
        "conversation_stage": 0.10,
        "response_consistency": 0.10,
        "price_sensitivity": 0.05,
    },
}

# ── Stage score mapping ──────────────────────────────────────────────
_LEAD_STAGE_SCORES = {
    LeadStage.NEW_LEAD: 10,
    LeadStage.CONTACTED: 25,
    LeadStage.QUALIFIED: 40,
    LeadStage.PROPOSAL_SENT: 60,
    LeadStage.NEGOTIATING: 75,
    LeadStage.CLOSED_WON: 100,
    LeadStage.CLOSED_LOST: 0,
    LeadStage.NURTURE: 20,
}

# ── Price-related keywords for sensitivity detection ─────────────────
_PRICE_KEYWORDS = {
    "precio", "price", "costo", "cost", "descuento", "discount",
    "barato", "cheap", "caro", "expensive", "oferta", "offer",
    "promoción", "promotion", "cuánto cuesta", "how much",
    "presupuesto", "budget", "pago", "payment", "pagos", "payments",
    "cuota", "installment", "financiación", "financing",
    "negociar", "negotiate", "rebaja", "rebate",
}

# ── Question markers ─────────────────────────────────────────────────
_QUESTION_MARKERS = {"?", "¿", "cuál", "cual", "cuáles", "cuales",
                     "qué", "que", "cómo", "como", "por qué", "porque",
                     "quién", "quien", "cuándo", "cuando", "dónde", "donde",
                     "cuánto", "cuanto", "cuántos", "cuantos"}


class DealScoreResult:
    """Result of a deal score calculation."""

    def __init__(
        self,
        score: int,
        category: str,
        factors: Dict[str, Any],
        recommendation: str,
        previous_score: Optional[int] = None,
        score_change: Optional[int] = None,
    ):
        self.score = score
        self.category = category
        self.factors = factors
        self.recommendation = recommendation
        self.previous_score = previous_score
        self.score_change = score_change


class DealScorer:
    """Calculates predictive deal scores for conversations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_business_type(self, business_id: Optional[uuid.UUID]) -> Optional[str]:
        """Load specific business type from BusinessContext."""
        if not business_id:
            return None
        try:
            from sqlalchemy import select
            from app.domains.business_context.models import BusinessContext
            result = await self.db.execute(
                select(BusinessContext.business_type).where(
                    BusinessContext.business_id == business_id,
                    BusinessContext.is_active == True,
                )
            )
            btype = result.scalar_one_or_none()
            return btype.value if btype else None
        except Exception as exc:
            logger.debug(f"Could not load business_type for deal scoring: {exc}")
            return None

    # ═══════════════════════════════════════════════════════════════════
    # Public API
    # ═══════════════════════════════════════════════════════════════════

    async def calculate_deal_score(
        self,
        conversation_id: uuid.UUID,
    ) -> DealScoreResult:
        """Calculate the full deal score for a conversation."""

        # Load conversation
        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Load messages
        msg_result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        messages = msg_result.scalars().all()

        # Load memory chunks
        chunk_result = await self.db.execute(
            select(ConversationMemoryChunk)
            .where(ConversationMemoryChunk.conversation_id == conversation_id)
            .order_by(ConversationMemoryChunk.created_at.asc())
        )
        chunks = chunk_result.scalars().all()

        # Load customer memories
        customer_id = None
        if chunks:
            customer_id = chunks[0].user_id

        memories = []
        if customer_id and conversation.business_id:
            mem_result = await self.db.execute(
                select(CustomerMemory).where(
                    CustomerMemory.business_id == conversation.business_id,
                    CustomerMemory.customer_id == customer_id,
                )
            )
            memories = mem_result.scalars().all()

        # Load deal (if any)
        deal_result = await self.db.execute(
            select(Deal).where(Deal.conversation_id == conversation_id)
        )
        deal = deal_result.scalar_one_or_none()

        # ── Compute factors ────────────────────────────────────────────
        factors: Dict[str, Any] = {}

        factors["engagement_rate"] = self._compute_engagement(messages)
        factors["objection_handling"] = self._compute_objection_handling(
            messages, memories
        )
        factors["emotional_positivity"] = await self._compute_emotional_positivity(
            conversation_id, messages
        )
        factors["tool_usage"] = self._compute_tool_usage(messages)
        factors["customer_profile_match"] = self._compute_profile_match(memories)
        factors["conversation_stage"] = self._compute_conversation_stage(deal)
        factors["response_consistency"] = self._compute_response_consistency(messages)
        factors["price_sensitivity"] = self._compute_price_sensitivity(messages)

        # ── Load business type for adaptive weights ────────────────────
        business_type = await self._get_business_type(conversation.business_id)
        weights = BUSINESS_TYPE_WEIGHTS.get(business_type, DEFAULT_WEIGHTS)

        raw_score = sum(
            factors.get(key, 0) * weight for key, weight in weights.items()
        )
        score = max(0, min(100, int(round(raw_score))))

        category = self._score_to_category(score)
        recommendation = self.generate_recommendation(score, factors)

        return DealScoreResult(
            score=score,
            category=category,
            factors=factors,
            recommendation=recommendation,
        )

    def generate_recommendation(self, score: int, factors: Dict[str, Any]) -> str:
        """Generate a recommendation based on score and factors."""
        if score <= 25:
            return "Enviar contenido de valor, no presionar"
        elif score <= 50:
            return "Hacer descubrimiento, identificar pain points"
        elif score <= 75:
            return "Presentar propuesta, manejar objeciones"
        else:
            return "Cerrar ahora, ofrecer incentivo de urgencia"

    def detect_score_drop(self, current_score: int, previous_score: int) -> bool:
        """Alert if score drops by more than 15 points."""
        if previous_score is None:
            return False
        return (previous_score - current_score) > 15

    # ═══════════════════════════════════════════════════════════════════
    # Factor computations
    # ═══════════════════════════════════════════════════════════════════

    def _compute_engagement(self, messages) -> int:
        """Messages per hour, response time, questions asked → 0-100."""
        if not messages:
            return 0

        inbound = [m for m in messages if getattr(m, "direction", None) == "inbound"]
        outbound = [m for m in messages if getattr(m, "direction", None) == "outbound"]

        # Questions asked by customer
        question_count = 0
        for m in inbound:
            content = (m.content or "").lower()
            if any(q in content for q in _QUESTION_MARKERS):
                question_count += 1

        # Messages per hour
        times = [m.created_at for m in messages if m.created_at]
        if len(times) >= 2:
            duration_hours = max(
                (max(times) - min(times)).total_seconds() / 3600, 0.5
            )
            mph = len(messages) / duration_hours
        else:
            mph = len(messages)

        # Response time (avg seconds between inbound and next outbound)
        response_times = []
        for i, m in enumerate(messages):
            if getattr(m, "direction", None) == "inbound" and i + 1 < len(messages):
                nxt = messages[i + 1]
                if getattr(nxt, "direction", None) == "outbound" and m.created_at and nxt.created_at:
                    response_times.append((nxt.created_at - m.created_at).total_seconds())

        avg_response_sec = sum(response_times) / len(response_times) if response_times else 3600

        # Score components
        msg_score = min(mph * 10, 40)  # up to 40 pts
        question_score = min(question_count * 5, 30)  # up to 30 pts
        response_score = 30 if avg_response_sec < 300 else (20 if avg_response_sec < 900 else 10)

        return min(100, msg_score + question_score + response_score)

    def _compute_objection_handling(self, messages, memories) -> int:
        """Objections raised vs overcome → 0-100."""
        objections_raised = 0
        objections_overcome = 0

        # Count from customer memories
        for mem in memories:
            if getattr(mem, "memory_type", None) == "objection":
                objections_raised += 1
                content = (mem.content or "").lower()
                if any(w in content for w in {"superado", "overcome", "resuelto", "resolved", "aceptado", "accepted"}):
                    objections_overcome += 1

        # Fallback: scan messages for objection keywords
        if objections_raised == 0:
            objection_keywords = {
                "no tengo dinero", "no puedo pagar", "es caro", "too expensive",
                "no me interesa", "not interested", "lo pensaré", "i'll think about it",
                "no es momento", "not the right time", "necesito consultar", "need to ask",
                "ya tengo", "already have", "no confío", "don't trust",
            }
            for m in messages:
                content = (m.content or "").lower()
                if any(kw in content for kw in objection_keywords):
                    objections_raised += 1
                    # Simple heuristic: if agent replied with reassurance
                    # we count it as partially overcome
                    objections_overcome += 0.5

        if objections_raised == 0:
            return 75  # No objections = neutral-good

        ratio = objections_overcome / objections_raised
        return int(40 + ratio * 60)  # 40-100 based on ratio

    async def _compute_emotional_positivity(
        self, conversation_id: uuid.UUID, messages
    ) -> int:
        """Percentage of messages with positive emotion → 0-100."""
        if EmotionDetection is None:
            # Fallback heuristic: positive words vs negative words
            return self._heuristic_emotional_positivity(messages)

        result = await self.db.execute(
            select(EmotionDetection).where(
                EmotionDetection.conversation_id == conversation_id
            )
        )
        emotions = result.scalars().all()

        if not emotions:
            return self._heuristic_emotional_positivity(messages)

        positive = sum(
            1 for e in emotions
            if getattr(e, "sentiment", "").lower() in ("positive", "positivo", "happy", "excited")
        )
        return int((positive / len(emotions)) * 100)

    def _heuristic_emotional_positivity(self, messages) -> int:
        """Simple keyword-based emotional positivity."""
        positive_words = {
            "genial", "great", "excelente", "excellent", "me encanta", "love it",
            "perfecto", "perfect", "gracias", "thanks", "fantástico", "fantastic",
            "increíble", "incredible", "feliz", "happy", "emocionado", "excited",
            "interesado", "interested", "sí", "yes", "claro", "sure", "ok",
            "bueno", "good", "me gusta", "like", "amazing", "asombroso",
        }
        negative_words = {
            "malo", "bad", "terrible", "horrible", "odio", "hate", "no", "never",
            "nunca", "jamás", "jamás", "peor", "worst", "molesto", "annoyed",
            "enojado", "angry", "frustrado", "frustrated", "decepcionado", "disappointed",
            "caro", "expensive", "estafa", "scam", "basura", "trash",
        }

        pos_count = 0
        neg_count = 0
        total = 0

        for m in messages:
            content = (m.content or "").lower()
            if not content:
                continue
            total += 1
            if any(w in content for w in positive_words):
                pos_count += 1
            elif any(w in content for w in negative_words):
                neg_count += 1

        if total == 0:
            return 50

        return max(0, min(100, 50 + int((pos_count - neg_count) / total * 50)))

    def _compute_tool_usage(self, messages) -> int:
        """How many tools the agent used → 0-100."""
        tool_count = 0
        for m in messages:
            extra = getattr(m, "extra_data", {}) or {}
            if isinstance(extra, dict):
                if extra.get("tool_calls") or extra.get("tools") or extra.get("actions"):
                    tool_count += len(extra.get("tool_calls", [])) or len(extra.get("tools", [])) or 1
                # Also check for function_call legacy format
                if extra.get("function_call"):
                    tool_count += 1

        # Score: 0 tools = 30, 1-2 = 50, 3-5 = 70, 6+ = 90-100
        if tool_count == 0:
            return 30
        elif tool_count <= 2:
            return 50
        elif tool_count <= 5:
            return 70
        else:
            return min(100, 80 + tool_count * 2)

    def _compute_profile_match(self, memories) -> int:
        """How well we know the customer → 0-100."""
        if not memories:
            return 20

        # Score based on memory diversity and confidence
        memory_types = set()
        total_confidence = 0.0
        for mem in memories:
            memory_types.add(getattr(mem, "memory_type", "unknown"))
            total_confidence += getattr(mem, "confidence", 0.0)

        type_score = min(len(memory_types) * 15, 60)  # up to 60 pts for diversity
        conf_score = min((total_confidence / max(len(memories), 1)) * 40, 40)  # up to 40 pts

        return min(100, type_score + conf_score)

    def _compute_conversation_stage(self, deal: Optional[Deal]) -> int:
        """More advanced pipeline stage = better → 0-100."""
        if deal and deal.stage:
            return _LEAD_STAGE_SCORES.get(deal.stage, 25)
        return 10  # Default: new lead

    def _compute_response_consistency(self, messages) -> int:
        """Customer responds regularly vs disappears → 0-100."""
        inbound = [m for m in messages if getattr(m, "direction", None) == "inbound"]
        if len(inbound) < 2:
            return 30

        times = sorted(m.created_at for m in inbound if m.created_at)
        gaps = []
        for i in range(1, len(times)):
            gaps.append((times[i] - times[i - 1]).total_seconds())

        if not gaps:
            return 50

        avg_gap = sum(gaps) / len(gaps)
        max_gap = max(gaps)

        # Score based on average gap and max gap
        # <1h avg = excellent, >24h avg = poor
        if avg_gap < 3600:
            score = 90
        elif avg_gap < 7200:
            score = 75
        elif avg_gap < 21600:
            score = 60
        elif avg_gap < 86400:
            score = 45
        else:
            score = 30

        # Penalize if max gap is >48h
        if max_gap > 172800:
            score -= 20
        elif max_gap > 86400:
            score -= 10

        return max(0, min(100, score))

    def _compute_price_sensitivity(self, messages) -> int:
        """If customer negotiated a lot, lower score → 0-100 (inverse)."""
        price_mentions = 0
        negotiation_signals = 0

        for m in messages:
            content = (m.content or "").lower()
            if any(kw in content for kw in _PRICE_KEYWORDS):
                price_mentions += 1
            if any(kw in content for kw in {
                "más barato", "cheaper", "descuento", "discount",
                "mejor precio", "better price", "competencia", "competitor",
                "otro lugar", "somewhere else", "oferta", "ofertas", "offers",
            }):
                negotiation_signals += 1

        # More price talk = lower score (but some is normal)
        # 0 mentions = 90, 1-2 = 75, 3-5 = 55, 6+ = 35
        total = price_mentions + negotiation_signals * 2
        if total == 0:
            return 90
        elif total <= 2:
            return 75
        elif total <= 5:
            return 55
        else:
            return max(20, 40 - total * 2)

    # ═══════════════════════════════════════════════════════════════════
    # Helpers
    # ═══════════════════════════════════════════════════════════════════

    def _score_to_category(self, score: int) -> str:
        if score <= 25:
            return "cold"
        elif score <= 50:
            return "warm"
        elif score <= 75:
            return "hot"
        return "ready"
