"""BI dashboards for offline (in-store) activity.

Dashboards aggregate a business's data, so they are for its owner or an ADMIN member (see
app.core.business_access). Every figure is computed from the stored visits by app.domains.bi.offline_metrics;
the old version returned hard-coded numbers and hand-written insights as if they were real.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_business_access, require_location_access
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.bi import offline_metrics
from app.domains.bi.offline_dashboards_schemas import (
    DashboardSummary,
    FootTrafficMetrics,
    OfflineConversionMetrics,
)
from app.domains.users.models import User

router = APIRouter(prefix="", tags=["offline-bi"])


@router.get("/offline/foot-traffic/{location_id}", response_model=FootTrafficMetrics)
async def get_foot_traffic_dashboard(
    location_id: UUID,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FootTrafficMetrics:
    """Foot traffic for one location over the last ``days`` days."""
    location = await require_location_access(db, location_id, current_user, manage=True)
    now = datetime.now(timezone.utc)

    metrics = await db.run_sync(
        lambda sync_db: offline_metrics.location_foot_traffic(sync_db, location_id, days, now)
    )
    return FootTrafficMetrics(
        location_id=location_id,
        location_name=location.name,
        period=f"last_{days}_days",
        **metrics,
    )


@router.get("/offline/conversions/{location_id}", response_model=OfflineConversionMetrics)
async def get_conversion_dashboard(
    location_id: UUID,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OfflineConversionMetrics:
    """Visits, purchases and revenue from visits to one location over the last ``days`` days."""
    location = await require_location_access(db, location_id, current_user, manage=True)
    now = datetime.now(timezone.utc)

    metrics = await db.run_sync(
        lambda sync_db: offline_metrics.location_conversions(sync_db, location_id, days, now)
    )
    return OfflineConversionMetrics(
        location_id=location_id,
        location_name=location.name,
        total_visits=metrics["total_visits"],
        visits_converted=metrics["visits_converted"],
        conversion_rate=metrics["conversion_rate"],
        total_revenue=metrics["total_revenue"],
        avg_order_value=metrics["avg_order_value"],
        avg_transaction_value=metrics["avg_order_value"],
        by_visit_type=metrics["by_visit_type"],
    )


@router.get("/offline/dashboard-summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    business_id: UUID,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DashboardSummary:
    """Business-wide offline summary: this period against the one before it."""
    await require_business_access(db, business_id, current_user, manage=True)
    now = datetime.now(timezone.utc)

    summary = await db.run_sync(
        lambda sync_db: offline_metrics.business_summary(sync_db, business_id, days, now)
    )
    return DashboardSummary(
        business_id=business_id,
        period=f"last_{days}_days",
        actionable_insights=[],
        best_trigger_roi=None,
        **summary,
    )
