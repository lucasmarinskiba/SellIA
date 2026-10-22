"""Business intelligence endpoints, mounted under /api/v1/businesses (the frontend calls /businesses/{id}/bi/*).

Who may do what (see app.core.business_access):

* the funnel (computed on demand) is a dashboard -> the owner or an ADMIN member;
* the insight alerts are read-only and shown to any active member.

No response is cached: a cache key that ignores the caller would hand one business's figures to another user.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_business_access
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.bi.schemas import FunnelMetricsResponse, InsightAlertResponse
from app.domains.bi.services import BiService
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/bi", tags=["Business Intelligence"])


@router.post("/funnel", response_model=FunnelMetricsResponse)
async def generate_funnel(
    business_id: UUID,
    period: str = Query(..., max_length=50),
    period_type: str = Query("monthly", pattern="^(daily|weekly|monthly)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The funnel for the window ending now (nothing is stored)."""
    await require_business_access(db, business_id, current_user, manage=True)
    return await BiService(db).generate_funnel_report(business_id, period, period_type)


@router.get("/funnel/latest", response_model=FunnelMetricsResponse)
async def get_latest_funnel(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """The current monthly funnel."""
    await require_business_access(db, business_id, current_user, manage=True)
    return await BiService(db).get_latest_funnel(business_id)


@router.get("/insights", response_model=list[InsightAlertResponse])
async def list_insights(
    business_id: UUID,
    insight_type: str | None = Query(None, max_length=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Active insight alerts written by the analytics engine."""
    await require_business_access(db, business_id, current_user)
    return await BiService(db).list_insight_alerts(business_id, insight_type)
