"""Funnel Stage Detector — infers which funnel stage a conversation is in.

Combines with app.core.prompts.funnel_specialists to pick the right
specialist (and its business-type adaptation) automatically for each
AI-generated reply, without requiring manual stage tagging.

Detection is based on real signals already tracked by the app — Order
records and message counts — not on re-reading conversation text with an
extra LLM call, so it stays fast and cheap enough to run on every reply.
"""

import uuid

from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.prompts.funnel_specialists import FunnelStage
from app.domains.channels.models import Conversation, Message, MessageDirection
from app.domains.orders.models import Order, OrderStatus
from app.core.logger import get_logger

logger = get_logger(__name__)

_CONVERTED_STATUSES = (OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED)


async def detect_funnel_stage(
    db: AsyncSession,
    business_id: uuid.UUID,
    conversation: Conversation,
) -> FunnelStage:
    """Infer the current funnel stage for a conversation.

    Priority order (most decisive signal first):
    1. Two or more completed orders from this customer -> EXPANSION
    2. Exactly one completed order, no pending order since -> RETENTION
    3. A pending/unpaid order tied to this conversation -> CONVERSION
    4. Very early conversation (1 inbound message) -> AWARENESS
    5. A few messages in, no order yet -> ACQUISITION
    6. Fallback -> ACQUISITION
    """
    try:
        # Match orders by conversation_id, or by the lead's email/phone across
        # the business (so a customer who returns via a new conversation is
        # still recognized as a repeat buyer).
        identity_filters = [Order.conversation_id == conversation.id]
        if conversation.lead_email:
            identity_filters.append(Order.customer_email == conversation.lead_email)
        if conversation.lead_phone:
            identity_filters.append(Order.customer_phone == conversation.lead_phone)

        orders_result = await db.execute(
            select(Order.status).where(
                Order.business_id == business_id,
                or_(*identity_filters),
            )
        )
        order_statuses = [row[0] for row in orders_result.all()]

        completed_count = sum(1 for s in order_statuses if s in _CONVERTED_STATUSES)
        has_pending_order = any(s == OrderStatus.PENDING for s in order_statuses)

        if completed_count >= 2:
            return FunnelStage.EXPANSION
        if completed_count == 1 and not has_pending_order:
            return FunnelStage.RETENTION
        if has_pending_order:
            return FunnelStage.CONVERSION

        # No order history yet — use message volume as a proxy for how far
        # along the conversation is.
        inbound_count_result = await db.execute(
            select(func.count(Message.id)).where(
                Message.conversation_id == conversation.id,
                Message.direction == MessageDirection.INBOUND,
            )
        )
        inbound_count = inbound_count_result.scalar() or 0

        if inbound_count <= 1:
            return FunnelStage.AWARENESS

        return FunnelStage.ACQUISITION

    except Exception as e:
        logger.warning(f"Funnel stage detection failed, defaulting to ACQUISITION: {e}")
        return FunnelStage.ACQUISITION


__all__ = ["detect_funnel_stage"]
