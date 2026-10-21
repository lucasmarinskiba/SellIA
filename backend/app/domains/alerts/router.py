"""Alerts API Router"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.alerts.schemas import (
    AlertResponse,
    AlertRuleCreate,
    AlertRuleResponse,
    AlertRuleUpdate,
    AlertStatsResponse,
    RecommendationApplyRequest,
    RecommendationResponse,
)
from app.domains.alerts.service import AlertService
from app.domains.businesses.models import Business
from app.domains.channels.token_rotation import RotationNotPossible
from app.domains.users.models import User

router = APIRouter(prefix="/alerts", tags=["alerts"])


# ========== Alert Rules ==========


@router.get("/rules", response_model=list[AlertRuleResponse])
async def list_rules(
    business_id: Annotated[UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    svc = AlertService(db)
    return await svc.list_rules(business_id)


@router.post(
    "/rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED
)
async def create_rule(
    data: AlertRuleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    svc = AlertService(db)
    return await svc.create_rule(data)


@router.patch("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_rule(
    rule_id: UUID,
    data: AlertRuleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    svc = AlertService(db)
    rule = await svc.update_rule(rule_id, data)
    if not rule:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return rule


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    svc = AlertService(db)
    if not await svc.delete_rule(rule_id):
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return {"message": "Regla eliminada"}


# ========== Alerts ==========


@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    business_id: Annotated[UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    status: str | None = None,
    severity: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    svc = AlertService(db)
    return await svc.list_alerts(business_id, status, severity, limit, offset)


@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    business_id: Annotated[UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    svc = AlertService(db)
    return await svc.get_stats(business_id)


@router.patch("/{alert_id}/read", response_model=AlertResponse)
async def mark_alert_read(
    alert_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    svc = AlertService(db)
    alert = await svc.mark_read(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alert


@router.patch("/{alert_id}/dismiss", response_model=AlertResponse)
async def dismiss_alert(
    alert_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    svc = AlertService(db)
    alert = await svc.dismiss_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alert


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    svc = AlertService(db)
    if not await svc.delete_alert(alert_id):
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return {"message": "Alerta eliminada"}


# ========== Recommendations ==========


async def _require_business_owner(
    db: AsyncSession, business_id: UUID, user: User
) -> None:
    """404 unless ``user`` owns ``business_id``: recommendations can change things (e.g. rotate a
    webhook token), so being logged in is not enough to read or answer someone else's.
    """
    if getattr(user, "is_superuser", False):
        return
    owned = await db.execute(
        select(Business.id).where(
            Business.id == business_id, Business.user_id == user.id
        )
    )
    if owned.first() is None:
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")


async def _owned_recommendation(db: AsyncSession, rec_id: UUID, user: User):
    rec = await AlertService(db).get_recommendation(rec_id)
    if rec is None:
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")
    await _require_business_owner(db, rec.business_id, user)


@router.get("/recommendations", response_model=list[RecommendationResponse])
async def list_recommendations(
    business_id: Annotated[UUID, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    status: Annotated[str | None, Query()] = "pending",
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
):
    await _require_business_owner(db, business_id, current_user)
    svc = AlertService(db)
    return await svc.list_recommendations(business_id, status, limit)


@router.post("/recommendations/{rec_id}/apply", response_model=RecommendationResponse)
async def apply_recommendation(
    rec_id: UUID,
    req: RecommendationApplyRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    await _owned_recommendation(db, rec_id, current_user)
    svc = AlertService(db)
    try:
        # the answer is attributed to the authenticated user, never to a user_id sent in the body
        rec = await svc.apply_recommendation(rec_id, current_user.id)
    except RotationNotPossible as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if not rec:
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")
    return rec


@router.post("/recommendations/{rec_id}/dismiss", response_model=RecommendationResponse)
async def dismiss_recommendation(
    rec_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    await _owned_recommendation(db, rec_id, current_user)
    svc = AlertService(db)
    rec = await svc.dismiss_recommendation(rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")
    return rec
