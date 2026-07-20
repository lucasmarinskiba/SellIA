"""Warm Lead Detector — Detecta cuando un lead frío empieza a calentarse automáticamente.

Monitorea señales de comportamiento que indican interés creciente:
- Vuelve a abrir mensajes
- Clickea links
- Responde después de días de silencio
- Pregunta por precio/detalle específico
- Visita la web/bio link

Cuando detecta calentamiento, activa secuencias de aceleración automáticamente.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Any, List

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.growth.models import InboundLead, NurturingStage
from app.domains.crm.models import LeadScore
from app.domains.channels.models import Conversation, Message
from app.core.logger import get_logger
from app.core.events import event_bus

logger = get_logger(__name__)


class WarmLeadDetector:
    """Detects when cold leads start warming up and triggers acceleration."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def scan_for_warming_leads(
        self,
        business_id: uuid.UUID,
        lookback_hours: int = 24,
    ) -> List[dict]:
        """Scan for leads showing warming signals in the last N hours."""
        since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)

        warming_leads = []

        # Find leads who were cold/dormant but showed activity recently
        result = await self.db.execute(
            select(InboundLead, Conversation).join(
                Conversation, InboundLead.conversation_id == Conversation.id
            ).where(
                InboundLead.business_id == business_id,
                InboundLead.is_active == True,
                InboundLead.nurturing_stage.in_([
                    NurturingStage.NEW,
                    NurturingStage.AWARENESS,
                    NurturingStage.DORMANT,
                ]),
            )
        )

        for lead, conv in result.all():
            signals = await self._analyze_warming_signals(lead, conv, since)
            if signals["score"] >= 3:
                warming_leads.append({
                    "lead_id": str(lead.id),
                    "conversation_id": str(conv.id),
                    "previous_stage": lead.nurturing_stage.value,
                    "warming_score": signals["score"],
                    "signals_detected": signals["details"],
                })

                # Auto-advance stage
                await self._advance_stage(lead, signals["score"])

        return warming_leads

    async def _analyze_warming_signals(
        self,
        lead: InboundLead,
        conv: Conversation,
        since: datetime,
    ) -> dict[str, Any]:
        """Analyze all warming signals for a lead."""
        score = 0
        details = []

        # Signal 1: Replied after long silence (> 7 days)
        last_msg_result = await self.db.execute(
            select(Message).where(
                Message.conversation_id == conv.id,
                Message.direction == "inbound",
                Message.created_at >= since,
            ).order_by(desc(Message.created_at)).limit(1)
        )
        last_inbound = last_msg_result.scalar_one_or_none()

        if last_inbound:
            # Check gap since previous message
            prev_msg_result = await self.db.execute(
                select(Message).where(
                    Message.conversation_id == conv.id,
                    Message.direction == "inbound",
                    Message.created_at < last_inbound.created_at,
                ).order_by(desc(Message.created_at)).limit(1)
            )
            prev_msg = prev_msg_result.scalar_one_or_none()

            if prev_msg:
                gap_days = (last_inbound.created_at - prev_msg.created_at).days
                if gap_days >= 7:
                    score += 2
                    details.append(f"replied_after_{gap_days}d_silence")
                else:
                    score += 1
                    details.append("new_reply")

        # Signal 2: Multiple messages in short window
        msg_count_result = await self.db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conv.id,
                Message.direction == "inbound",
                Message.created_at >= since,
            )
        )
        msg_count = msg_count_result.scalar() or 0
        if msg_count >= 3:
            score += 2
            details.append("high_message_frequency")
        elif msg_count >= 2:
            score += 1
            details.append("multiple_messages")

        # Signal 3: Asked about price/product specifically
        if last_inbound and last_inbound.content:
            content_lower = last_inbound.content.lower()
            price_keywords = ["precio", "cuanto", "cuánto", "costo", "valor", "price", "cost", "cuanto sale", "precios"]
            if any(kw in content_lower for kw in price_keywords):
                score += 3
                details.append("price_inquiry")

            buy_keywords = ["comprar", "ordenar", "quiero", "me interesa", "disponible", "stock", "buy", "order"]
            if any(kw in content_lower for kw in buy_keywords):
                score += 2
                details.append("buying_intent_keywords")

        # Signal 4: Lead score increased significantly
        if lead.engagement_score >= 20:
            score += 1
            details.append("high_engagement_score")

        return {"score": score, "details": details}

    async def _advance_stage(self, lead: InboundLead, warming_score: int):
        """Advance nurturing stage based on warming signals."""
        old_stage = lead.nurturing_stage

        if warming_score >= 5:
            lead.nurturing_stage = NurturingStage.EVALUATION
        elif warming_score >= 3:
            lead.nurturing_stage = NurturingStage.CONSIDERATION
        else:
            return  # Not enough to advance

        lead.last_touch_at = datetime.now(timezone.utc)
        await self.db.commit()

        # Emit event for autopilot to act
        await event_bus.emit("lead.warming_detected", {
            "business_id": str(lead.business_id),
            "lead_id": str(lead.id),
            "conversation_id": str(lead.conversation_id) if lead.conversation_id else None,
            "old_stage": old_stage.value,
            "new_stage": lead.nurturing_stage.value,
            "warming_score": warming_score,
        })

        logger.info(
            f"Lead {lead.id} warmed up from {old_stage.value} to {lead.nurturing_stage.value} "
            f"(score: {warming_score})"
        )

    async def get_warming_report(
        self,
        business_id: uuid.UUID,
        days: int = 7,
    ) -> dict[str, Any]:
        """Get report of warming leads over time."""
        since = datetime.now(timezone.utc) - timedelta(days=days)

        result = await self.db.execute(
            select(func.count(InboundLead.id)).where(
                InboundLead.business_id == business_id,
                InboundLead.last_touch_at >= since,
                InboundLead.nurturing_stage.in_([
                    NurturingStage.CONSIDERATION,
                    NurturingStage.EVALUATION,
                ]),
            )
        )
        warmed_count = result.scalar() or 0

        converted_result = await self.db.execute(
            select(func.count(InboundLead.id)).where(
                InboundLead.business_id == business_id,
                InboundLead.converted_at >= since,
            )
        )
        converted_count = converted_result.scalar() or 0

        return {
            "period_days": days,
            "warmed_leads": warmed_count,
            "converted_leads": converted_count,
            "conversion_rate": round((converted_count / warmed_count * 100), 2) if warmed_count > 0 else 0,
            "trend": "improving" if warmed_count > 5 else "stable",
        }
