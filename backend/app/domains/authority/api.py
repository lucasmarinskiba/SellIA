"""Authority builder API."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User

from . import service
from .models import ActionStatus, AuthorityAction

router = APIRouter(prefix="/authority-builder", tags=["Authority Builder"])


class StatusIn(BaseModel):
    status: ActionStatus


@router.get("/dashboard")
async def dashboard(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Score, six pillars, trend, chart analysis and the work queue.

    Measuring is the same call as reading: opening the screen records a snapshot
    (at most one per 6 h), which is what makes the trend real without asking the
    user to remember to press a button.
    """
    return await service.get_dashboard(db, user)


@router.post("/measure")
async def measure_now(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Force a fresh measurement — used after the user says they did the work."""
    snapshot = await service.capture_snapshot(db, user, force=True)
    return {
        "total_score": snapshot["total_score"],
        "captured_at": snapshot["captured_at"].isoformat(),
    }


@router.patch("/actions/{action_id}")
async def update_action(
    action_id: uuid.UUID,
    payload: StatusIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    action = await service.set_action_status(db, user.id, action_id, payload.status)
    if action is None:
        raise HTTPException(status_code=404, detail="Acción no encontrada")
    return service.serialize_action(action)


@router.post("/actions/{action_id}/personalize")
async def personalize(
    action_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Rewrite this action's message in the account's own voice with the real
    LLM. Answers with `source` so the UI can say whether it was written by the
    AI or is still the base template."""
    result = await db.execute(
        select(AuthorityAction).where(
            AuthorityAction.id == action_id, AuthorityAction.user_id == user.id
        )
    )
    action = result.scalar_one_or_none()
    if action is None:
        raise HTTPException(status_code=404, detail="Acción no encontrada")

    script, source = await service.personalize_script(db, user, action)
    if source == "ia" and script:
        action.script = script
        await db.commit()
    return {"script": script, "source": source}
