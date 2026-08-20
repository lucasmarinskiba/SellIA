"""Phase 2: ML Pipeline Endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from app.core.database import get_db
from app.domains.ml_pipelines.service import MLPipelineService


router = APIRouter(prefix="/api/v1/ml-pipelines", tags=["ml-pipelines"])


@router.post("/score-lead")
async def score_lead(
    business_id: UUID,
    customer_id: UUID,
    engagement_score: float,
    email_opens: int = 0,
    email_clicks: int = 0,
    phone_calls: int = 0,
    demo_attended: bool = False,
    website_visits: int = 0,
    pages_viewed: int = 0,
    time_on_site_minutes: float = 0,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Calculate lead score using ML model."""
    lead = await MLPipelineService.score_lead(
        db,
        business_id,
        customer_id,
        engagement_score,
        email_opens,
        email_clicks,
        phone_calls,
        demo_attended,
        website_visits,
        pages_viewed,
        time_on_site_minutes,
    )
    return {
        "customer_id": lead.lead_id,
        "lead_score": round(lead.lead_score, 2),
        "confidence": round(lead.confidence, 2),
        "tier": lead.tier,
        "top_factors": lead.top_factors,
    }


@router.post("/predict-churn")
async def predict_churn(
    business_id: UUID,
    customer_id: UUID,
    days_since_last_purchase: int,
    total_lifetime_value: float,
    purchase_frequency_per_month: float,
    support_tickets: int = 0,
    nps_score: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Predict churn probability."""
    churn = await MLPipelineService.predict_churn(
        db,
        business_id,
        customer_id,
        days_since_last_purchase,
        total_lifetime_value,
        purchase_frequency_per_month,
        support_tickets,
        nps_score,
    )
    return {
        "customer_id": churn.customer_id,
        "churn_probability": round(churn.churn_probability, 2),
        "churn_risk": churn.churn_risk,
        "days_until_churn": churn.days_until_churn,
        "recommended_action": churn.recommended_action,
    }


@router.post("/calculate-clv")
async def calculate_clv(
    business_id: UUID,
    customer_id: UUID,
    total_spent: float,
    total_orders: int,
    customer_lifespan_days: int,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Calculate Customer Lifetime Value."""
    clv = await MLPipelineService.calculate_clv(
        db,
        business_id,
        customer_id,
        total_spent,
        total_orders,
        customer_lifespan_days,
    )
    return {
        "customer_id": clv.customer_id,
        "clv_12m": round(clv.predicted_clv_12m, 2),
        "clv_36m": round(clv.predicted_clv_36m, 2),
        "segment": clv.clv_segment,
        "upsell_propensity": round(clv.upsell_propensity, 2),
        "crosssell_propensity": round(clv.crosssell_propensity, 2),
    }
