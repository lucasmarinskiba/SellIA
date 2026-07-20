"""Alerts API Router"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.alerts.service import AlertService
from app.domains.alerts.schemas import (
    AlertRuleCreate, AlertRuleUpdate, AlertRuleResponse,
    AlertResponse, AlertStatsResponse,
    RecommendationResponse, RecommendationApplyRequest,
)

router = APIRouter(prefix="/alerts", tags=["alerts"])


# ========== Alert Rules ==========

@router.get("/rules", response_model=list[AlertRuleResponse])
async def list_rules(
    business_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AlertService(db)
    return await svc.list_rules(business_id)


@router.post("/rules", response_model=AlertRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: AlertRuleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AlertService(db)
    return await svc.create_rule(data)


@router.patch("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_rule(
    rule_id: UUID,
    data: AlertRuleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AlertService(db)
    rule = await svc.update_rule(rule_id, data)
    if not rule:
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return rule


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AlertService(db)
    if not await svc.delete_rule(rule_id):
        raise HTTPException(status_code=404, detail="Regla no encontrada")
    return {"message": "Regla eliminada"}


# ========== Alerts ==========

@router.get("", response_model=list[AlertResponse])
async def list_alerts(
    business_id: UUID = Query(...),
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AlertService(db)
    return await svc.list_alerts(business_id, status, severity, limit, offset)


@router.get("/stats", response_model=AlertStatsResponse)
async def get_alert_stats(
    business_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AlertService(db)
    return await svc.get_stats(business_id)


@router.patch("/{alert_id}/read", response_model=AlertResponse)
async def mark_alert_read(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AlertService(db)
    alert = await svc.mark_read(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alert


@router.patch("/{alert_id}/dismiss", response_model=AlertResponse)
async def dismiss_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AlertService(db)
    alert = await svc.dismiss_alert(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return alert


@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AlertService(db)
    if not await svc.delete_alert(alert_id):
        raise HTTPException(status_code=404, detail="Alerta no encontrada")
    return {"message": "Alerta eliminada"}


# ========== Recommendations ==========

@router.get("/recommendations", response_model=list[RecommendationResponse])
async def list_recommendations(
    business_id: UUID = Query(...),
    status: Optional[str] = Query("pending"),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AlertService(db)
    return await svc.list_recommendations(business_id, status, limit)


@router.post("/recommendations/{rec_id}/apply", response_model=RecommendationResponse)
async def apply_recommendation(
    rec_id: UUID,
    req: RecommendationApplyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AlertService(db)
    rec = await svc.apply_recommendation(rec_id, req.user_id or current_user.id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")
    return rec


@router.post("/recommendations/{rec_id}/dismiss", response_model=RecommendationResponse)
async def dismiss_recommendation(
    rec_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AlertService(db)
    rec = await svc.dismiss_recommendation(rec_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Recomendación no encontrada")
    return rec
