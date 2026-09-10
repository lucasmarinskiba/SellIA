"""AI Activity service: write path (log_ai_action) + read path (summary/list).

log_ai_action() is deliberately fire-and-forget and failure-isolated: it opens
its OWN short-lived DB session rather than reusing the caller's, and never
raises -- a logging hiccup must never break the real action it's describing
(same "best-effort, never break the hot path" rule the in-memory
BrainActivityBus already follows, just persisted this time).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

logger = get_logger(__name__)


async def _safe_rollback(db: AsyncSession) -> None:
    """Undo a failed statement so the caller's session stays usable.

    Postgres aborts the whole transaction on the first failing statement, so a
    lookup that fails and is only logged still kills every query that follows --
    including ones in a completely different feature that merely called this
    function. A missing `orders` table was taking down the authority dashboard
    this way.
    """
    try:
        await db.rollback()
    except Exception:  # noqa: BLE001
        pass


async def log_ai_action(
    *,
    user_id: Optional[uuid.UUID | str],
    action: str,
    summary: str,
    business_id: Optional[uuid.UUID | str] = None,
    actor_type: str = "system",
    actor_id: Optional[str] = None,
    payload: Optional[dict[str, Any]] = None,
    status: str = "success",
) -> None:
    """Persist one AI/automation action. Silent no-op if user_id is missing --
    an unattributable row (no known SellIA account) is worse than no row."""
    if not user_id:
        return
    try:
        from app.core.database import AsyncSessionLocal
        from .models import AIActionLog

        async with AsyncSessionLocal() as db:
            db.add(AIActionLog(
                user_id=user_id,
                business_id=business_id,
                actor_type=actor_type,
                actor_id=actor_id,
                action=action,
                summary=summary[:2000],
                payload=payload or {},
                status=status,
            ))
            await db.commit()
    except Exception as e:  # noqa: BLE001
        logger.warning("log_ai_action failed (%s/%s): %s", action, actor_id, str(e)[:200])


async def list_recent_actions(
    db: AsyncSession,
    user_id: uuid.UUID,
    limit: int = 50,
) -> list[dict[str, Any]]:
    from .models import AIActionLog

    result = await db.execute(
        select(AIActionLog)
        .where(AIActionLog.user_id == user_id)
        .order_by(AIActionLog.created_at.desc())
        .limit(min(limit, 200))
    )
    rows = result.scalars().all()
    return [
        {
            "id": str(r.id),
            "business_id": str(r.business_id) if r.business_id else None,
            "actor_type": r.actor_type,
            "actor_id": r.actor_id,
            "action": r.action,
            "summary": r.summary,
            "payload": r.payload,
            "status": r.status,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


async def get_account_kpis(db: AsyncSession, user) -> dict[str, Any]:
    """Real, per-account KPIs -- everything here belongs to THIS user.

    The Brain page's KPI row used to be fed by GET /brain/kpis, which
    aggregates the whole `leads` table with no ownership filter at all (that
    table has no user_id/business_id column, so its rows cannot be attributed
    to anyone). A brand-new account therefore saw "4 leads activos ·
    $55.8K pipeline" that were not its own -- exactly the invented activity
    this endpoint exists to replace. Every number below is scoped through
    Business.user_id, and an account with nothing yet honestly gets zeros.
    """
    from .models import AIActionLog
    from app.domains.businesses.models import Business
    from app.domains.channels.models import (
        ChannelConnection, Conversation, Message, MessageDirection,
    )

    biz_ids_q = select(Business.id).where(Business.user_id == user.id)

    channels_result = await db.execute(
        select(func.count())
        .select_from(ChannelConnection)
        .where(
            ChannelConnection.business_id.in_(biz_ids_q),
            ChannelConnection.is_active.is_(True),
        )
    )
    channels_connected = channels_result.scalar() or 0

    conv_ids_q = select(Conversation.id).where(
        Conversation.business_id.in_(biz_ids_q),
        Conversation.is_active.is_(True),
    )
    conv_result = await db.execute(
        select(func.count()).select_from(conv_ids_q.subquery())
    )
    conversations_total = conv_result.scalar() or 0

    msgs_result = await db.execute(
        select(func.count())
        .select_from(Message)
        .where(Message.conversation_id.in_(conv_ids_q))
    )
    messages_total = msgs_result.scalar() or 0

    # Only messages the AI itself composed carry extra_data.generated_by ==
    # "ai" (set at the real generation call sites in channels/services.py and
    # automations/engine.py), so a human replying through the same inbox is
    # never counted as an AI reply.
    ai_msgs_result = await db.execute(
        select(func.count())
        .select_from(Message)
        .where(
            Message.conversation_id.in_(conv_ids_q),
            Message.direction == MessageDirection.OUTBOUND,
            Message.extra_data["generated_by"].astext == "ai",
        )
    )
    messages_ai = ai_msgs_result.scalar() or 0

    actions_result = await db.execute(
        select(func.count()).select_from(AIActionLog).where(AIActionLog.user_id == user.id)
    )
    ai_actions_total = actions_result.scalar() or 0

    last_action_result = await db.execute(
        select(AIActionLog.created_at)
        .where(AIActionLog.user_id == user.id)
        .order_by(AIActionLog.created_at.desc())
        .limit(1)
    )
    last_action_at = last_action_result.scalar_one_or_none()

    return {
        "channels_connected": channels_connected,
        "conversations_total": conversations_total,
        "messages_total": messages_total,
        "messages_ai": messages_ai,
        "ai_actions_total": ai_actions_total,
        "last_action_at": last_action_at.isoformat() if last_action_at else None,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


async def get_business_snapshot(db: AsyncSession, user) -> dict[str, Any]:
    """One honest, per-account picture of the business: verification signals,
    real per-platform channel activity and real order revenue.

    This exists because the dashboard's SEO / authority / multi-platform pages
    were rendering invented figures -- "Trust Score 82.5 GOLD" came from a
    backend that literally called random.uniform(), "$550k GMV / 350 listings /
    8.0% conversion" was a hardcoded frontend fallback, and none of it was tied
    to the signed-in account. Every field below is counted from this account's
    own rows; an account with nothing gets zeros and empty lists, never a
    plausible-looking number.
    """
    from app.domains.businesses.models import Business
    from app.domains.channels.models import (
        ChannelConnection, Conversation, Message, MessageDirection,
    )
    from app.domains.orders.models import Order, OrderStatus
    from app.domains.websites.models import Website, Domain

    biz_rows = await db.execute(
        select(Business.id, Business.name).where(Business.user_id == user.id)
    )
    businesses = biz_rows.all()
    business_ids = [b[0] for b in businesses]

    now = datetime.now(timezone.utc)
    created = getattr(user, "created_at", None)
    account_age_days = (now - created).days if created else 0

    snapshot: dict[str, Any] = {
        "business": {
            "id": str(business_ids[0]) if business_ids else None,
            "name": businesses[0][1] if businesses else None,
            "count": len(businesses),
        },
        "verification": {
            "email_verified": bool(getattr(user, "email_verified", False)),
            "two_factor_enabled": bool(getattr(user, "is_2fa_enabled", False)),
            "account_age_days": account_age_days,
            "has_business": bool(business_ids),
            "website_published": False,
            "domain_verified": False,
            "subdomain": None,
        },
        "channels": [],
        "conversations": {
            "total": 0, "inbound": 0, "answered": 0, "ai_answered": 0,
            "response_rate": 0.0, "ai_share": 0.0,
        },
        "revenue": {
            "orders_total": 0, "orders_paid": 0,
            "gross_amount": 0.0, "paid_amount": 0.0, "currency": None,
        },
        "generated_at": now.isoformat(),
    }

    if not business_ids:
        return snapshot

    # ── Website / domain: real publication + verification state ──
    try:
        site_rows = await db.execute(
            select(Website.status, Domain.subdomain, Domain.is_verified)
            .outerjoin(Domain, Domain.website_id == Website.id)
            .where(Website.business_id.in_(business_ids))
            .limit(1)
        )
        row = site_rows.first()
        if row:
            status, subdomain, verified = row
            snapshot["verification"]["website_published"] = str(getattr(status, "value", status)).lower() == "published"
            snapshot["verification"]["subdomain"] = subdomain
            snapshot["verification"]["domain_verified"] = bool(verified)
    except Exception as e:  # noqa: BLE001
        logger.warning("business snapshot: website lookup failed: %s", str(e)[:200])
        await _safe_rollback(db)

    # ── Channels: one row per real connection, with its real traffic ──
    try:
        conn_rows = await db.execute(
            select(ChannelConnection)
            .where(ChannelConnection.business_id.in_(business_ids))
            .where(ChannelConnection.is_active.is_(True))
        )
        for conn in conn_rows.scalars().all():
            conv_ids_q = select(Conversation.id).where(
                Conversation.channel_connection_id == conn.id,
                Conversation.is_active.is_(True),
            )
            conv_count = (await db.execute(
                select(func.count()).select_from(conv_ids_q.subquery())
            )).scalar() or 0
            ai_count = (await db.execute(
                select(func.count()).select_from(Message).where(
                    Message.conversation_id.in_(conv_ids_q),
                    Message.direction == MessageDirection.OUTBOUND,
                    Message.extra_data["generated_by"].astext == "ai",
                )
            )).scalar() or 0
            last_msg = (await db.execute(
                select(func.max(Message.created_at)).where(Message.conversation_id.in_(conv_ids_q))
            )).scalar()
            snapshot["channels"].append({
                "platform": getattr(conn.platform, "value", str(conn.platform)),
                "name": conn.name,
                "status": getattr(conn.status, "value", str(conn.status)),
                "conversations": conv_count,
                "ai_replies": ai_count,
                "last_message_at": last_msg.isoformat() if last_msg else None,
            })
    except Exception as e:  # noqa: BLE001
        logger.warning("business snapshot: channels lookup failed: %s", str(e)[:200])
        await _safe_rollback(db)

    # ── Conversations: real response rate, real AI share ──
    try:
        conv_ids_q = select(Conversation.id).where(
            Conversation.business_id.in_(business_ids),
            Conversation.is_active.is_(True),
        )
        total = (await db.execute(select(func.count()).select_from(conv_ids_q.subquery()))).scalar() or 0

        inbound_convs = select(Message.conversation_id).where(
            Message.conversation_id.in_(conv_ids_q),
            Message.direction == MessageDirection.INBOUND,
        ).distinct()
        inbound = (await db.execute(select(func.count()).select_from(inbound_convs.subquery()))).scalar() or 0

        answered_convs = select(Message.conversation_id).where(
            Message.conversation_id.in_(inbound_convs),
            Message.direction == MessageDirection.OUTBOUND,
        ).distinct()
        answered = (await db.execute(select(func.count()).select_from(answered_convs.subquery()))).scalar() or 0

        ai_convs = select(Message.conversation_id).where(
            Message.conversation_id.in_(inbound_convs),
            Message.direction == MessageDirection.OUTBOUND,
            Message.extra_data["generated_by"].astext == "ai",
        ).distinct()
        ai_answered = (await db.execute(select(func.count()).select_from(ai_convs.subquery()))).scalar() or 0

        snapshot["conversations"] = {
            "total": total,
            "inbound": inbound,
            "answered": answered,
            "ai_answered": ai_answered,
            "response_rate": round(answered / inbound * 100, 1) if inbound else 0.0,
            "ai_share": round(ai_answered / answered * 100, 1) if answered else 0.0,
        }
    except Exception as e:  # noqa: BLE001
        logger.warning("business snapshot: conversations lookup failed: %s", str(e)[:200])
        await _safe_rollback(db)

    # ── Revenue: real orders only (no projections, no "avg ticket" guesses) ──
    try:
        rows = await db.execute(
            select(
                func.count(Order.id),
                func.coalesce(func.sum(Order.total_amount), 0),
                func.max(Order.currency),
            ).where(Order.business_id.in_(business_ids))
        )
        orders_total, gross, currency = rows.one()

        paid_rows = await db.execute(
            select(func.count(Order.id), func.coalesce(func.sum(Order.total_amount), 0)).where(
                Order.business_id.in_(business_ids),
                Order.status.in_([OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED]),
            )
        )
        orders_paid, paid_amount = paid_rows.one()

        snapshot["revenue"] = {
            "orders_total": orders_total or 0,
            "orders_paid": orders_paid or 0,
            "gross_amount": float(gross or 0),
            "paid_amount": float(paid_amount or 0),
            "currency": currency,
        }
    except Exception as e:  # noqa: BLE001
        logger.warning("business snapshot: orders lookup failed: %s", str(e)[:200])
        await _safe_rollback(db)

    return snapshot


async def get_account_summary(db: AsyncSession, user) -> dict[str, Any]:
    """Registration + questionnaire + AI-activity completeness for one user.

    Ties together three things that previously had no single place they were
    all visible together: how the account was created, how much of the
    business-context questionnaire it has actually answered, and what SellIA's
    AI has actually done for it since.
    """
    from .models import AIActionLog
    from app.domains.business_context.service import BusinessContextService

    registration = {
        "email": user.email,
        "full_name": user.full_name,
        "email_verified": bool(user.email_verified),
        "is_2fa_enabled": bool(user.is_2fa_enabled),
        "created_at": user.created_at.isoformat() if user.created_at else None,
        "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
    }

    questionnaire: dict[str, Any] = {"has_context": False}
    try:
        svc = BusinessContextService(db)
        ctx = await svc.get_or_create_context(user.id, None)
        wizard = await svc.get_wizard_state(user.id, ctx.id)
        completed_steps = sum(1 for s in wizard.steps if s.is_completed)
        questionnaire = {
            "has_context": True,
            "context_id": str(ctx.id),
            "current_step": wizard.current_step,
            "total_steps": wizard.total_steps,
            "completed_steps": completed_steps,
            "is_fully_complete": completed_steps == wizard.total_steps,
            "business_type": ctx.business_type.value if ctx.business_type else None,
            "industry": ctx.industry,
        }
    except Exception as e:  # noqa: BLE001
        logger.warning("get_account_summary: questionnaire lookup failed: %s", str(e)[:200])
        await _safe_rollback(db)

    total_result = await db.execute(
        select(func.count()).select_from(AIActionLog).where(AIActionLog.user_id == user.id)
    )
    total_actions = total_result.scalar() or 0

    last_result = await db.execute(
        select(AIActionLog.created_at)
        .where(AIActionLog.user_id == user.id)
        .order_by(AIActionLog.created_at.desc())
        .limit(1)
    )
    last_action_at = last_result.scalar_one_or_none()

    # Real setup readiness -- the single source of truth for whether this
    # account's AI agents/automations should be presented as genuinely
    # active anywhere in the UI. Before this, the Brain page's own
    # "¿está todo listo?" gate read a completely different, localStorage-only
    # "business profile" (frontend/src/lib/business-profile.ts) that never
    # touches this database at all -- a user could fill that local form and
    # see "AGENTE ACTIVO" while their real BusinessContext stayed empty (or
    # vice versa: finish the real questionnaire via /sellia-onboarding and
    # still see "Completá tu negocio" on the Brain page), because the two
    # systems never talked to each other.
    setup: dict[str, Any] = {
        "has_business": False,
        "has_subdomain": False,
        "questionnaire_complete": bool(questionnaire.get("is_fully_complete")),
        "has_channel_declared": False,
    }
    try:
        from app.domains.businesses.models import Business
        from app.domains.websites.models import Website, Domain

        biz_result = await db.execute(
            select(Business.id).where(Business.user_id == user.id).limit(1)
        )
        business_id = biz_result.scalar_one_or_none()
        setup["has_business"] = business_id is not None

        if business_id:
            domain_result = await db.execute(
                select(Domain.subdomain)
                .join(Website, Domain.website_id == Website.id)
                .where(Website.business_id == business_id)
                .limit(1)
            )
            subdomain = domain_result.scalar_one_or_none()
            setup["has_subdomain"] = subdomain is not None
            setup["subdomain"] = subdomain
    except Exception as e:  # noqa: BLE001
        logger.warning("get_account_summary: setup/subdomain lookup failed: %s", str(e)[:200])
        await _safe_rollback(db)

    if questionnaire.get("has_context"):
        try:
            from app.domains.business_context.models import BusinessContext

            ctx_result = await db.execute(
                select(BusinessContext.channels_configured).where(
                    BusinessContext.id == uuid.UUID(questionnaire["context_id"])
                )
            )
            channels = ctx_result.scalar_one_or_none() or {}
            setup["has_channel_declared"] = any(bool(v) for v in channels.values())
        except Exception as e:  # noqa: BLE001
            logger.warning("get_account_summary: channels lookup failed: %s", str(e)[:200])
            await _safe_rollback(db)

    setup["setup_complete"] = (
        setup["has_business"]
        and setup["has_subdomain"]
        and setup["questionnaire_complete"]
        and setup["has_channel_declared"]
    )

    return {
        "registration": registration,
        "questionnaire": questionnaire,
        "setup": setup,
        "ai_activity": {
            "total_actions": total_actions,
            "last_action_at": last_action_at.isoformat() if last_action_at else None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
