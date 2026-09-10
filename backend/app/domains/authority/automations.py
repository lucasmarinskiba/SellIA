"""Automations that actually run.

An action labelled "La hace SellIA" has to be something SellIA really does, or
the label is the same lie as an invented metric. So this module only implements
what is genuinely executable against real infrastructure that already exists,
and every other recommendation stays honestly marked as the user's work.

What is executable today:
  enable_auto_reply    writes the real AgentConfig flags that gate
                       _maybe_ai_auto_reply in the channels service, so new
                       inbound messages really do get answered automatically.
  review_campaign      builds a recipient list from REAL conversations that had
                       a real exchange on a connected channel, and sends the
                       request through the real connector -- only after the user
                       confirms, because it puts messages in front of their
                       customers under their name.

What is NOT executable, and is not pretended to be: publishing JSON-LD or
profile links into the user's own site. SellIA has no renderer for a hosted
storefront, so it cannot put anything on their page; that stays "SellIA te lo
prepara" -- we generate the exact code and the user pastes it.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

logger = get_logger(__name__)

#: Never message the same customer twice for the same campaign, and never
#: someone whose last exchange is ancient -- a review request six months late
#: reads as spam, not attention.
REVIEW_WINDOW_DAYS = 90
REVIEW_CAMPAIGN_TAG = "authority_review_request"


class NotExecutable(Exception):
    """This action is not something SellIA can carry out by itself."""


async def enable_auto_reply(db: AsyncSession, business_id: uuid.UUID) -> dict[str, Any]:
    """Turn on the real AI auto-reply for this business.

    _maybe_ai_auto_reply (app/domains/channels/services.py) refuses to answer
    unless an AgentConfig row exists with is_enabled and ai_auto_reply_enabled.
    Writing those flags is the whole automation -- from then on, real inbound
    messages get a real automatic answer.
    """
    from app.domains.agents.models import AgentConfig, AgentPersonality

    result = await db.execute(
        select(AgentConfig).where(AgentConfig.business_id == business_id).limit(1)
    )
    config = result.scalar_one_or_none()

    if config is None:
        personality = await db.execute(select(AgentPersonality.id).limit(1))
        personality_id = personality.scalar_one_or_none()
        if personality_id is None:
            raise NotExecutable(
                "No hay ninguna personalidad de agente cargada en esta instalación, "
                "así que no se puede activar la respuesta automática."
            )
        config = AgentConfig(
            business_id=business_id,
            personality_id=personality_id,
            is_enabled=True,
            ai_auto_reply_enabled=True,
        )
        db.add(config)
    else:
        config.is_enabled = True
        config.ai_auto_reply_enabled = True

    await db.commit()
    return {
        "executed": True,
        "detail": (
            "Respuesta automática activada. A partir de ahora, cada consulta que entre por un "
            "canal conectado recibe una primera respuesta de la IA en segundos."
        ),
    }


async def review_campaign_recipients(
    db: AsyncSession, business_ids: list[uuid.UUID], limit: int = 25
) -> list[dict[str, Any]]:
    """Real customers who could be asked for a review, right now.

    A candidate is a conversation on a connected channel where the customer
    really wrote and the business really answered, recently enough for the
    request to make sense, and which was not already asked.
    """
    from app.domains.channels.models import (
        ChannelConnection, Conversation, Message, MessageDirection,
    )

    if not business_ids:
        return []

    since = datetime.now(timezone.utc) - timedelta(days=REVIEW_WINDOW_DAYS)
    result = await db.execute(
        select(
            Conversation.id,
            Conversation.lead_name,
            Conversation.lead_phone,
            Conversation.extra_data,
            Conversation.last_message_at,
            ChannelConnection.id,
            ChannelConnection.platform,
        )
        .join(ChannelConnection, Conversation.channel_connection_id == ChannelConnection.id)
        .where(
            Conversation.business_id.in_(business_ids),
            # last_message_at is NULL on every conversation created before it
            # was fixed (it was assigned from an unflushed column default), so
            # recency falls back to when the conversation itself started.
            or_(
                Conversation.last_message_at >= since,
                and_(Conversation.last_message_at.is_(None), Conversation.created_at >= since),
            ),
            ChannelConnection.is_active.is_(True),
        )
        .order_by(Conversation.created_at.desc())
        .limit(200)
    )

    candidates: list[dict[str, Any]] = []
    for conv_id, name, phone, extra, last_at, channel_id, platform in result.all():
        if (extra or {}).get(REVIEW_CAMPAIGN_TAG):
            continue  # already asked

        counts = await db.execute(
            select(Message.direction, Message.id)
            .where(Message.conversation_id == conv_id)
        )
        directions = [row[0] for row in counts.all()]
        has_inbound = any(d == MessageDirection.INBOUND for d in directions)
        has_outbound = any(d == MessageDirection.OUTBOUND for d in directions)
        if not (has_inbound and has_outbound):
            continue  # never a real exchange: nothing to review

        candidates.append({
            "conversation_id": str(conv_id),
            "channel_connection_id": str(channel_id),
            "name": name or "cliente",
            "contact": phone,
            "platform": platform.value if hasattr(platform, "value") else str(platform),
            "last_message_at": last_at.isoformat() if last_at else None,
        })
        if len(candidates) >= limit:
            break

    return candidates


async def send_review_campaign(
    db: AsyncSession,
    business_ids: list[uuid.UUID],
    script: str,
    conversation_ids: Optional[list[str]] = None,
) -> dict[str, Any]:
    """Send the review request to the selected real conversations.

    Only ever called after the user confirmed the recipient list in the UI: this
    puts a message in front of their customers, signed as them.
    """
    from app.domains.channels.models import Conversation
    from app.domains.channels.services import send_outbound_message

    recipients = await review_campaign_recipients(db, business_ids, limit=50)
    if conversation_ids:
        wanted = set(conversation_ids)
        recipients = [r for r in recipients if r["conversation_id"] in wanted]

    if not recipients:
        raise NotExecutable(
            "No hay conversaciones que califiquen: hace falta al menos un cliente que haya "
            "escrito y haya sido respondido en los últimos 90 días."
        )

    sent, failed = 0, 0
    last_error: Optional[str] = None
    for recipient in recipients:
        try:
            message = script.replace("{nombre}", recipient["name"])
            await send_outbound_message(
                db,
                conversation_id=uuid.UUID(recipient["conversation_id"]),
                content=message,
                generated_by="ai",
            )
            # Mark it so the same customer is never asked twice.
            conv = await db.get(Conversation, uuid.UUID(recipient["conversation_id"]))
            if conv is not None:
                extra = dict(conv.extra_data or {})
                extra[REVIEW_CAMPAIGN_TAG] = datetime.now(timezone.utc).isoformat()
                conv.extra_data = extra
            sent += 1
        except Exception as e:  # noqa: BLE001 -- one bad recipient must not sink the batch
            logger.warning("review campaign: send failed for %s: %s",
                           recipient["conversation_id"], str(e)[:200])
            last_error = str(e)[:200]
            failed += 1

    await db.commit()

    # Zero sends is a failure, not a completed automation. Reporting
    # executed: true here (and letting the caller tick the action off) would be
    # the same lie as a metric nobody measured: the platform rejected every
    # message, usually because its credentials are wrong.
    if sent == 0:
        raise NotExecutable(
            f"No se pudo enviar ninguno de los {failed} mensajes. La plataforma los rechazó"
            + (f": {last_error}" if last_error else ".")
            + " Revisá las credenciales del canal en Vendedor Multiplataforma."
        )

    return {
        "executed": True,
        "sent": sent,
        "failed": failed,
        "detail": (
            f"Pedido de reseña enviado a {sent} cliente(s) reales por su propio canal."
            + (f" {failed} no se pudieron enviar: {last_error}" if failed else "")
        ),
    }


#: action_key -> how it runs. Anything absent is honestly not automatable.
EXECUTABLE = {
    "speed_up_first_reply": "enable_auto_reply",
    "ask_first_reviews": "review_campaign",
    "grow_reviews": "review_campaign",
}


def is_executable(action_key: str) -> bool:
    return action_key in EXECUTABLE


def needs_confirmation(action_key: str) -> bool:
    """True when running it sends something to the user's customers."""
    return EXECUTABLE.get(action_key) == "review_campaign"
