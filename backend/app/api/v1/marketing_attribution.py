"""Marketing attribution API — channel ROI + multi-touch attribution."""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.domains.attribution.attribution_service import ChannelAttributionService
from app.domains.attribution.attribution_models import AttributionModel

router = APIRouter(prefix="/api/v1", tags=["marketing-attribution"])


@router.post("/businesses/{business_id}/channel-metrics")
def calculate_channel_metrics(
    business_id: UUID,
    channel: str = Query(..., description="Channel: organic_search, paid_search, social_media, email, etc"),
    date: str = Query(..., description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Calculate attribution metrics for channel on given date."""
    return ChannelAttributionService.calculate_channel_metrics(
        business_id=business_id,
        channel=channel,
        date=date,
        db=db
    )


@router.post("/locations/{location_id}/channel-attribution")
def attribute_visits_to_channel(
    location_id: UUID,
    business_id: UUID = Query(...),
    attribution_model: str = Query(AttributionModel.FIRST_TOUCH, description="first_touch, last_touch, linear, time_decay"),
    date_start: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_end: Optional[str] = Query(None, description="YYYY-MM-DD"),
    db: Session = Depends(get_db)
):
    """Attribute location visits to channels."""
    model = AttributionModel[attribution_model.upper()]
    return ChannelAttributionService.attribute_visits_to_channel(
        business_id=business_id,
        location_id=location_id,
        attribution_model=model,
        date_start=date_start,
        date_end=date_end,
        db=db
    )


@router.get("/businesses/{business_id}/channel-roi-report")
def get_channel_roi_report(
    business_id: UUID,
    date: Optional[str] = Query(None, description="YYYY-MM-DD, default today"),
    db: Session = Depends(get_db)
):
    """Generate ROI ranking by channel."""
    return ChannelAttributionService.generate_channel_roi_report(
        business_id=business_id,
        date=date,
        db=db
    )


@router.get("/businesses/{business_id}/top-channels")
def get_top_channels(
    business_id: UUID,
    metric: str = Query("revenue", description="revenue, visits, roas"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get top performing channels by metric."""
    return ChannelAttributionService.get_top_performing_channels(
        business_id=business_id,
        metric=metric,
        days=days,
        db=db
    )
