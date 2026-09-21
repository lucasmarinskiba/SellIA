"""Cold-lead follow-up scanner (Task 5).

Recovers leads who went quiet after the bot's last message — the sale that
would otherwise just evaporate because nobody nudged them. Runs as a
periodic background loop (see app.core.followup_scheduler), not per-request:
there's no natural request to hang this off of, since by definition the
customer stopped writing in.

Conservative by design:
- Only nudges when the BOT sent the last message and the customer never
  replied (direction == OUTBOUND) — if the customer wrote last, that's a
  "we haven't replied yet" problem, out of scope here, not a "lead went cold".
- Caps nudges per conversation (default 2) so it can't turn into spam.
- Dedupes via last_followup_sent_at so the same silence window never gets
  more than one nudge per scan cycle.
"""

from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.channels.models import (
    Conversation, ConversationStatus, Message, MessageDirection,
)

logger = get_logger(__name__)

COLD_THRESHOLD_HOURS = 24  # how long a conversation must sit silent before it counts as "cold"
MAX_FOLLOWUPS_PER_CONVERSATION = 2
SCAN_BATCH_LIMIT = 200  # cap per run so one giant backlog can't block the loop for too long


async def _find_cold_conversations(db: AsyncSession) -> list[tuple[Any, Any]]:
    """(conversation_id, business_id) pairs for every cold conversation.

    Plain values on purpose, not Conversation instances: the scan rolls the
    session back when one send fails, and rollback() expires every instance
    loaded in it. Reading an expired attribute afterwards is a lazy refresh
    outside an `await` -> MissingGreenlet, which used to abort the whole scan
    (and mask the real send error) as soon as a single conversation failed.
    """
    threshold = datetime.now(timezone.utc) - timedelta(hours=COLD_THRESHOLD_HOURS)

    result = await db.execute(
        select(Conversation.id, Conversation.business_id).where(
            Conversation.status == ConversationStatus.ACTIVE,
            Conversation.last_message_at.isnot(None),
            Conversation.last_message_at < threshold,
            Conversation.followup_count < MAX_FOLLOWUPS_PER_CONVERSATION,
            or_(
                Conversation.last_followup_sent_at.is_(None),
                Conversation.last_followup_sent_at < Conversation.last_message_at,
            ),
        ).limit(SCAN_BATCH_LIMIT)
    )
    return [(row.id, row.business_id) for row in result.all()]


async def _last_message_was_outbound(db: AsyncSession, conversation_id: Any) -> bool:
    result = await db.execute(
        select(Message.direction)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(1)
    )
    direction = result.scalar_one_or_none()
    return direction == MessageDirection.OUTBOUND


async def _build_followup_text(db: AsyncSession, business_id: Any) -> str:
    """Pull a business-tailored nudge from BusinessContext angles if
    configured, else fall back to a generic one — mirrors the pitch-building
    logic in process_incoming_message's auto-qualification block."""
    try:
        from app.domains.business_context.models import BusinessContext

        result = await db.execute(
            select(BusinessContext).where(BusinessContext.business_id == business_id)
        )
        ctx = result.scalar_one_or_none()
        if ctx and ctx.communication_angles:
            angle = ctx.communication_angles[0]
            hook = angle.get("hook")
            if hook:
                return f"¡Hola! {hook} ¿Seguís interesado/a? Cualquier duda, acá estoy 🙂"
        if ctx and ctx.scheduling_link:
            return f"¡Hola! ¿Seguís por ahí? Si querés avanzamos: {ctx.scheduling_link}"
    except Exception as e:
        logger.error(f"Follow-up angle lookup error for business {business_id}: {e}")

    return "¡Hola! Vi que quedamos a mitad de charla — ¿seguís interesado/a en avanzar? Estoy para lo que necesites 🙂"


async def scan_and_send_followups(db: AsyncSession) -> dict[str, int]:
    """One scan cycle. Returns counters for logging/observability."""
    stats = {"scanned": 0, "sent": 0, "skipped_replied": 0, "errors": 0}

    try:
        cold_conversations = await _find_cold_conversations(db)
    except Exception as e:
        logger.error(f"Follow-up scan query failed: {e}")
        return stats

    stats["scanned"] = len(cold_conversations)

    for conversation_id, business_id in cold_conversations:
        try:
            if not await _last_message_was_outbound(db, conversation_id):
                # Customer wrote last — bot hasn't replied. Not this task's job.
                stats["skipped_replied"] += 1
                continue

            text = await _build_followup_text(db, business_id)

            from app.domains.channels.services import send_outbound_message
            await send_outbound_message(db, conversation_id, text)

            # Awaited fetch, so it is safe whatever expired since the query
            # (send_outbound_message commits; a default-config session expires on commit).
            conversation = await db.get(Conversation, conversation_id)
            if conversation is None:
                # Deleted while the nudge was going out; nothing left to record.
                stats["sent"] += 1
                continue

            followup_number = (conversation.followup_count or 0) + 1
            conversation.last_followup_sent_at = datetime.now(timezone.utc)
            conversation.followup_count = followup_number
            await db.commit()

            stats["sent"] += 1
            logger.info(f"Follow-up sent to conversation {conversation_id} (#{followup_number})")

        except Exception as e:
            # Only plain values below this line: rollback() expires every loaded instance.
            await db.rollback()
            stats["errors"] += 1
            logger.error(f"Follow-up send failed for conversation {conversation_id}: {e}")

    if stats["sent"] or stats["errors"]:
        logger.info(f"Follow-up scan complete: {stats}")

    return stats
