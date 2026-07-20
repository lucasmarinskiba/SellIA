"""BI API Router."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.cache import cached
from app.domains.users.models import User
from app.domains.bi.schemas import FunnelMetricsResponse, InsightAlertResponse
from app.domains.bi.services import BiService

router = APIRouter(prefix="/{business_id}/bi", tags=["Business Intelligence"])


@router.post("/funnel", response_model=FunnelMetricsResponse, status_code=status.HTTP_201_CREATED)
async def generate_funnel(
    business_id: UUID,
    period: str,
    period_type: str = "monthly",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BiService(db)
    return await service.generate_funnel_report(business_id, period, period_type)


@cached(ttl_seconds=300, key_prefix="bi")
@router.get("/funnel/latest", response_model=FunnelMetricsResponse | None)
async def get_latest_funnel(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BiService(db)
    return await service.get_latest_funnel(business_id)


@cached(ttl_seconds=300, key_prefix="bi")
@router.get("/insights", response_model=list[InsightAlertResponse])
async def list_insights(
    business_id: UUID,
    insight_type: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = BiService(db)
    return await service.list_insight_alerts(business_id, insight_type)
