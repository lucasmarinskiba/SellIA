"""Marketing attribution API — channel ROI + multi-touch attribution."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.domains.attribution.attribution_models import AttributionModel
from app.domains.attribution.attribution_service import ChannelAttributionService

router = APIRouter(prefix="/api/v1", tags=["marketing-attribution"])


@router.post("/businesses/{business_id}/channel-metrics")
def calculate_channel_metrics(
    business_id: UUID,
    channel: Annotated[str, Query(description="Channel: organic_search, paid_search, social_media, email, etc")],
    date: Annotated[str, Query(description="YYYY-MM-DD")],
    db: Annotated[Session, Depends(get_db)],
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
    business_id: Annotated[UUID, Query()],
    db: Annotated[Session, Depends(get_db)],
    attribution_model: Annotated[str, Query(description="first_touch, last_touch, linear, time_decay")] = AttributionModel.FIRST_TOUCH,
    date_start: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
    date_end: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
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
    db: Annotated[Session, Depends(get_db)],
    date: Annotated[str | None, Query(description="YYYY-MM-DD, default today")] = None,
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
    db: Annotated[Session, Depends(get_db)],
    metric: Annotated[str, Query(description="revenue, visits, roas")] = "revenue",
    days: Annotated[int, Query(ge=1, le=365)] = 30,
):
    """Get top performing channels by metric."""
    return ChannelAttributionService.get_top_performing_channels(
        business_id=business_id,
        metric=metric,
        days=days,
        db=db
    )
