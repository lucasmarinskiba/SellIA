from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.crm.models import Deal, LeadStage
from app.domains.enterprise.forecasting import ForecastingManager

router = APIRouter(tags=["forecasting"])
forecasting_engine = ForecastingManager()

# Maps this endpoint's original opportunity "stage" query param vocabulary
# onto the app's real LeadStage enum.
_STAGE_ALIASES = {
    "prospecting": LeadStage.NEW_LEAD,
    "contacted": LeadStage.CONTACTED,
    "qualified": LeadStage.QUALIFIED,
    "proposal": LeadStage.PROPOSAL_SENT,
    "negotiation": LeadStage.NEGOTIATING,
    "won": LeadStage.CLOSED_WON,
    "lost": LeadStage.CLOSED_LOST,
}


async def _get_business_for_user(business_id: UUID, user: User, db: AsyncSession) -> Business:
    result = await db.execute(select(Business).where(Business.id == business_id, Business.user_id == user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


@router.post("/forecast/opportunities/add")
async def add_opportunity(
    business_id: UUID = Query(...),
    title: str = Query(...),
    amount: float = Query(...),
    stage: str = Query("prospecting"),
    contact_name: str = Query(...),
    source: str = Query("direct"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a sales opportunity to the pipeline.

    Creates a real Deal row (app.domains.crm.models.Deal) -- this endpoint
    previously built an in-memory `Opportunity` dataclass that was never
    defined anywhere and stored it in a method (add_opportunity on
    ForecastingManager) that also never existed; every call raised
    ImportError/AttributeError before this fix. Deals are the app's one
    real pipeline-item concept, so this creates one directly rather than
    inventing a second, parallel "Opportunity" entity.
    """
    await _get_business_for_user(business_id, current_user, db)
    stage_enum = _STAGE_ALIASES.get(stage)
    if stage_enum is None:
        return {"status": "error", "message": f"Invalid stage: {stage}"}

    deal = Deal(
        business_id=business_id,
        title=title,
        value=amount,
        stage=stage_enum,
        contact_name=contact_name,
        description=f"Source: {source}" if source else None,
    )
    db.add(deal)
    await db.commit()
    await db.refresh(deal)

    return {
        "status": "added",
        "opportunity_id": str(deal.id),
        "title": title,
        "amount": amount,
        "stage": stage,
    }


@router.get("/forecast/pipeline/{business_id}")
async def get_pipeline_forecast(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get pipeline snapshot with weighted forecast."""
    await _get_business_for_user(business_id, current_user, db)
    pipeline = await forecasting_engine.get_pipeline_forecast(business_id, db)

    return {
        "timestamp": pipeline["timestamp"].isoformat(),
        "total_opportunities": pipeline["total_opportunities"],
        "total_pipeline_value": f"${pipeline['total_pipeline_value']:,.2f}",
        "weighted_forecast": f"${pipeline['weighted_forecast']:,.2f}",
        "average_deal_size": f"${pipeline['average_deal_size']:,.2f}",
        "average_days_in_pipeline": round(pipeline["average_days_in_pipeline"], 1),
        "by_stage": {
            stage: {
                "count": data["count"],
                "value": f"${data['value']:,.2f}",
                "weighted_value": f"${data['weighted_value']:,.2f}",
                "avg_probability": f"{data['avg_probability']:.1f}%",
            }
            for stage, data in pipeline["by_stage"].items()
        },
    }


@router.get("/forecast/revenue/{business_id}")
async def project_revenue(
    business_id: UUID,
    days_ahead: int = Query(30, ge=1, le=365),
    target_revenue: float = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Project revenue for period ahead."""
    await _get_business_for_user(business_id, current_user, db)
    projection = await forecasting_engine.project_revenue(business_id, db, days_ahead, target_revenue)

    return {
        "period": projection["period"],
        "projected_revenue": f"${projection['projected_revenue']:,.2f}",
        "confidence": f"{projection['confidence']:.1f}%",
        "scenarios": {
            "best_case": f"${projection['best_case']:,.2f}",
            "most_likely": f"${projection['most_likely']:,.2f}",
            "worst_case": f"${projection['worst_case']:,.2f}",
        },
        "probability_of_target": (
            f"{projection['probability_of_target']:.1f}%" if projection["probability_of_target"] is not None else "N/A"
        ),
        "key_drivers": {
            "avg_deal_size": f"${projection['key_drivers']['avg_deal_size']:,.2f}",
            "pipeline_velocity": f"${projection['key_drivers']['pipeline_velocity']:,.2f}/day",
        },
    }


@router.get("/forecast/scenarios/{business_id}")
async def get_forecast_scenarios(
    business_id: UUID,
    days_ahead: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get best/base/worst case scenarios."""
    await _get_business_for_user(business_id, current_user, db)
    scenarios = await forecasting_engine.generate_scenarios(business_id, db, days_ahead)

    return {
        "period": f"{days_ahead}d",
        "scenarios": [
            {
                "name": s["name"],
                "projected_revenue": f"${s['projected_revenue']:,.2f}",
                "probability": f"{s['probability']}%",
                "assumptions": s["assumptions"],
            }
            for s in scenarios
        ],
    }


@router.get("/forecast/funnel/{business_id}")
async def get_conversion_funnel(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get conversion funnel analysis."""
    await _get_business_for_user(business_id, current_user, db)
    funnel = await forecasting_engine.get_conversion_funnel(business_id, db)

    return {
        "business_id": str(business_id),
        "funnel": {
            stage: {
                "count": data["count"],
                "percentage": f"{data['percentage']:.1f}%",
                "value": f"${data['value']:,.2f}",
                "cumulative_value": f"${data['cumulative_value']:,.2f}",
            }
            for stage, data in funnel.items()
        },
    }


@router.get("/forecast/risks/{business_id}")
async def identify_risks(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Identify at-risk and stalled opportunities."""
    await _get_business_for_user(business_id, current_user, db)
    risks = await forecasting_engine.identify_risk_opportunities(business_id, db)

    return {
        "business_id": str(business_id),
        "summary": {
            "at_risk_count": risks["at_risk_count"],
            "stalled_count": risks["stalled_count"],
            "risk_value": f"${risks['risk_value']:,.2f}",
        },
        "at_risk_opportunities": risks["at_risk"],
        "stalled_opportunities": risks["stalled"],
    }
