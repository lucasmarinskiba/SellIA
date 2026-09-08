from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.crm.models import Deal
from app.domains.enterprise.forecasting import ForecastingManager, DealOutcomeAnalyzer

router = APIRouter()

forecasting = ForecastingManager()
outcome_analyzer = DealOutcomeAnalyzer()


async def _get_business_for_user(business_id: UUID, user: User, db: AsyncSession) -> Business:
    result = await db.execute(select(Business).where(Business.id == business_id, Business.user_id == user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


async def _get_owned_deal(deal_id: UUID, user: User, db: AsyncSession) -> Deal:
    result = await db.execute(select(Deal).where(Deal.id == deal_id))
    deal = result.scalar_one_or_none()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal no encontrado")
    await _get_business_for_user(deal.business_id, user, db)
    return deal


@router.post("/intelligence/analyze-deals/{business_id}")
async def analyze_deals(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze all open deals for win probability and risk assessment."""
    await _get_business_for_user(business_id, current_user, db)
    result = await forecasting.analyze_deals(business_id, db)
    return {"status": "ok", "business_id": str(business_id), "analysis": result}


@router.get("/intelligence/deal-score/{deal_id}")
async def get_deal_score(
    deal_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get current deal score and risk assessment."""
    deal = await _get_owned_deal(deal_id, current_user, db)
    score = await forecasting.get_deal_score(deal.business_id, deal_id, db)
    if not score:
        return {"status": "not_found", "deal_id": str(deal_id)}
    return {"status": "ok", "deal_id": str(deal_id), "score": score}


@router.post("/intelligence/forecast-revenue/{business_id}")
async def forecast_revenue(
    business_id: UUID,
    periods: list[int] = Query([30, 60, 90]),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate revenue forecast for multiple periods."""
    await _get_business_for_user(business_id, current_user, db)
    forecast = await forecasting.forecast_revenue(business_id, db, periods)
    return {"status": "ok", "business_id": str(business_id), "forecast": forecast}


@router.get("/intelligence/at-risk-deals/{business_id}")
async def get_at_risk_deals(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get summary of all at-risk deals for this business."""
    await _get_business_for_user(business_id, current_user, db)
    summary = await forecasting.get_at_risk_summary(business_id, db)
    return {"status": "ok", "at_risk_summary": summary}


@router.post("/intelligence/record-outcome/{deal_id}")
async def record_deal_outcome(
    deal_id: UUID,
    outcome: str,
    final_value: float = None,
    days_to_close: int = 0,
    forecasted_probability: float = 0.5,
    win_loss_reason: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record deal outcome (won/lost) for forecast-accuracy tracking."""
    deal = await _get_owned_deal(deal_id, current_user, db)
    result = await outcome_analyzer.record_outcome(
        db, deal_id, deal.business_id, outcome, final_value, days_to_close, forecasted_probability, win_loss_reason,
    )
    return {"status": "ok", "outcome": result}


@router.get("/intelligence/accuracy-metrics/{business_id}")
async def get_accuracy_metrics(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get forecast accuracy metrics for this business."""
    await _get_business_for_user(business_id, current_user, db)
    metrics = await outcome_analyzer.get_accuracy_metrics(business_id, db)
    return {"status": "ok", "business_id": str(business_id), "metrics": metrics}


@router.get("/intelligence/win-loss-summary/{business_id}")
async def get_win_loss_summary(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get win/loss analysis and patterns."""
    await _get_business_for_user(business_id, current_user, db)
    summary = await outcome_analyzer.get_win_loss_summary(business_id, db)
    return {"status": "ok", "business_id": str(business_id), "summary": summary}


@router.get("/intelligence/dashboard/{business_id}")
async def get_intelligence_dashboard(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Comprehensive deal intelligence dashboard."""
    await _get_business_for_user(business_id, current_user, db)
    at_risk = await forecasting.get_at_risk_summary(business_id, db)
    accuracy = await outcome_analyzer.get_accuracy_metrics(business_id, db)
    win_loss = await outcome_analyzer.get_win_loss_summary(business_id, db)
    analysis = await forecasting.analyze_deals(business_id, db)

    return {
        "status": "ok",
        "business_id": str(business_id),
        "dashboard": {
            "at_risk": at_risk,
            "accuracy": accuracy,
            "win_loss_patterns": win_loss,
            "total_deals_analyzed": analysis["total_deals"],
        },
    }
