"""
Consumo Router

User-facing endpoints for Consumo dashboard inside Configuración.
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.consumo import service as consumo_service
from app.domains.consumo.schemas import (
    CostAttributionSummary,
    QualityGateConfigOut,
    QualityGateConfigUpdate,
    PlanRecommendationOut,
    OnboardingProgressOut,
    OnboardingHelpRequest,
    OnboardingHelpResponse,
    UserMarginOut,
)

router = APIRouter(prefix="/consumo", tags=["consumo"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ===== COST ATTRIBUTION =====

@router.get("/cost-attribution", response_model=CostAttributionSummary)
async def get_cost_attribution(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: int = Query(30, ge=1, le=90),
):
    """Get AI cost attribution summary for the current user."""
    return await consumo_service.get_cost_attribution_summary(
        db, user_id=current_user.id, days=days
    )


@router.get("/admin/margins", response_model=list[UserMarginOut])
async def get_admin_margins(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: int = Query(30, ge=1, le=90),
):
    """Admin-only: margin analysis per user."""
    # TODO: add admin role check
    return await consumo_service.get_user_margins(db, days=days)


# ===== QUALITY GATE =====

@router.get("/quality-gate", response_model=QualityGateConfigOut)
async def get_quality_gate(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get quality gate configuration for AI support."""
    config = await consumo_service.get_or_create_quality_gate_config(db, current_user.id)
    return config


@router.patch("/quality-gate", response_model=QualityGateConfigOut)
async def update_quality_gate(
    data: QualityGateConfigUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update quality gate configuration."""
    config = await consumo_service.update_quality_gate_config(
        db, current_user.id, data.model_dump(exclude_unset=True)
    )
    return config


# ===== PLAN RECOMMENDATION =====

@router.get("/plan-recommendation", response_model=PlanRecommendationOut)
async def get_plan_recommendation(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get AI-powered plan recommendation (upgrade/downgrade/keep)."""
    return await consumo_service.get_plan_recommendation(db, current_user.id)


# ===== ONBOARDING =====

@router.get("/onboarding", response_model=OnboardingProgressOut)
async def get_onboarding_progress(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current onboarding progress with auto-refresh from DB."""
    prog = await consumo_service.refresh_onboarding_progress(db, current_user.id)
    return {
        "account_created": prog.account_created,
        "business_created": prog.business_created,
        "channel_connected": prog.channel_connected,
        "agent_configured": prog.agent_configured,
        "first_conversation": prog.first_conversation,
        "catalog_added": prog.catalog_added,
        "automation_created": prog.automation_created,
        "current_step": prog.current_step,
        "stuck_minutes": prog.stuck_minutes,
        "ai_interventions_count": prog.ai_interventions_count,
        "progress_percent": prog.progress_percent,
    }


@router.post("/onboarding/help", response_model=OnboardingHelpResponse)
async def request_onboarding_help(
    req: OnboardingHelpRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Request AI-guided help for current onboarding step."""
    return await consumo_service.generate_onboarding_help(
        db, current_user.id, req.current_step, req.context
    )


# ===== ADVANCED ANALYTICS =====

@router.get("/heatmap")
async def get_heatmap(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: int = Query(30, ge=7, le=90),
):
    """Get AI usage heatmap by hour and day."""
    return await consumo_service.get_usage_heatmap(db, current_user.id, days)


@router.get("/monthly-comparison")
async def get_monthly_comparison(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Compare current month vs previous month."""
    return await consumo_service.get_monthly_comparison(db, current_user.id)


@router.get("/cost-per-lead")
async def get_cost_per_lead(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: int = Query(30, ge=1, le=90),
):
    """Calculate AI cost per lead/conversation."""
    return await consumo_service.get_cost_per_lead(db, current_user.id, days)


# ===== INTERNAL: CHURN SHIELD (admin only) =====

@router.get("/admin/churn-signals")
async def get_churn_signals(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(50, ge=1, le=200),
):
    """Admin-only: list unresolved churn risk signals."""
    signals = await consumo_service.get_pending_churn_signals(db, limit)
    return [
        {
            "id": s.id,
            "user_id": s.user_id,
            "risk_score": s.risk_score,
            "risk_level": s.risk_level,
            "signals": s.signals,
            "action_taken": s.action_taken,
            "created_at": s.created_at,
        }
        for s in signals
    ]
