"""Autopilot Engine API Router."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.autopilot.models import AutopilotConfig, AutopilotActionLog, AutopilotDailyReport, AutopilotActionStatus
from app.domains.autopilot.schemas import (
    AutopilotConfigResponse,
    AutopilotConfigUpdate,
    AutopilotActionLogResponse,
    AutopilotActionLogFilter,
    AutopilotActionApproveRequest,
    AutopilotActionRejectRequest,
    AutopilotDailyReportResponse,
    AutopilotStatusResponse,
    AutopilotOverviewResponse,
    OvernightReportResponse,
)
from app.domains.autopilot.service import AutopilotEngine, AutopilotReportService
from app.domains.autopilot.overnight_story import OvernightStoryEngine

router = APIRouter(prefix="/autopilot", tags=["Autopilot"])


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

@router.get("/config/{business_id}", response_model=AutopilotConfigResponse)
async def get_autopilot_config(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = AutopilotEngine(db)
    config = await engine.get_or_create_config(business_id)
    return AutopilotConfigResponse.model_validate(config)


@router.patch("/config/{business_id}", response_model=AutopilotConfigResponse)
async def update_autopilot_config(
    business_id: UUID,
    update: AutopilotConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = AutopilotEngine(db)
    config = await engine.get_or_create_config(business_id)

    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)
    return AutopilotConfigResponse.model_validate(config)


# ---------------------------------------------------------------------------
# Status & Overview
# ---------------------------------------------------------------------------

@router.get("/status/{business_id}", response_model=AutopilotStatusResponse)
async def get_autopilot_status(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = AutopilotEngine(db)
    config = await engine.get_or_create_config(business_id)
    counts = await engine.get_today_counts(business_id)
    last_action = await engine.get_last_action(business_id)

    # Get today's revenue
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    from sqlalchemy import func as sa_func
    revenue_result = await db.execute(
        select(sa_func.sum(AutopilotActionLog.revenue_impact)).where(
            AutopilotActionLog.business_id == business_id,
            AutopilotActionLog.status == AutopilotActionStatus.EXECUTED,
            AutopilotActionLog.created_at >= today_start,
        )
    )
    today_revenue = revenue_result.scalar() or 0

    return AutopilotStatusResponse(
        business_id=business_id,
        is_active=config.is_active,
        is_paused=config.is_paused,
        paused_reason=config.paused_reason,
        today_executed=counts.get("executed", 0),
        today_pending=counts.get("pending_approval", 0),
        today_escalated=counts.get("escalated", 0),
        today_revenue=today_revenue,
        last_action_at=last_action,
    )


@router.get("/overview/{business_id}", response_model=AutopilotOverviewResponse)
async def get_autopilot_overview(
    business_id: UUID,
    period: str = "last_24h",  # last_24h, last_7d
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = AutopilotEngine(db)
    report_service = AutopilotReportService(db)

    latest_report = await report_service.get_latest_report(business_id)

    # Pending actions
    pending_result = await db.execute(
        select(AutopilotActionLog).where(
            AutopilotActionLog.business_id == business_id,
            AutopilotActionLog.status == AutopilotActionStatus.PENDING_APPROVAL,
        ).order_by(desc(AutopilotActionLog.created_at)).limit(10)
    )
    pending_actions = pending_result.scalars().all()

    # Escalations (last 24h)
    since = datetime.now(timezone.utc) - timedelta(hours=24)
    escalated_result = await db.execute(
        select(AutopilotActionLog).where(
            AutopilotActionLog.business_id == business_id,
            AutopilotActionLog.status == AutopilotActionStatus.ESCALATED,
            AutopilotActionLog.created_at >= since,
        ).order_by(desc(AutopilotActionLog.created_at)).limit(10)
    )
    escalations = escalated_result.scalars().all()

    summary = {
        "revenue_today": float(latest_report.revenue_generated) if latest_report else 0,
        "deals_closed_today": latest_report.deals_closed if latest_report else 0,
        "messages_sent_today": latest_report.messages_sent if latest_report else 0,
        "leads_contacted_today": latest_report.leads_contacted if latest_report else 0,
    }

    message = latest_report.ai_summary if latest_report else "No hay reporte disponible aún."

    return AutopilotOverviewResponse(
        business_id=business_id,
        message=message,
        period=period,
        summary=summary,
        pending_actions=[AutopilotActionLogResponse.model_validate(a) for a in pending_actions],
        escalations=[AutopilotActionLogResponse.model_validate(a) for a in escalations],
    )


# ---------------------------------------------------------------------------
# Audit Log
# ---------------------------------------------------------------------------

@router.get("/audit-log/{business_id}", response_model=list[AutopilotActionLogResponse])
async def list_audit_logs(
    business_id: UUID,
    status: AutopilotActionStatus | None = None,
    action_type: str | None = None,
    entity_type: str | None = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = select(AutopilotActionLog).where(
        AutopilotActionLog.business_id == business_id,
    )
    if status:
        query = query.where(AutopilotActionLog.status == status)
    if action_type:
        query = query.where(AutopilotActionLog.action_type == action_type)
    if entity_type:
        query = query.where(AutopilotActionLog.entity_type == entity_type)

    query = query.order_by(desc(AutopilotActionLog.created_at)).offset(offset).limit(limit)
    result = await db.execute(query)
    logs = result.scalars().all()
    return [AutopilotActionLogResponse.model_validate(log) for log in logs]


# ---------------------------------------------------------------------------
# Approve / Reject
# ---------------------------------------------------------------------------

@router.post("/approve/{action_id}", response_model=AutopilotActionLogResponse)
async def approve_action(
    action_id: UUID,
    req: AutopilotActionApproveRequest | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = AutopilotEngine(db)
    log = await engine.approve_action(action_id, current_user.id, req.reason if req else None)
    if not log:
        raise HTTPException(status_code=404, detail="Action not found or not pending")
    return AutopilotActionLogResponse.model_validate(log)


@router.post("/reject/{action_id}", response_model=AutopilotActionLogResponse)
async def reject_action(
    action_id: UUID,
    req: AutopilotActionRejectRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = AutopilotEngine(db)
    log = await engine.reject_action(action_id, req.reason)
    if not log:
        raise HTTPException(status_code=404, detail="Action not found or not pending")
    return AutopilotActionLogResponse.model_validate(log)


# ---------------------------------------------------------------------------
# Pause / Resume
# ---------------------------------------------------------------------------

@router.post("/pause/{business_id}", response_model=AutopilotConfigResponse)
async def pause_autopilot(
    business_id: UUID,
    reason: str = "Paused by user",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = AutopilotEngine(db)
    config = await engine.get_or_create_config(business_id)
    config.is_paused = True
    config.paused_reason = reason
    config.paused_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(config)
    return AutopilotConfigResponse.model_validate(config)


@router.post("/resume/{business_id}", response_model=AutopilotConfigResponse)
async def resume_autopilot(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = AutopilotEngine(db)
    config = await engine.get_or_create_config(business_id)
    config.is_paused = False
    config.paused_reason = None
    config.paused_at = None
    await db.commit()
    await db.refresh(config)
    return AutopilotConfigResponse.model_validate(config)


# ---------------------------------------------------------------------------
# Daily Reports
# ---------------------------------------------------------------------------

@router.get("/daily-reports/{business_id}", response_model=list[AutopilotDailyReportResponse])
async def list_daily_reports(
    business_id: UUID,
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(AutopilotDailyReport).where(
            AutopilotDailyReport.business_id == business_id,
        ).order_by(desc(AutopilotDailyReport.report_date)).limit(limit)
    )
    reports = result.scalars().all()
    return [AutopilotDailyReportResponse.model_validate(r) for r in reports]


# ---------------------------------------------------------------------------
# Overnight Report (Mientras Dormías)
# ---------------------------------------------------------------------------

@router.get("/overnight-report/{business_id}", response_model=OvernightReportResponse)
async def get_overnight_report(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    engine = OvernightStoryEngine(db)
    report = await engine.generate_overnight_report(
        business_id=business_id,
        user_name=current_user.full_name or current_user.email or "",
    )
    return OvernightReportResponse.model_validate(report)
