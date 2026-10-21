"""Analytics & BI API Router."""

from datetime import UTC
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.analytics.adapters import DashboardKPIAdapter
from app.domains.analytics.models import (
    ChurnPrediction,
    FunnelMetric,
    InsightAlert,
    LtvPrediction,
)
from app.domains.analytics.schemas import (
    ChurnPredictionResponse,
    DashboardSummaryResponse,
    FunnelMetricResponse,
    InsightAlertResponse,
    LtvPredictionResponse,
)
from app.domains.analytics.services import BusinessIntelligenceService
from app.domains.business_context.models import BusinessContext
from app.domains.retention.services import RetentionService
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/analytics", tags=["Analytics & BI"])


@router.post("/funnel/{period}")
async def calculate_funnel(
    business_id: UUID,
    period: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    service = BusinessIntelligenceService(db)
    metric = await service.calculate_funnel(business_id, period)
    return {"funnel": metric}


@router.get("/funnel", response_model=list[FunnelMetricResponse])
async def list_funnel_metrics(
    business_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(FunnelMetric).where(FunnelMetric.business_id == business_id).order_by(FunnelMetric.period.desc()).limit(12))
    return result.scalars().all()


@router.post("/churn-predict/{conversation_id}", response_model=ChurnPredictionResponse)
async def predict_churn(
    business_id: UUID,
    conversation_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    service = BusinessIntelligenceService(db)
    prediction = await service.predict_churn(business_id, conversation_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Conversation not found or insufficient data")
    return prediction


@router.post("/ltv-predict/{conversation_id}", response_model=LtvPredictionResponse)
async def predict_ltv(
    business_id: UUID,
    conversation_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    service = BusinessIntelligenceService(db)
    prediction = await service.predict_ltv(business_id, conversation_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Conversation not found or insufficient data")
    return prediction


@router.get("/insights", response_model=list[InsightAlertResponse])
async def list_insights(
    business_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(select(InsightAlert).where(InsightAlert.business_id == business_id, InsightAlert.is_active == True).order_by(InsightAlert.created_at.desc()).limit(50))
    return result.scalars().all()


@router.get("/dashboard", response_model=DashboardSummaryResponse)
async def get_dashboard(
    business_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    BusinessIntelligenceService(db)
    retention = RetentionService(db)

    # Revenue
    from sqlalchemy import func

    from app.domains.orders.models import Order
    rev_result = await db.execute(select(func.sum(Order.total_amount), func.count(Order.id)).where(Order.business_id == business_id, Order.is_active == True))
    rev_row = rev_result.first()
    revenue = float(rev_row[0] or 0)
    orders = rev_row[1] or 0

    # Leads
    from app.domains.channels.models import Conversation
    leads_result = await db.execute(select(func.count(Conversation.id)).where(Conversation.business_id == business_id, Conversation.is_active == True))
    leads = leads_result.scalar() or 0

    # NPS
    nps = await retention.get_nps_score(business_id)

    # Segments
    segments = await retention.get_segment_counts(business_id)
    top_segment = max(segments, key=segments.get) if segments else "unknown"

    # Churn risk
    churn_result = await db.execute(select(func.count(ChurnPrediction.id)).where(ChurnPrediction.business_id == business_id, ChurnPrediction.risk_level.in_(["high", "critical"])))
    at_risk = churn_result.scalar() or 0

    # Insights today
    from datetime import datetime, timedelta
    today = datetime.now(UTC) - timedelta(hours=24)
    insights_result = await db.execute(select(func.count(InsightAlert.id)).where(InsightAlert.business_id == business_id, InsightAlert.created_at >= today))
    insights_today = insights_result.scalar() or 0

    # Avg LTV
    ltv_result = await db.execute(select(func.avg(LtvPrediction.predicted_ltv)).where(LtvPrediction.business_id == business_id))
    avg_ltv = float(ltv_result.scalar() or 0)

    conversion = (orders / leads * 100) if leads else 0

    # Business-type-aware KPIs
    bc_result = await db.execute(select(BusinessContext).where(BusinessContext.business_id == business_id))
    bc = bc_result.scalar_one_or_none()
    kpis = DashboardKPIAdapter.get_kpis(bc.business_type if bc else None)

    return DashboardSummaryResponse(
        business_id=business_id,
        period="current",
        revenue_total=revenue,
        orders_count=orders,
        leads_count=leads,
        conversion_rate=round(conversion, 2),
        nps_score=nps["nps"],
        at_risk_customers=at_risk,
        avg_ltv=round(avg_ltv, 2),
        top_segment=top_segment,
        insights_today=insights_today,
        kpis=kpis,
    )
