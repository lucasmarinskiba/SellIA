"""Phase 5D: Offline Analytics & Re-engagement Endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional
from datetime import datetime
from app.core.database import get_db
from app.domains.offline_analytics.service import OfflineAnalyticsService


router = APIRouter(prefix="/api/v1/offline-analytics", tags=["offline-analytics"])


@router.post("/create-attribution")
async def create_attribution(
    business_id: UUID,
    user_id: UUID,
    first_online_channel: Optional[str] = None,
    first_online_date: Optional[datetime] = None,
    location_visited_id: Optional[UUID] = None,
    location_visit_date: Optional[datetime] = None,
    post_visit_order_date: Optional[datetime] = None,
    post_visit_order_value: float = 0,
    conversion_type: str = "online_to_offline",
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create online-offline attribution record."""
    attribution = OfflineAnalyticsService.create_attribution(
        db=db,
        business_id=business_id,
        user_id=user_id,
        first_online_channel=first_online_channel,
        first_online_date=first_online_date,
        location_visited_id=location_visited_id,
        location_visit_date=location_visit_date,
        post_visit_order_date=post_visit_order_date,
        post_visit_order_value=post_visit_order_value,
        conversion_type=conversion_type,
    )
    return {
        "id": attribution.id,
        "conversion_type": attribution.conversion_type,
        "time_to_conversion_days": attribution.time_to_conversion_days,
        "message": "Attribution created",
    }


@router.get("/metrics")
async def get_offline_metrics(business_id: UUID, db: AsyncSession = Depends(get_db)) -> dict:
    """Get offline analytics metrics."""
    metrics = OfflineAnalyticsService.calculate_offline_metrics(db, business_id)
    return {
        "business_id": business_id,
        "total_foot_traffic": metrics.total_foot_traffic,
        "unique_visitors": metrics.unique_visitors,
        "total_conversions_offline": metrics.total_conversions_offline,
        "conversion_rate_offline": round(metrics.conversion_rate_offline, 2),
        "avg_dwell_time_minutes": round(metrics.avg_dwell_time_minutes, 2),
        "total_revenue_from_visits": metrics.total_revenue_from_visits,
        "online_to_offline_conversions": metrics.online_to_offline_conversions,
        "offline_to_online_conversions": metrics.offline_to_online_conversions,
        "full_loop_conversions": metrics.full_loop_conversions,
        "peak_traffic_hour": metrics.peak_traffic_hour,
        "repeat_visitor_rate": round(metrics.repeat_visitor_rate, 2),
    }


@router.get("/attribution-report")
async def get_attribution_report(
    business_id: UUID,
    days: int = 30,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get online-to-offline-to-online attribution report."""
    report = OfflineAnalyticsService.get_attribution_report(db, business_id, days)
    return report


@router.post("/post-visit-sequence/create")
async def create_post_visit_sequence(
    business_id: UUID,
    sequence_name: str,
    trigger_type: str,
    location_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create post-visit re-engagement sequence."""
    seq = OfflineAnalyticsService.create_post_visit_sequence(
        db=db,
        business_id=business_id,
        sequence_name=sequence_name,
        trigger_type=trigger_type,
        location_id=location_id,
    )
    return {
        "id": seq.id,
        "sequence_name": seq.sequence_name,
        "trigger_type": seq.trigger_type,
        "message": "Sequence created",
    }


@router.post("/post-visit-sequence/execute")
async def execute_post_visit_sequence(
    business_id: UUID,
    sequence_id: UUID,
    user_id: UUID,
    offline_conversion_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Execute post-visit sequence for user."""
    execution = OfflineAnalyticsService.execute_post_visit_sequence(
        db=db,
        business_id=business_id,
        sequence_id=sequence_id,
        user_id=user_id,
        offline_conversion_id=offline_conversion_id,
    )
    return {
        "id": execution.id,
        "user_id": execution.user_id,
        "status": execution.status,
        "started_at": execution.started_at,
        "message": "Sequence execution started",
    }
