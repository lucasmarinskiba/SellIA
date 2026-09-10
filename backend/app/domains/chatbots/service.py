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
            "updated_at": None,
        }
        bots.append({
            **config,
            "configured": bot is not None,
            "stats": stats.get(platform, {
                "conversations": 0, "inbound": 0, "ai_replies": 0,
                "human_replies": 0, "waiting": 0,
            }),
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

    bot = await get_bot(db, business_id, platform)
    focus = (bot.focus.value if bot and isinstance(bot.focus, BotFocus) else BotFocus.AUTO.value)

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
            custom_prompt=(
                (bot.custom_instructions or "") if bot else ""
            ) + f"\n\nMensaje del comprador: {question}",
            force_stage=None if focus == BotFocus.AUTO.value else focus,
            max_tokens=500,
        )
    except Exception as e:  # noqa: BLE001 -- a failed generation is a real answer
        logger.warning("chatbot test failed for %s: %s", platform, str(e)[:200])
        return {"ok": False, "reason": str(e)[:200]}

    if not reply:
        return {
            "ok": False,
            "reason": (
                "El proveedor de IA no devolvió respuesta. Suele ser saldo agotado o falta de "
                "clave configurada: revisá Integraciones."
            ),
        }
    return {"ok": True, "reply": reply, "focus": focus}
