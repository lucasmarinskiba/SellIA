"""
ML Data Collector

Recolecta datos de uso, conversaciones, y outcomes para entrenar modelos ML.
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.domains.feedback.models import MLTrainingData
from app.core.logger import get_logger

logger = get_logger(__name__)


async def collect_conversation_outcomes(db: AsyncSession) -> int:
    """Recolecta datos de resultado de conversaciones (lead convertido? sí/no)."""
    try:
        from app.domains.channels.models import Conversation, Message
        from app.domains.crm.models import Deal

        # Conversaciones con deals asociados = convertidas
        result = await db.execute(
            select(Conversation.id, func.count(Deal.id))
            .outerjoin(Deal, Deal.conversation_id == Conversation.id)
            .where(Conversation.created_at >= datetime.now(timezone.utc) - timedelta(days=1))
            .group_by(Conversation.id)
        )

        count = 0
        for conv_id, deal_count in result.all():
            data = MLTrainingData(
                data_type="conversation_outcome",
                features={"conversation_id": str(conv_id), "has_deal": deal_count > 0},
                label="converted" if deal_count > 0 else "not_converted",
            )
            db.add(data)
            count += 1

        await db.commit()
        logger.info(f"Collected {count} conversation outcomes for ML training")
        return count
    except Exception as e:
        logger.warning(f"Could not collect conversation outcomes: {e}")
        return 0


async def collect_ai_response_ratings(db: AsyncSession) -> int:
    """Recolecta ratings de respuestas AI (de tickets de soporte resueltos)."""
    try:
        from app.domains.support.models import SupportTicket, TicketMessage

        result = await db.execute(
            select(SupportTicket).where(
                SupportTicket.csat_rating.isnot(None),
                SupportTicket.updated_at >= datetime.now(timezone.utc) - timedelta(days=1),
            )
        )

        count = 0
        for ticket in result.scalars().all():
            data = MLTrainingData(
                data_type="ai_response_rating",
                features={"ticket_id": str(ticket.id), "category": ticket.category},
                score=float(ticket.csat_rating),
            )
            db.add(data)
            count += 1

        await db.commit()
        logger.info(f"Collected {count} AI response ratings for ML training")
        return count
    except Exception as e:
        logger.warning(f"Could not collect AI response ratings: {e}")
        return 0


async def collect_intent_accuracy(db: AsyncSession) -> int:
    """Recolecta datos de precisión de clasificación de intenciones."""
    try:
        from app.domains.automations.models import ChatbotRule
        from app.domains.channels.models import Message

        # Mensajes donde una regla de chatbot hizo match = clasificación correcta
        result = await db.execute(
            select(Message).where(
                Message.created_at >= datetime.now(timezone.utc) - timedelta(days=1),
                Message.extra_data.isnot(None),
            ).limit(100)
        )

        count = 0
        for msg in result.scalars().all():
            extra = msg.extra_data or {}
            if "matched_rule_id" in extra:
                data = MLTrainingData(
                    data_type="intent_accuracy",
                    features={"message_content": msg.content[:200], "matched_rule": extra.get("matched_rule_id")},
                    label="correct" if extra.get("user_satisfied", True) else "incorrect",
                )
                db.add(data)
                count += 1

        await db.commit()
        logger.info(f"Collected {count} intent accuracy samples for ML training")
        return count
    except Exception as e:
        logger.warning(f"Could not collect intent accuracy: {e}")
        return 0
