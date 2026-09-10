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

from . import automations, service
from .models import ActionStatus, AuthorityAction

router = APIRouter(prefix="/authority-builder", tags=["Authority Builder"])


class StatusIn(BaseModel):
    status: ActionStatus


class RunIn(BaseModel):
    #: Required for anything that messages the user's customers.
    confirm: bool = False
    #: Optional subset of the previewed recipients.
    conversation_ids: list[str] | None = None


async def _get_action(db: AsyncSession, user_id: uuid.UUID, action_id: uuid.UUID) -> AuthorityAction:
    result = await db.execute(
        select(AuthorityAction).where(
            AuthorityAction.id == action_id, AuthorityAction.user_id == user_id
        )
    )
    action = result.scalar_one_or_none()
    if action is None:
        raise HTTPException(status_code=404, detail="Acción no encontrada")
    return action


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


@router.get("/actions/{action_id}/preview")
async def preview_action(
    action_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """What running this action would actually do, with the real rows involved.

    For a review campaign that means the real customers who would be messaged:
    the user sees exactly who, from which channel, before anything is sent.
    """
    action = await _get_action(db, user.id, action_id)
    if not automations.is_executable(action.action_key):
        return {
            "executable": False,
            "reason": "Esta acción la tenés que hacer vos: SellIA no tiene forma de ejecutarla.",
        }

    if automations.needs_confirmation(action.action_key):
        business_ids = await service.business_ids_for(db, user.id)
        recipients = await automations.review_campaign_recipients(db, business_ids)
        return {
            "executable": True,
            "needs_confirmation": True,
            "recipients": recipients,
            "script": action.script,
            "warning": (
                "Se le va a enviar este mensaje a cada uno de estos clientes reales, por tu "
                "canal y con tu nombre. Revisá la lista antes de confirmar."
            ),
        }

    return {
        "executable": True,
        "needs_confirmation": False,
        "detail": (
            "Activa la respuesta automática de la IA en tus canales conectados: cada consulta "
            "nueva recibe una primera respuesta en segundos."
        ),
    }


@router.post("/actions/{action_id}/run")
async def run_action(
    action_id: uuid.UUID,
    payload: RunIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Execute a real automation.

    Anything that puts a message in front of the user's customers requires
    `confirm: true`, sent only after they reviewed the recipient list.
    """
    action = await _get_action(db, user.id, action_id)
    business_ids = await service.business_ids_for(db, user.id)
    if not business_ids:
        raise HTTPException(status_code=400, detail="Necesitás un negocio creado.")

    if not automations.is_executable(action.action_key):
        raise HTTPException(
            status_code=400,
            detail="Esta acción no es automatizable: la tenés que hacer vos.",
        )

    if automations.needs_confirmation(action.action_key) and not payload.confirm:
        raise HTTPException(
            status_code=400,
            detail="Falta confirmar el envío: revisá la lista de destinatarios primero.",
        )

    try:
        if automations.needs_confirmation(action.action_key):
            result = await automations.send_review_campaign(
                db, business_ids, action.script or "", payload.conversation_ids
            )
        else:
            result = await automations.enable_auto_reply(db, business_ids[0])
    except automations.NotExecutable as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    await service.set_action_status(db, user.id, action_id, ActionStatus.DONE)
    return result


@router.post("/actions/{action_id}/personalize")
async def personalize(
    action_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Rewrite this action's message in the account's own voice with the real
    LLM. Answers with `source` so the UI can say whether it was written by the
    AI or is still the base template."""
    action = await _get_action(db, user.id, action_id)
    script, source = await service.personalize_script(db, user, action)
    if source == "ia" and script:
        action.script = script
        await db.commit()
    return {"script": script, "source": source}
