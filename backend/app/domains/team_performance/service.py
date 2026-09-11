"""Who on the team is actually doing the work, measured from the work itself.

This replaces what the Leaderboard screen was ranking. That board sorted team
members by total_xp, total_sales_closed and total_revenue_generated on the
gamification profile — and those counters are only ever written by
GamificationEngine.record_sale, which the order handler calls with biz.user_id,
the OWNER, no matter who closed the sale. So every employee sat at zero forever
and the owner's number measured nothing but the passage of orders. A ranking
whose positions are decided before anyone works is worse than no ranking: it
tells the owner nothing and tells the employee they do not count.

What is measurable here, from rows that already exist:

* Replies a person sent, and how fast the first one went out (messages now carry
  sent_by_user_id — see channels.services.send_outbound_message).
* Conversations they took part in, and how many are still waiting for a human.
* Deals assigned to them and which were won (crm.Deal.assigned_to_user_id).

What is NOT measurable, and is named rather than guessed: revenue per person.
Orders carry a conversation, not a seller, so attributing money to one teammate
would be an invention. The board reports the deals they own instead, and says
the gap out loud.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

logger = get_logger(__name__)

WON_STATES = ("won", "ganado", "closed_won")


async def _attribution_started_at(db: AsyncSession, conversation_ids: list[Any]):
    """When this account's replies first began carrying their author.

    Read from the data rather than hardcoded: messages only started recording
    sent_by_user_id once that was deployed, and a constant written by hand would
    be wrong for anyone whose first attributed reply came later — or, worse, would
    name a date in the future. Returns None when no reply has an author yet, and
    the caller says that plainly instead of printing a date nothing supports.
    """
    from app.domains.channels.models import Message, MessageDirection

    if not conversation_ids:
        return None
    try:
        result = await db.execute(
            select(func.min(Message.created_at)).where(
                Message.conversation_id.in_(conversation_ids),
                Message.direction == MessageDirection.OUTBOUND,
                Message.extra_data["sent_by_user_id"].isnot(None),
            )
        )
        return result.scalar()
    except Exception as e:  # noqa: BLE001
        logger.info("team board: attribution start unreadable (%s)", str(e)[:120])
        await db.rollback()
        return None


async def _members(db: AsyncSession, business_id: uuid.UUID) -> dict[uuid.UUID, dict[str, Any]]:
    """Everyone who can act on this business: the owner plus its members."""
    from app.domains.businesses.models import Business
    from app.domains.users.models import User

    people: dict[uuid.UUID, dict[str, Any]] = {}

    business = await db.get(Business, business_id)
    if business is None:
        return people

    owner = await db.get(User, business.user_id)
    if owner is not None:
        people[owner.id] = {
            "user_id": str(owner.id),
            "name": owner.full_name or owner.email,
            "email": owner.email,
            "role": "dueño",
        }

    try:
        from app.domains.enterprise.models import BusinessMember

        result = await db.execute(
            select(BusinessMember).where(BusinessMember.business_id == business_id)
        )
        for member in result.scalars().all():
            member_user = await db.get(User, member.user_id)
            if member_user is None or member_user.id in people:
                continue
            people[member_user.id] = {
                "user_id": str(member_user.id),
                "name": member_user.full_name or member_user.email,
                "email": member_user.email,
                "role": str(getattr(member, "role", "") or "miembro"),
            }
    except Exception as e:  # noqa: BLE001 - a business with no team is the common case
        logger.info("team board: members unavailable (%s)", str(e)[:120])
        await db.rollback()

    return people


async def board(db: AsyncSession, business_id: uuid.UUID, days: int = 30) -> dict[str, Any]:
    """One row per person, with the denominators and the gaps stated."""
    from app.domains.channels.models import Conversation, Message, MessageDirection
    from app.domains.data_science.stats import MIN_TO_READ, median

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    people = await _members(db, business_id)
    if not people:
        return {
            "has_data": False,
            "headline": "No se pudo leer el equipo de este negocio.",
            "members": [],
            "gaps": [],
            "period_days": days,
            "generated_at": now.isoformat(),
        }

    conv_result = await db.execute(
        select(Conversation.id, Conversation.extra_data).where(
            Conversation.business_id == business_id,
            Conversation.is_active.is_(True),
        )
    )
    conversations = {row[0]: (row[1] or {}) for row in conv_result.all()}

    stats: dict[str, dict[str, Any]] = {
        str(uid): {
            **info,
            "replies": 0,
            "conversation_ids": set(),
            "latencies": [],
            "deals_assigned": 0,
            "deals_won": 0,
        }
        for uid, info in people.items()
    }

    ai_replies = 0
    unattributed_replies = 0

    if conversations:
        msg_result = await db.execute(
            select(
                Message.conversation_id, Message.direction,
                Message.extra_data, Message.created_at,
            )
            .where(
                Message.conversation_id.in_(list(conversations)),
                Message.created_at >= since,
            )
            .order_by(Message.created_at.asc())
        )
        first_inbound: dict[Any, datetime] = {}
        answered: set[Any] = set()

        for conv_id, direction, extra, created in msg_result.all():
            extra = extra if isinstance(extra, dict) else {}
            if direction == MessageDirection.INBOUND:
                first_inbound.setdefault(conv_id, created)
                continue

            if str(extra.get("generated_by") or "").startswith("ai"):
                ai_replies += 1
                continue

            sender = extra.get("sent_by_user_id")
            if not sender or sender not in stats:
                # A human reply nobody can be credited for: sent before the
                # sender was recorded, or by an automation. Counted apart rather
                # than dropped, so the totals still add up.
                unattributed_replies += 1
                continue

            bucket = stats[sender]
            bucket["replies"] += 1
            bucket["conversation_ids"].add(conv_id)
            opened = first_inbound.get(conv_id)
            if opened is not None and conv_id not in answered and created >= opened:
                answered.add(conv_id)
                bucket["latencies"].append((created - opened).total_seconds() / 60)

    # Deals do record their owner, so this part is attributable today.
    try:
        from app.domains.crm.models import Deal

        deal_result = await db.execute(
            select(Deal.assigned_to_user_id, Deal.status).where(Deal.business_id == business_id)
        )
        for assignee, deal_status in deal_result.all():
            key = str(assignee) if assignee else None
            if key not in stats:
                continue
            stats[key]["deals_assigned"] += 1
            if str(deal_status or "").lower() in WON_STATES:
                stats[key]["deals_won"] += 1
    except Exception as e:  # noqa: BLE001
        logger.info("team board: deals unavailable (%s)", str(e)[:120])
        await db.rollback()

    rows = []
    for bucket in stats.values():
        latencies = bucket.pop("latencies")
        conv_ids = bucket.pop("conversation_ids")
        med = median(latencies)
        rows.append({
            **bucket,
            "conversations": len(conv_ids),
            "median_first_reply_minutes": round(med, 1) if med is not None else None,
            "first_reply_sample": len(latencies),
            # A median over two replies is not a speed; the UI greys it out.
            "speed_is_readable": len(latencies) >= MIN_TO_READ,
        })

    rows.sort(key=lambda row: (-row["replies"], row["name"].lower()))

    waiting = sum(
        1 for extra in conversations.values()
        if isinstance(extra, dict) and extra.get("awaiting_human")
    )

    gaps: list[str] = [
        "La facturación no se reparte por persona: las órdenes guardan la conversación, "
        "no quién la cerró. Repartir plata entre integrantes sería inventarlo.",
    ]
    if unattributed_replies:
        gaps.append(
            f"{unattributed_replies} respuestas humanas no tienen autor registrado: se "
            "enviaron antes de que el sistema empezara a guardarlo, o desde una "
            "automatización. No se le cuentan a nadie."
        )
    started_at = await _attribution_started_at(db, list(conversations))
    if not any(row["replies"] for row in rows):
        gaps.append(
            "Todavía no hay respuestas con autor en este período."
            + (
                f" La primera con autor registrado es del {started_at.date().isoformat()}."
                if started_at is not None
                else " Las respuestas enviadas antes de esta versión no guardaban quién las"
                " escribió, así que no se pueden asignar."
            )
        )

    total_human = sum(row["replies"] for row in rows)
    headline = (
        f"{total_human} respuestas del equipo y {ai_replies} de la IA en {days} días."
        if (total_human or ai_replies)
        else f"Sin actividad registrada en los últimos {days} días."
    )

    return {
        "has_data": True,
        "headline": headline,
        "members": rows,
        "ai_replies": ai_replies,
        "human_replies": total_human,
        "unattributed_replies": unattributed_replies,
        "conversations_waiting": waiting,
        "gaps": gaps,
        "attribution_since": started_at.date().isoformat() if started_at is not None else None,
        "period_days": days,
        "generated_at": now.isoformat(),
    }
