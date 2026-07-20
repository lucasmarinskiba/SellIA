"""Message Intelligence & Intent Detection Service.

Analyzes every inbound message with LLM to detect sentiment, intent, objections,
pain points, buying signals, and recommends next actions.
"""

import uuid
import json
import re
from datetime import datetime, timezone
from typing import Optional, Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.intelligence.models import MessageAnalysis, ConversationIntelligence
from app.domains.channels.models import Message, Conversation
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.core.logger import get_logger
from app.core.events import event_bus

logger = get_logger(__name__)

INTELLIGENCE_PROMPT = """Analiza el siguiente mensaje de un lead potencial o cliente.

MENSAJE: "{message_content}"

Contexto adicional:
- Historial de la conversación: {context_summary}
- Productos/servicios del negocio: {business_context}

Responde ÚNICAMENTE en JSON válido con esta estructura exacta:
{{
  "sentiment_score": -1.0 a 1.0,
  "sentiment_label": "positive" | "negative" | "neutral" | "mixed",
  "intent_type": "buy" | "price_inquiry" | "support" | "complaint" | "appointment" | "demo" | "objection" | "churn_risk" | "referral" | "neutral",
  "intent_confidence": 0.0 a 1.0,
  "objections_detected": ["too_expensive", "need_to_think", "bad_timing", "competitor_cheaper", "no_budget", "not_interested"],
  "pain_points_detected": ["slow_process", "bad_experience", "high_cost", "lack_of_features", "poor_support"],
  "buying_signals_detected": ["asks_price", "asks_availability", "requests_demo", "asks_payment_methods", "urgent_need", "comparison_shopping"],
  "urgency_level": "low" | "medium" | "high" | "critical",
  "language_detected": "es" | "en" | "pt",
  "key_entities": {{
    "products": [],
    "prices": [],
    "dates": [],
    "locations": []
  }},
  "recommended_action": "send_proposal" | "schedule_demo" | "send_followup" | "escalate_human" | "offer_discount" | "send_nurture" | "none",
  "recommended_personality": "vendedor" | "post-venta" | "soporte" | "cerrador" | "captador"
}}

Reglas:
- sentiment_score: negativo = cliente enojado o insatisfecho, positivo = entusiasmado, 0 = neutral
- intent_type: "buy" si muestra intención clara de compra, "objection" si pone excusas, "churn_risk" si muestra insatisfacción severa
- objections_detected: solo incluye objeciones reales detectadas en el texto
- buying_signals_detected: solo incluye señales reales detectadas
- urgency_level: "critical" si usa palabras como "urgente", "ahora", "hoy", "inmediato"
- recommended_action: basado en la intención y el estado emocional del lead
- recommended_personality: el agente más adecuado para responder
"""


class MessageIntelligenceService:
    """Analyzes messages using LLM for sentiment, intent, and signals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_message(self, message_id: uuid.UUID) -> Optional[MessageAnalysis]:
        """Analyze a single message and store results."""
        # Check if already analyzed
        existing = await self.db.execute(
            select(MessageAnalysis).where(MessageAnalysis.message_id == message_id)
        )
        if existing.scalar_one_or_none():
            return None

        # Get message
        msg_result = await self.db.execute(
            select(Message).where(Message.id == message_id)
        )
        message = msg_result.scalar_one_or_none()
        if not message or message.direction != "inbound":
            return None

        # Get conversation context
        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id == message.conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()
        if not conversation:
            return None

        # Get recent messages for context
        recent_result = await self.db.execute(
            select(Message).where(
                Message.conversation_id == conversation.id,
            ).order_by(desc(Message.created_at)).limit(5)
        )
        recent_messages = recent_result.scalars().all()
        context_summary = " | ".join([
            f"{'Cliente' if m.direction == 'inbound' else 'Sistema'}: {m.content[:100]}"
            for m in reversed(recent_messages)
        ])

        # Get business context (catalog summary)
        from app.domains.businesses.models import Business
        from app.domains.catalogs.models import CatalogItem
        biz_result = await self.db.execute(
            select(Business).where(Business.id == conversation.business_id)
        )
        business = biz_result.scalar_one_or_none()
        business_context = ""
        if business:
            catalog_result = await self.db.execute(
                select(CatalogItem).where(
                    CatalogItem.business_id == business.id,
                    CatalogItem.is_active == True,
                ).limit(5)
            )
            items = catalog_result.scalars().all()
            business_context = ", ".join([f"{i.name} (${i.price})" for i in items])

        # Build prompt
        prompt = INTELLIGENCE_PROMPT.format(
            message_content=message.content,
            context_summary=context_summary,
            business_context=business_context or "No disponible",
        )

        try:
            # Call LLM
            response_text = await generate_raw_ai_response(
                db=self.db,
                business_id=conversation.business_id,
                system_prompt="Eres un analista de ventas experto. Analizas mensajes de leads para detectar intención, sentimiento, objeciones y señales de compra. Respondes ÚNICAMENTE en JSON válido.",
                user_prompt=prompt,
                max_tokens=1500,
                temperature=0.2,  # Low temp for consistent JSON
            )

            if not response_text:
                logger.warning(f"No response from LLM for message {message_id}")
                return None

            # Parse JSON
            analysis_data = self._extract_json(response_text)
            if not analysis_data:
                logger.warning(f"Could not parse JSON from LLM response for message {message_id}")
                return None

            # Create analysis record
            analysis = MessageAnalysis(
                business_id=conversation.business_id,
                conversation_id=conversation.id,
                message_id=message.id,
                sentiment_score=float(analysis_data.get("sentiment_score", 0)),
                sentiment_label=analysis_data.get("sentiment_label", "neutral"),
                intent_type=analysis_data.get("intent_type", "neutral"),
                intent_confidence=float(analysis_data.get("intent_confidence", 0)),
                objections_detected=analysis_data.get("objections_detected", []),
                pain_points_detected=analysis_data.get("pain_points_detected", []),
                buying_signals_detected=analysis_data.get("buying_signals_detected", []),
                urgency_level=analysis_data.get("urgency_level", "low"),
                language_detected=analysis_data.get("language_detected", "es"),
                key_entities=analysis_data.get("key_entities", {}),
                recommended_action=analysis_data.get("recommended_action"),
                recommended_personality=analysis_data.get("recommended_personality"),
                raw_analysis=analysis_data,
            )
            self.db.add(analysis)
            await self.db.commit()
            await self.db.refresh(analysis)

            # Update conversation intelligence
            await self._update_conversation_intelligence(conversation.id)

            # Emit events
            await self._emit_events(analysis, conversation)

            logger.info(
                f"Analyzed message {message_id}: intent={analysis.intent_type}, "
                f"sentiment={analysis.sentiment_label}, confidence={analysis.intent_confidence}"
            )
            return analysis

        except Exception as e:
            logger.exception(f"Failed to analyze message {message_id}: {e}")
            return None

    def _extract_json(self, text: str) -> Optional[dict]:
        """Extract JSON from LLM response (handles markdown code blocks)."""
        # Try to find JSON in markdown code block
        match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
        if match:
            text = match.group(1).strip()

        # Try to find JSON between braces
        if not text.strip().startswith('{'):
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                text = match.group(0)

        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return None

    async def _update_conversation_intelligence(self, conversation_id: uuid.UUID) -> None:
        """Recalculate aggregated intelligence for a conversation."""
        # Get all analyses for this conversation
        result = await self.db.execute(
            select(MessageAnalysis).where(
                MessageAnalysis.conversation_id == conversation_id,
            ).order_by(desc(MessageAnalysis.created_at))
        )
        analyses = result.scalars().all()

        if not analyses:
            return

        # Calculate aggregates
        total = len(analyses)
        avg_sentiment = sum(a.sentiment_score for a in analyses) / total
        positive_count = sum(1 for a in analyses if a.sentiment_label == "positive")
        negative_count = sum(1 for a in analyses if a.sentiment_label == "negative")
        buying_signals_count = sum(len(a.buying_signals_detected) for a in analyses)
        churn_signals = sum(1 for a in analyses if a.intent_type == "churn_risk")

        # Determine dominant intent
        intents = {}
        for a in analyses:
            intents[a.intent_type] = intents.get(a.intent_type, 0) + 1
        dominant_intent = max(intents, key=intents.get) if intents else "neutral"

        # Determine sentiment trend
        if total >= 3:
            recent_avg = sum(a.sentiment_score for a in analyses[:3]) / 3
            older_avg = sum(a.sentiment_score for a in analyses[-3:]) / 3
            if recent_avg > older_avg + 0.2:
                trend = "improving"
            elif recent_avg < older_avg - 0.2:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        # Calculate buying readiness (0-100)
        readiness = min(100, int(
            (avg_sentiment + 1) * 15 +  # sentiment contribution (0-30)
            (buying_signals_count / max(total, 1)) * 30 +  # signals per message (0-30)
            (intents.get("buy", 0) / max(total, 1)) * 20 +  # buy intent frequency (0-20)
            max(0, 20 - churn_signals * 5)  # churn penalty (0-20)
        ))

        # Determine next best action
        latest = analyses[0]
        next_action = latest.recommended_action
        next_reason = f"Último mensaje: intent={latest.intent_type}, sentiment={latest.sentiment_label}, urgency={latest.urgency_level}"

        # Upsert conversation intelligence
        conv_intel_result = await self.db.execute(
            select(ConversationIntelligence).where(
                ConversationIntelligence.conversation_id == conversation_id,
            )
        )
        conv_intel = conv_intel_result.scalar_one_or_none()
        if not conv_intel:
            from app.domains.channels.models import Conversation
            conv_result = await self.db.execute(
                select(Conversation).where(Conversation.id == conversation_id)
            )
            conv = conv_result.scalar_one_or_none()
            conv_intel = ConversationIntelligence(
                business_id=conv.business_id if conv else None,
                conversation_id=conversation_id,
            )
            self.db.add(conv_intel)

        conv_intel.overall_sentiment_trend = trend
        conv_intel.average_sentiment_score = avg_sentiment
        conv_intel.dominant_intent = dominant_intent
        conv_intel.buying_readiness_score = readiness
        conv_intel.churn_risk_signals_count = churn_signals
        conv_intel.next_best_action = next_action
        conv_intel.next_best_action_reason = next_reason
        conv_intel.total_messages_analyzed = total
        conv_intel.positive_messages_count = positive_count
        conv_intel.negative_messages_count = negative_count
        conv_intel.buying_signals_count = buying_signals_count

        await self.db.commit()

    async def _emit_events(self, analysis: MessageAnalysis, conversation: Conversation) -> None:
        """Emit events based on analysis results."""
        # Emit message analyzed event
        await event_bus.emit("message.analyzed", {
            "message_id": str(analysis.message_id),
            "conversation_id": str(analysis.conversation_id),
            "business_id": str(analysis.business_id),
            "intent_type": analysis.intent_type,
            "sentiment_label": analysis.sentiment_label,
            "urgency_level": analysis.urgency_level,
        })

        # Emit intent detected
        if analysis.intent_type != "neutral" and analysis.intent_confidence >= 0.6:
            await event_bus.emit("intent.detected", {
                "conversation_id": str(analysis.conversation_id),
                "business_id": str(analysis.business_id),
                "intent_type": analysis.intent_type,
                "confidence": float(analysis.intent_confidence),
                "recommended_action": analysis.recommended_action,
            })

        # Emit buying signal
        if analysis.buying_signals_detected:
            await event_bus.emit("buying_signal.detected", {
                "conversation_id": str(analysis.conversation_id),
                "business_id": str(analysis.business_id),
                "signals": analysis.buying_signals_detected,
                "urgency": analysis.urgency_level,
            })

        # Emit objection raised
        if analysis.objections_detected:
            await event_bus.emit("objection.raised", {
                "conversation_id": str(analysis.conversation_id),
                "business_id": str(analysis.business_id),
                "objections": analysis.objections_detected,
            })

        # Emit churn risk
        if analysis.intent_type == "churn_risk" or analysis.sentiment_score < -0.5:
            await event_bus.emit("churn_risk.detected", {
                "conversation_id": str(analysis.conversation_id),
                "business_id": str(analysis.business_id),
                "sentiment_score": float(analysis.sentiment_score),
            })

    async def get_pending_messages(self, limit: int = 100) -> list[Message]:
        """Get inbound messages that haven't been analyzed yet."""
        result = await self.db.execute(
            select(Message).where(
                Message.direction == "inbound",
            ).outerjoin(
                MessageAnalysis, MessageAnalysis.message_id == Message.id
            ).where(
                MessageAnalysis.id == None
            ).order_by(desc(Message.created_at)).limit(limit)
        )
        return result.scalars().all()

    async def analyze_pending_messages(self) -> int:
        """Analyze all pending messages. Returns count analyzed."""
        messages = await self.get_pending_messages(limit=50)
        analyzed = 0
        for msg in messages:
            result = await self.analyze_message(msg.id)
            if result:
                analyzed += 1
        return analyzed


class ConversationIntelligenceService:
    """Aggregated conversation intelligence queries."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_conversation(self, conversation_id: uuid.UUID) -> Optional[ConversationIntelligence]:
        result = await self.db.execute(
            select(ConversationIntelligence).where(
                ConversationIntelligence.conversation_id == conversation_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_hot_leads(self, business_id: uuid.UUID, min_readiness: int = 60) -> list[ConversationIntelligence]:
        result = await self.db.execute(
            select(ConversationIntelligence).where(
                ConversationIntelligence.business_id == business_id,
                ConversationIntelligence.buying_readiness_score >= min_readiness,
            ).order_by(desc(ConversationIntelligence.buying_readiness_score)).limit(50)
        )
        return result.scalars().all()

    async def get_at_risk_conversations(self, business_id: uuid.UUID) -> list[ConversationIntelligence]:
        result = await self.db.execute(
            select(ConversationIntelligence).where(
                ConversationIntelligence.business_id == business_id,
                ConversationIntelligence.churn_risk_signals_count >= 2,
            ).order_by(desc(ConversationIntelligence.churn_risk_signals_count)).limit(50)
        )
        return result.scalars().all()
