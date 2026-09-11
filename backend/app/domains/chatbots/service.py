"""Resolve, measure and test the per-platform chatbots.

Nothing here decides what a good answer looks like -- that is ai_reply.py, which
already detects the funnel stage and layers the right specialist prompt and
expert voice. This module answers the narrower questions the seller actually
controls: does the bot speak on this platform, as whom, aimed at what, and when
does it step aside for a human.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

from . import playbooks
from .models import BotFocus, PlatformBot

logger = get_logger(__name__)

DEFAULT_PERSONALITY = "captador"

FOCUS_LABELS: dict[str, str] = {
    BotFocus.AUTO.value: "Automático (según la conversación)",
    BotFocus.ATTRACT.value: "Atraer clientes",
    BotFocus.CLOSE.value: "Cerrar la venta",
    BotFocus.RETAIN.value: "Fidelizar / posventa",
    BotFocus.GROW.value: "Vender más al mismo cliente",
}


def _clean_hours(value: Any) -> Optional[dict[str, int]]:
    """Validate the active-hours window, or store nothing.

    A half-filled or out-of-range window would silence the bot at hours the
    seller never chose, so anything that does not parse becomes "no restriction"
    rather than a guess.
    """
    if not isinstance(value, dict):
        return None
    try:
        start = int(value.get("from"))
        end = int(value.get("to"))
        offset = int(value.get("utc_offset", 0))
    except (TypeError, ValueError):
        return None
    if not (0 <= start <= 23 and 0 <= end <= 23 and -12 <= offset <= 14):
        return None
    if start == end:
        return None
    return {"from": start, "to": end, "utc_offset": offset}


async def get_bot(
    db: AsyncSession, business_id: uuid.UUID, platform: str
) -> Optional[PlatformBot]:
    result = await db.execute(
        select(PlatformBot).where(
            PlatformBot.business_id == business_id,
            PlatformBot.platform == platform,
        )
    )
    return result.scalar_one_or_none()


def serialize(bot: PlatformBot) -> dict[str, Any]:
    return {
        "platform": bot.platform,
        "enabled": bool(bot.enabled),
        "personality_slug": bot.personality_slug,
        "focus": bot.focus.value if isinstance(bot.focus, BotFocus) else str(bot.focus),
        "focus_label": FOCUS_LABELS.get(
            bot.focus.value if isinstance(bot.focus, BotFocus) else str(bot.focus), ""
        ),
        "custom_instructions": bot.custom_instructions,
        "handoff_keywords": list(bot.handoff_keywords or []),
        "max_ai_replies": bot.max_ai_replies,
        "active_hours": bot.active_hours,
        "after_hours_message": bot.after_hours_message,
        "escalate_on_frustration": bool(bot.escalate_on_frustration),
        "hold_on_policy_violation": bool(bot.hold_on_policy_violation),
        "updated_at": bot.updated_at.isoformat() if bot.updated_at else None,
    }


async def upsert_bot(
    db: AsyncSession, business_id: uuid.UUID, platform: str, changes: dict[str, Any]
) -> PlatformBot:
    bot = await get_bot(db, business_id, platform)
    if bot is None:
        bot = PlatformBot(business_id=business_id, platform=platform)
        db.add(bot)

    for field, value in changes.items():
        if field == "focus" and value is not None:
            bot.focus = BotFocus(value)
        elif field == "handoff_keywords" and value is not None:
            bot.handoff_keywords = [str(w).strip().lower() for w in value if str(w).strip()]
        elif field == "active_hours":
            bot.active_hours = _clean_hours(value)
        else:
            setattr(bot, field, value)

    await db.commit()
    await db.refresh(bot)
    return bot


async def platform_stats(
    db: AsyncSession, business_ids: list[uuid.UUID]
) -> dict[str, dict[str, Any]]:
    """Real traffic per platform: how much came in, how much the AI answered,
    and how much is still waiting. Counted from messages, not claimed."""
    from app.domains.channels.models import (
        ChannelConnection, Conversation, Message, MessageDirection,
    )

    if not business_ids:
        return {}

    result = await db.execute(
        select(Conversation.id, ChannelConnection.platform)
        .join(ChannelConnection, Conversation.channel_connection_id == ChannelConnection.id)
        .where(Conversation.business_id.in_(business_ids))
    )
    conv_platform = {
        row[0]: (row[1].value if hasattr(row[1], "value") else str(row[1]))
        for row in result.all()
    }
    if not conv_platform:
        return {}

    messages = await db.execute(
        select(Message.conversation_id, Message.direction, Message.extra_data, Message.created_at)
        .where(Message.conversation_id.in_(list(conv_platform)))
        .order_by(Message.created_at.asc())
    )

    stats: dict[str, dict[str, Any]] = {}
    last_direction: dict[uuid.UUID, Any] = {}

    for conv_id, direction, extra, _created in messages.all():
        platform = conv_platform.get(conv_id)
        if platform is None:
            continue
        bucket = stats.setdefault(platform, {
            "conversations": 0, "inbound": 0, "ai_replies": 0,
            "human_replies": 0, "waiting": 0,
        })
        if direction == MessageDirection.INBOUND:
            bucket["inbound"] += 1
        else:
            if isinstance(extra, dict) and extra.get("generated_by") == "ai":
                bucket["ai_replies"] += 1
            else:
                bucket["human_replies"] += 1
        last_direction[conv_id] = direction

    for conv_id, platform in conv_platform.items():
        bucket = stats.setdefault(platform, {
            "conversations": 0, "inbound": 0, "ai_replies": 0,
            "human_replies": 0, "waiting": 0,
        })
        bucket["conversations"] += 1
        if last_direction.get(conv_id) == MessageDirection.INBOUND:
            bucket["waiting"] += 1

    return stats


async def platform_performance(
    db: AsyncSession, business_ids: list[uuid.UUID]
) -> dict[str, dict[str, Any]]:
    """What each platform's bot actually achieved, not how much it typed.

    Three things the counters could not answer:

    * How fast the first reply went out, as a median over real timestamps.
    * How many conversations ended up held for a human, and why.
    * How many orders came from a conversation this bot had touched — real
      attribution, because orders carry conversation_id.

    Every number is reported with its denominator, and a sample too small to
    read says so rather than printing a percentage. An order whose conversation
    is unknown is not attributed to anyone.
    """
    from app.domains.channels.models import (
        ChannelConnection, Conversation, Message, MessageDirection,
    )
    from app.domains.data_science.stats import MIN_TO_READ, Proportion, median
    from app.domains.orders.models import Order

    if not business_ids:
        return {}

    convs = await db.execute(
        select(Conversation.id, ChannelConnection.platform, Conversation.extra_data)
        .join(ChannelConnection, Conversation.channel_connection_id == ChannelConnection.id)
        .where(Conversation.business_id.in_(business_ids))
    )
    rows = convs.all()
    if not rows:
        return {}

    platform_of: dict[Any, str] = {}
    held: dict[str, int] = {}
    held_reasons: dict[str, dict[str, int]] = {}
    for conv_id, platform, extra in rows:
        name = platform.value if hasattr(platform, "value") else str(platform)
        platform_of[conv_id] = name
        held.setdefault(name, 0)
        if isinstance(extra, dict) and extra.get("awaiting_human"):
            held[name] += 1
            reason = str(extra.get("handoff_reason") or "sin motivo registrado")[:120]
            held_reasons.setdefault(name, {})
            held_reasons[name][reason] = held_reasons[name].get(reason, 0) + 1

    messages = await db.execute(
        select(Message.conversation_id, Message.direction, Message.extra_data, Message.created_at)
        .where(Message.conversation_id.in_(list(platform_of)))
        .order_by(Message.created_at.asc())
    )

    first_inbound: dict[Any, datetime] = {}
    first_ai: dict[Any, datetime] = {}
    ai_touched: set[Any] = set()
    asked: set[Any] = set()
    for conv_id, direction, extra, created in messages.all():
        if direction == MessageDirection.INBOUND:
            first_inbound.setdefault(conv_id, created)
            asked.add(conv_id)
        elif isinstance(extra, dict) and str(extra.get("generated_by") or "").startswith("ai"):
            ai_touched.add(conv_id)
            if conv_id in first_inbound:
                first_ai.setdefault(conv_id, created)

    # Orders attributed to a conversation the bot answered in.
    orders = await db.execute(
        select(Order.conversation_id, Order.total_amount, Order.currency, Order.status)
        .where(Order.business_id.in_(business_ids), Order.is_active.is_(True))
    )
    revenue: dict[str, dict[str, float]] = {}
    order_counts: dict[str, int] = {}
    unattributed = 0
    for conv_id, amount, currency, _status in orders.all():
        if conv_id is None or conv_id not in platform_of:
            unattributed += 1
            continue
        if conv_id not in ai_touched:
            continue
        name = platform_of[conv_id]
        order_counts[name] = order_counts.get(name, 0) + 1
        revenue.setdefault(name, {})
        key = currency or "?"
        revenue[name][key] = round(revenue[name].get(key, 0.0) + float(amount or 0), 2)

    out: dict[str, dict[str, Any]] = {}
    for name in set(platform_of.values()):
        latencies = [
            (first_ai[c] - first_inbound[c]).total_seconds() / 60
            for c in first_ai
            if platform_of.get(c) == name and first_ai[c] >= first_inbound[c]
        ]
        platform_asked = {c for c in asked if platform_of.get(c) == name}
        platform_ai = {c for c in ai_touched if platform_of.get(c) == name}
        coverage = Proportion(len(platform_ai & platform_asked), len(platform_asked))
        med = median(latencies)
        out[name] = {
            "answered_by_ai": len(platform_ai & platform_asked),
            "asked": len(platform_asked),
            "coverage_percent": coverage.percent,
            "coverage_confidence": coverage.confidence,
            "coverage_reading": coverage.reading("consultas"),
            "median_first_reply_minutes": round(med, 1) if med is not None else None,
            "latency_sample": len(latencies),
            "held_for_human": held.get(name, 0),
            "held_reasons": sorted(
                ({"reason": reason, "count": count} for reason, count in held_reasons.get(name, {}).items()),
                key=lambda item: -item["count"],
            )[:4],
            "orders_after_ai": order_counts.get(name, 0),
            "revenue_after_ai": revenue.get(name, {}),
            # Said out loud: the bot being in the conversation does not prove it
            # caused the sale, and a small sample proves even less.
            "attribution_note": (
                "Son órdenes de conversaciones donde la IA respondió. No prueba que la IA haya "
                "cerrado la venta, y con menos de "
                f"{MIN_TO_READ} casos tampoco alcanza para leer una tendencia."
            ),
            "orders_without_conversation": unattributed,
        }
    return out


async def overview(db: AsyncSession, business_ids: list[uuid.UUID]) -> dict[str, Any]:
    """One row per connected platform: its bot, and what that bot really did."""
    from app.domains.channels.models import ChannelConnection

    if not business_ids:
        return {"bots": [], "has_business": False}

    connections = await db.execute(
        select(ChannelConnection).where(
            ChannelConnection.business_id.in_(business_ids),
            ChannelConnection.is_active.is_(True),
        )
    )
    stats = await platform_stats(db, business_ids)
    performance = await platform_performance(db, business_ids)

    bots: list[dict[str, Any]] = []
    seen: set[str] = set()
    for channel in connections.scalars().all():
        platform = channel.platform.value if hasattr(channel.platform, "value") else str(channel.platform)
        if platform in seen:
            continue
        seen.add(platform)

        bot = await get_bot(db, channel.business_id, platform)
        config = serialize(bot) if bot else {
            "platform": platform,
            "enabled": False,
            "personality_slug": None,
            "focus": BotFocus.AUTO.value,
            "focus_label": FOCUS_LABELS[BotFocus.AUTO.value],
            "custom_instructions": None,
            "handoff_keywords": [],
            "max_ai_replies": None,
            "active_hours": None,
            "after_hours_message": None,
            "escalate_on_frustration": False,
            "hold_on_policy_violation": True,
            "updated_at": None,
        }
        bots.append({
            **config,
            "configured": bot is not None,
            "stats": stats.get(platform, {
                "conversations": 0, "inbound": 0, "ai_replies": 0,
                "human_replies": 0, "waiting": 0,
            }),
            # The rules this platform imposes, shown so the seller can see what
            # the bot is being held to instead of guessing.
            "playbook": playbooks.describe(platform),
            "performance": performance.get(platform),
        })

    return {
        "bots": sorted(bots, key=lambda b: b["platform"]),
        "has_business": True,
        "focus_options": [
            {"value": value, "label": label} for value, label in FOCUS_LABELS.items()
        ],
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def personalities(db: AsyncSession, limit: int = 60) -> list[dict[str, Any]]:
    """The real personalities seeded in this deployment."""
    from app.domains.agents.models import AgentPersonality

    result = await db.execute(
        select(AgentPersonality)
        .where(AgentPersonality.is_active.is_(True))
        .order_by(AgentPersonality.display_order.asc())
        .limit(limit)
    )
    return [
        {
            "slug": p.slug,
            "name": p.name,
            "emoji": p.emoji,
            "tagline": p.tagline,
        }
        for p in result.scalars().all()
    ]


async def test_reply(
    db: AsyncSession,
    business_id: uuid.UUID,
    platform: str,
    question: str,
) -> dict[str, Any]:
    """What this platform's bot WOULD answer, without sending anything.

    Runs the real generation path against a throwaway in-memory conversation, so
    what the seller reads in the test is what a buyer would receive -- not a
    sample written for the demo.
    """
    from app.domains.agents.ai_reply import generate_ai_response
    from app.domains.channels.models import Conversation

    from .brief import build_brief, check_hours, vet_reply

    bot = await get_bot(db, business_id, platform)
    focus = (bot.focus.value if bot and isinstance(bot.focus, BotFocus) else BotFocus.AUTO.value)

    # The same brief the live path builds: platform rules plus the seller's
    # configured languages, banned topics and voice. Testing with a different
    # prompt than production would make the preview worthless.
    brief = await build_brief(db, business_id, platform, bot)
    hours = check_hours(bot.active_hours if bot else None)

    # Not added to the session: this conversation must never reach the database
    # or a seller's inbox. It exists only to carry the question into the prompt.
    draft = Conversation(
        id=uuid.uuid4(),
        business_id=business_id,
        lead_name="Comprador de prueba",
        extra_data={"test_preview": True, "last_message": question},
    )

    try:
        reply = await generate_ai_response(
            db=db,
            conversation=draft,
            personality_slug=(bot.personality_slug if bot and bot.personality_slug else DEFAULT_PERSONALITY),
            business_id=business_id,
            custom_prompt=f"{brief.prompt}\n\nMensaje del comprador: {question}",
            force_stage=None if focus == BotFocus.AUTO.value else focus,
            max_tokens=500,
        )
    except Exception as e:  # noqa: BLE001 -- a failed generation is a real answer
        logger.warning("chatbot test failed for %s: %s", platform, str(e)[:200])
        return {"ok": False, "reason": str(e)[:200], "brief_sources": brief.sources}

    context = {
        "focus": focus,
        "playbook": playbooks.describe(platform),
        # What really fed this reply, so the seller can tell whether their
        # configuration is reaching the bot at all.
        "brief_sources": brief.sources,
        "brief_missing": brief.missing,
        "within_hours": hours.within_hours,
        "hours_note": hours.reason,
    }

    if not reply:
        return {
            "ok": False,
            "reason": (
                "El proveedor de IA no devolvió respuesta. Suele ser saldo agotado o falta de "
                "clave configurada: revisá Integraciones."
            ),
            **context,
        }

    # Run the same vetting the live path runs, and report it: a preview that
    # hides the fact that the reply would have been held is a lie.
    verdict = vet_reply(
        platform, reply, hold_on_violation=bool(bot.hold_on_policy_violation) if bot else True
    )
    return {
        "ok": True,
        "reply": verdict.text,
        "raw_reply": reply if verdict.text != reply else None,
        "would_send": verdict.send,
        "policy_problems": verdict.problems,
        "trimmed": verdict.trimmed,
        **context,
    }
