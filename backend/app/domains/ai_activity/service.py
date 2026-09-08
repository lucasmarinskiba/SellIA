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

    return {
        "registration": registration,
        "questionnaire": questionnaire,
        "ai_activity": {
            "total_actions": total_actions,
            "last_action_at": last_action_at.isoformat() if last_action_at else None,
        },
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
