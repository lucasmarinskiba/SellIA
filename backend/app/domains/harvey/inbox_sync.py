"""Mirror Harvey's email threads into the business's unified inbox (``conversations`` / ``messages``).

The inbox then shows chat channels and prospecting emails side by side, with the "needs a person" flag.

Safety, on purpose: a mirrored conversation has NO channel (``channel_connection_id`` is NULL). Everything that sends
through a channel generically (the cold-lead follow-up scan, the auto-reply bot, ``send_outbound_message``) needs a
channel, so none of them can ever write to a prospect behind Harvey's back and skip its gate (opt-out line, postal
address, do-not-contact list, human approval). Answering happens in Prospección → Respuestas.

Best-effort like the CRM sync: it runs in a savepoint and a failure is logged, never raised.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.channels.handoff import mark_awaiting_human
from app.domains.channels.models import Conversation, ConversationStatus, Message, MessageDirection, MessageStatus
from app.domains.harvey.models import HarveyOutboxItem, HarveyProspect, OutboxStatus

logger = get_logger(__name__)

SOURCE = "harvey"
BLANK_LINE = "\n\n"
HANDOFF_REASON = "Prospecto de Harvey: respuesta que decide una persona"
REPLY_HINT = "Respondé desde Prospección → Respuestas: ahí pasa por los controles de Harvey."


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _existing(db: AsyncSession, business_id: uuid.UUID, prospect: HarveyProspect) -> Conversation | None:
    return (
        await db.execute(
            select(Conversation).where(
                Conversation.business_id == business_id, Conversation.external_id == f"{SOURCE}:{prospect.id}"
            )
        )
    ).scalar_one_or_none()


def _sent_message(conversation_id: uuid.UUID, item: Any) -> Message:
    return Message(
        conversation_id=conversation_id,
        direction=MessageDirection.OUTBOUND,
        content=(item.subject + BLANK_LINE + item.body if item.kind != "reply" else (item.body or ""))[:5000],
        status=MessageStatus.SENT,
        external_message_id=item.message_id,
        created_at=item.sent_at or _now(),
        extra_data={"source": SOURCE, "harvey_item_id": str(item.id), "step": item.step, "kind": item.kind},
    )


async def _create(db: AsyncSession, business_id: uuid.UUID, prospect: HarveyProspect) -> Conversation:
    """A new thread, with the emails Harvey already sent this prospect so the history reads from the start."""
    name = " ".join(p for p in (prospect.first_name, prospect.last_name) if p).strip() or prospect.company or prospect.email
    row = Conversation(
        business_id=business_id,
        channel_connection_id=None,  # see the module docstring: no channel, nothing can send through it
        external_id=f"{SOURCE}:{prospect.id}",
        lead_name=name[:255],
        lead_email=(prospect.email or "")[:255],
        lead_source=SOURCE,
        status=ConversationStatus.ACTIVE,
        extra_data={"source": SOURCE, "harvey_prospect_id": str(prospect.id), "company": prospect.company or ""},
    )
    db.add(row)
    await db.flush()
    sent = await db.execute(
        select(HarveyOutboxItem)
        .where(
            HarveyOutboxItem.business_id == business_id,
            HarveyOutboxItem.prospect_id == prospect.id,
            HarveyOutboxItem.status == OutboxStatus.SENT.value,
        )
        .order_by(HarveyOutboxItem.sent_at)
    )
    for item in sent.scalars():
        db.add(_sent_message(row.id, item))
    return row


async def _has_message(db: AsyncSession, conversation_id: uuid.UUID, key: str, value: str) -> bool:
    rows = await db.execute(select(Message.extra_data).where(Message.conversation_id == conversation_id))
    return any((extra or {}).get(key) == value for (extra,) in rows.all())


async def _mirror_reply(db: AsyncSession, business_id: uuid.UUID, prospect: HarveyProspect, reply: Any) -> None:
    conv = await _existing(db, business_id, prospect) or await _create(db, business_id, prospect)
    if await _has_message(db, conv.id, "harvey_reply_id", str(reply.id)):
        return
    db.add(
        Message(
            conversation_id=conv.id,
            direction=MessageDirection.INBOUND,
            content=(reply.body or "")[:5000],
            status=MessageStatus.DELIVERED,
            external_message_id=(reply.message_id or None),
            extra_data={"source": SOURCE, "harvey_reply_id": str(reply.id), "classification": reply.classification},
        )
    )
    conv.last_message_at = _now()
    if reply.needs_human:
        mark_awaiting_human(conv, HANDOFF_REASON)
    if reply.classification in ("opt_out", "not_interested"):
        conv.status = ConversationStatus.ARCHIVED  # nothing left to do: it leaves the active list
    extra = dict(conv.extra_data or {})
    extra["last_classification"] = reply.classification
    conv.extra_data = extra


async def _mirror_sent(db: AsyncSession, business_id: uuid.UUID, prospect: HarveyProspect, item: Any) -> None:
    """Only into a thread that already exists (a prospect who answered): cold emails alone do not fill the inbox."""
    conv = await _existing(db, business_id, prospect)
    if conv is None or await _has_message(db, conv.id, "harvey_item_id", str(item.id)):
        return
    db.add(_sent_message(conv.id, item))
    conv.last_message_at = _now()
    if item.kind == "reply":  # a person answered through Harvey: the "needs a person" flag is done
        extra = dict(conv.extra_data or {})
        extra["awaiting_human"] = False
        conv.extra_data = extra


async def on_reply(db: AsyncSession, business_id: uuid.UUID, prospect: HarveyProspect, reply: Any) -> None:
    """Add a prospect's reply to the inbox. Never raises."""
    try:
        async with db.begin_nested():
            await _mirror_reply(db, business_id, prospect, reply)
        await db.commit()
    except Exception:  # noqa: BLE001 - the reply itself is already saved
        logger.warning("harvey: inbox mirror failed for a reply", exc_info=True)


async def on_sent(db: AsyncSession, business_id: uuid.UUID, prospect: HarveyProspect, item: Any) -> None:
    """Add an email Harvey sent to the inbox. Never raises."""
    try:
        async with db.begin_nested():
            await _mirror_sent(db, business_id, prospect, item)
        await db.commit()
    except Exception:  # noqa: BLE001 - the email already went out
        logger.warning("harvey: inbox mirror failed for a sent email", exc_info=True)
