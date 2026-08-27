"""Orchestrator API — /api/v1/businesses/{business_id}/orchestrator/*"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.orchestrator.service import OrchestratorService
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/orchestrator", tags=["Orchestrator"])


@router.get("/analyze")
async def analyze(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze current business state across all domains → recommendations."""
    try:
        svc = OrchestratorService(db)
        plan = await svc.analyze(business_id)
        return {
            "business_id": plan.business_id,
            "priority": plan.priority.value,
            "metrics": {
                "cash_balance": float(plan.metrics.cash_balance),
                "runway_days": plan.metrics.runway_days,
                "forecast_revenue_30d": float(plan.metrics.forecast_revenue_30d),
                "forecast_confidence": float(plan.metrics.forecast_confidence),
                "monthly_opex": float(plan.metrics.current_monthly_opex),
                "gross_margin": float(plan.metrics.current_gross_margin),
                "highest_roas_channel": plan.metrics.highest_roas_channel,
                "lowest_roas_channel": plan.metrics.lowest_roas_channel,
                "daily_ad_spend": float(plan.metrics.ad_spend_daily),
            },
            "recommendations": [
                {
                    "action": r.action.value,
                    "rationale": r.rationale,
                    "target_value": float(r.target_value) if r.target_value else None,
                    "confidence": float(r.confidence),
                    "impact_cash_30d": float(r.impact_cash_30d) if r.impact_cash_30d else None,
                    "impact_revenue_30d": float(r.impact_revenue_30d) if r.impact_revenue_30d else None,
                }
                for r in plan.recommendations
            ],
            "reasoning": plan.reasoning,
        }
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scenarios")
async def scenarios(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate what-if scenarios based on current state."""
    try:
        svc = OrchestratorService(db)
        plan = await svc.analyze(business_id)
        scenario_list = await svc.scenarios(business_id, plan)
        return {
            "scenarios": [
                {
                    "name": s.name,
                    "description": s.description,
                    "projected_cash_30d": float(s.projected_cash_30d),
                    "projected_revenue_30d": float(s.projected_revenue_30d),
                    "projected_runway_days": s.projected_runway_days,
                    "feasibility": s.feasibility,
                    "risks": s.risks,
                }
                for s in scenario_list
            ]
        }
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=str(e))
