"""Proactive Outreach Engine

The system INITIATES conversations autonomously.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.outreach.models import OutreachLog, OutreachLogStatus
from app.domains.outreach.service import FatigueScoringService
from app.domains.channels.models import Conversation
from app.domains.crm.models import LeadScore, Deal
from app.domains.orders.models import Order
from app.domains.agents.ai_reply import generate_raw_ai_response
from app.core.logger import get_logger

logger = get_logger(__name__)

OUTREACH_TYPES = {
    "cold_reactivation": {
        "name": "Reactivación de leads fríos",
        "description": "Re-engage leads inactive >30 days with value content",
        "target_segment": "cold",
        "frequency_days": 30,
        "max_per_day": 10,
        "time_window_start": 9,
        "time_window_end": 18,
    },
    "warm_nurturing": {
        "name": "Nurturing de leads warm",
        "description": "Send relevant content every 3-5 days",
        "target_segment": "warm",
        "frequency_days": 4,
        "max_per_day": 15,
        "time_window_start": 9,
        "time_window_end": 20,
    },
    "hot_acceleration": {
        "name": "Aceleración de leads hot",
        "description": "Accelerated follow-up every 24h for hot leads",
        "target_segment": "hot",
        "frequency_days": 1,
        "max_per_day": 20,
        "time_window_start": 8,
        "time_window_end": 21,
    },
    "cart_recovery": {
        "name": "Recuperación de carrito",
        "description": "Recover abandoned carts with personalized message",
        "target_segment": "cart_abandoned",
        "frequency_days": 1,
        "max_per_day": 10,
        "time_window_start": 10,
        "time_window_end": 20,
    },
    "post_meeting": {
        "name": "Follow-up post-cita",
        "description": "Send summary + next steps after meeting",
        "target_segment": "post_meeting",
        "frequency_days": 1,
        "max_per_day": 20,
        "time_window_start": 9,
        "time_window_end": 18,
    },
    "churn_recovery": {
        "name": "Recuperación de churn",
        "description": "Win-back offer for at-risk customers",
        "target_segment": "at_risk",
        "frequency_days": 7,
        "max_per_day": 5,
        "time_window_start": 10,
        "time_window_end": 19,
    },
    "upsell": {
        "name": "Upsell / Cross-sell",
        "description": "Recommend complementary products to satisfied customers",
        "target_segment": "champions",
        "frequency_days": 14,
        "max_per_day": 5,
        "time_window_start": 10,
        "time_window_end": 20,
    },
    "referral_request": {
        "name": "Solicitud de referido",
        "description": "Ask champions for referrals",
        "target_segment": "champions",
        "frequency_days": 30,
        "max_per_day": 3,
        "time_window_start": 10,
        "time_window_end": 18,
    },
    "review_request": {
        "name": "Solicitud de review",
        "description": "Request NPS/review after purchase",
        "target_segment": "recent_buyers",
        "frequency_days": 7,
        "max_per_day": 10,
        "time_window_start": 10,
        "time_window_end": 20,
    },
    "birthday": {
        "name": "Saludo especial",
        "description": "Birthday/anniversary personalized message",
        "target_segment": "all_customers",
        "frequency_days": 365,
        "max_per_day": 20,
        "time_window_start": 9,
        "time_window_end": 21,
    },
}


class ProactiveOutreachEngine:
    """Generates and sends proactive outreach messages."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.fatigue = FatigueScoringService(db)

    async def generate_outreach(
        self,
        business_id: uuid.UUID,
        outreach_type: str,
        conversation_id: uuid.UUID,
    ) -> Optional[dict[str, Any]]:
        """Generate a proactive outreach message for a conversation."""
        config = OUTREACH_TYPES.get(outreach_type)
        if not config:
            return None

        # Check fatigue
        contact_check = await self.fatigue.can_contact_now(business_id, conversation_id)
        if not contact_check["can_contact"]:
            logger.info(f"Proactive outreach blocked by fatigue for conv {conversation_id}: {contact_check['reason']}")
            return None

        # Get conversation context
        conv_result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        conv = conv_result.scalar_one_or_none()
        if not conv:
            return None

        # Get lead score
        score_result = await self.db.execute(
            select(LeadScore).where(LeadScore.conversation_id == conversation_id)
        )
        score = score_result.scalar_one_or_none()

        # Get deal info
        deal_result = await self.db.execute(
            select(Deal).where(
                Deal.conversation_id == conversation_id,
                Deal.is_active == True,
            )
        )
        deal = deal_result.scalar_one_or_none()

        # Get last order
        order_result = await self.db.execute(
            select(Order).where(
                Order.conversation_id == conversation_id,
                Order.is_active == True,
            ).order_by(desc(Order.created_at)).limit(1)
        )
        last_order = order_result.scalar_one_or_none()

        # Build prompt
        prompt = self._build_outreach_prompt(
            outreach_type=outreach_type,
            config=config,
            conversation=conv,
            score=score,
            deal=deal,
            last_order=last_order,
        )

        try:
            # Generate message with AI
            message_content = await generate_raw_ai_response(
                db=self.db,
                business_id=business_id,
                system_prompt=f"Eres un experto en ventas de {config['name']}. Generas mensajes personalizados, cortos (máx 3 oraciones), y que generan valor sin ser invasivos. NUNCA uses placeholders como [nombre].",
                user_prompt=prompt,
                max_tokens=500,
                temperature=0.7,
            )

            if not message_content:
                return None

            # Record outreach
            log = OutreachLog(
                business_id=business_id,
                conversation_id=conversation_id,
                channel=contact_check.get("recommended_channel", "whatsapp"),
                message_type=outreach_type,
                message_content=message_content[:500],
                ai_generated=True,
            )
            self.db.add(log)
            await self.db.commit()
            await self.db.refresh(log)

            # Update fatigue
            await self.fatigue.record_contact(
                business_id=business_id,
                conversation_id=conversation_id,
                channel=log.channel,
                message_type=outreach_type,
                message_content=message_content,
                ai_generated=True,
            )

            logger.info(f"Generated proactive outreach {outreach_type} for conv {conversation_id}")
            return {
                "outreach_type": outreach_type,
                "conversation_id": str(conversation_id),
                "message": message_content,
                "channel": log.channel,
                "log_id": str(log.id),
            }

        except Exception as e:
            logger.exception(f"Failed to generate proactive outreach: {e}")
            return None

    def _build_outreach_prompt(
        self,
        outreach_type: str,
        config: dict,
        conversation: Conversation,
        score: Optional[LeadScore],
        deal: Optional[Deal],
        last_order: Optional[Order],
    ) -> str:
        """Build contextual prompt for outreach generation."""
        parts = [f"Tipo de outreach: {config['name']}"]
        parts.append(f"Descripción: {config['description']}")
        parts.append(f"Canal preferido: WhatsApp")
        parts.append(f"Lead: {conversation.lead_name or 'Cliente'}")
        parts.append(f"Canal de origen: {conversation.lead_source or 'desconocido'}")

        if score:
            parts.append(f"Lead score: {score.total_score} ({score.classification})")

        if deal:
            parts.append(f"Deal actual: {deal.title or 'Sin título'} - Stage: {deal.stage}")
            if deal.value:
                parts.append(f"Valor del deal: ${deal.value} {deal.currency}")

        if last_order:
            days_ago = (datetime.now(timezone.utc) - last_order.created_at).days if last_order.created_at else 0
            parts.append(f"Última compra: hace {days_ago} días - ${last_order.total_amount}")

        # Type-specific instructions
        if outreach_type == "cold_reactivation":
            parts.append("Instrucción: El lead estuvo inactivo 30+ días. Enviar mensaje de valor puro (tip, insight, noticia relevante) SIN pedir nada a cambio. Corto, amigable, sin presión.")
        elif outreach_type == "warm_nurturing":
            parts.append("Instrucción: Enviar contenido educativo relevante al negocio. Puede ser un tip, caso de éxito, o testimonio. Build trust.")
        elif outreach_type == "hot_acceleration":
            parts.append("Instrucción: El lead está caliente. Acelerar con propuesta clara, testimonio social, o scarcity/urgencia legítima.")
        elif outreach_type == "cart_recovery":
            parts.append("Instrucción: Recordarle amablemente que tiene items en el carrito. Ofrecer ayuda, no presionar. Preguntar si tiene dudas.")
        elif outreach_type == "churn_recovery":
            parts.append("Instrucción: El cliente muestra señales de insatisfacción. Mensaje de empatía, preguntar qué pasó, ofrecer solución. NO vender todavía.")
        elif outreach_type == "upsell":
            parts.append("Instrucción: Cliente satisfecho. Recomendar producto/servicio complementario basado en su compra anterior. Incluir beneficio claro.")
        elif outreach_type == "referral_request":
            parts.append("Instrucción: Cliente campeón. Pedir referido con incentivo. Agradecer primero, luego pedir. Hacerlo fácil.")
        elif outreach_type == "review_request":
            parts.append("Instrucción: Post-compra. Pedir review/NPS amablemente. Agradecer por la confianza. Incluir link.")

        return "\n\n".join(parts)

    async def schedule_outreach_for_business(self, business_id: uuid.UUID) -> list[dict[str, Any]]:
        """Schedule all proactive outreach for a business for today."""
        results = []

        for outreach_type, config in OUTREACH_TYPES.items():
            try:
                targets = await self._find_targets(business_id, outreach_type, config)
                for conv_id in targets:
                    result = await self.generate_outreach(business_id, outreach_type, conv_id)
                    if result:
                        results.append(result)
            except Exception as e:
                logger.error(f"Failed to schedule {outreach_type} for business {business_id}: {e}")

        return results

    async def _find_targets(
        self,
        business_id: uuid.UUID,
        outreach_type: str,
        config: dict,
    ) -> list[uuid.UUID]:
        """Find target conversations for an outreach type."""
        target_segment = config["target_segment"]
        frequency_days = config["frequency_days"]
        max_per_day = config["max_per_day"]

        since = datetime.now(timezone.utc) - timedelta(days=frequency_days)

        if target_segment == "cold":
            # Leads with score < 40 and no activity in frequency_days
            result = await self.db.execute(
                select(LeadScore.conversation_id).where(
                    LeadScore.business_id == business_id,
                    LeadScore.classification == "cold",
                    LeadScore.last_calculated_at < since,
                ).limit(max_per_day)
            )
            return [row[0] for row in result.all()]

        elif target_segment == "warm":
            result = await self.db.execute(
                select(LeadScore.conversation_id).where(
                    LeadScore.business_id == business_id,
                    LeadScore.classification == "warm",
                ).limit(max_per_day)
            )
            return [row[0] for row in result.all()]

        elif target_segment == "hot":
            result = await self.db.execute(
                select(LeadScore.conversation_id).where(
                    LeadScore.business_id == business_id,
                    LeadScore.classification == "hot",
                ).limit(max_per_day)
            )
            return [row[0] for row in result.all()]

        elif target_segment == "cart_abandoned":
            # Pending orders older than 1 day
            result = await self.db.execute(
                select(Order.conversation_id).where(
                    Order.business_id == business_id,
                    Order.status == "pending",
                    Order.created_at < datetime.now(timezone.utc) - timedelta(days=1),
                ).limit(max_per_day)
            )
            return [row[0] for row in result.all() if row[0]]

        elif target_segment == "at_risk":
            from app.domains.retention.models import CustomerSegment, CustomerSegmentType
            result = await self.db.execute(
                select(CustomerSegment.conversation_id).where(
                    CustomerSegment.business_id == business_id,
                    CustomerSegment.segment.in_([CustomerSegmentType.AT_RISK, CustomerSegmentType.LOST]),
                ).limit(max_per_day)
            )
            return [row[0] for row in result.all()]

        elif target_segment == "champions":
            from app.domains.retention.models import CustomerSegment, CustomerSegmentType
            result = await self.db.execute(
                select(CustomerSegment.conversation_id).where(
                    CustomerSegment.business_id == business_id,
                    CustomerSegment.segment == CustomerSegmentType.CHAMPIONS,
                ).limit(max_per_day)
            )
            return [row[0] for row in result.all()]

        elif target_segment == "recent_buyers":
            result = await self.db.execute(
                select(Order.conversation_id).where(
                    Order.business_id == business_id,
                    Order.status == "paid",
                    Order.paid_at >= datetime.now(timezone.utc) - timedelta(days=7),
                ).limit(max_per_day)
            )
            return [row[0] for row in result.all() if row[0]]

        return []
