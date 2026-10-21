"""Customer timeline API endpoints."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.timeline.timeline_service import TimelineService

router = APIRouter(prefix="/api/v1", tags=["timeline"])


class LogEventRequest(BaseModel):
    event_type: str
    channel: str
    title: str
    event_data: dict
    description: str | None = None
    outcome: str | None = "success"
    revenue_impact: str | None = None
    estimated_value: int | None = None


class SaveFilterRequest(BaseModel):
    name: str
    event_types: list[str] | None = None
    channels: list[str] | None = None
    outcomes: list[str] | None = None


@router.post("/customers/{customer_id}/events")
def log_event(
    customer_id: UUID,
    business_id: Annotated[UUID, Query()],
    db: Annotated[Session, Depends(get_db)],
    request: LogEventRequest = None,
    created_by: UUID | None = None,
):
    """Log customer event."""
    return TimelineService.log_event(
        business_id=business_id,
        customer_id=customer_id,
        event_type=request.event_type,
        channel=request.channel,
        title=request.title,
        event_data=request.event_data,
        description=request.description,
        outcome=request.outcome,
        revenue_impact=request.revenue_impact,
        estimated_value=request.estimated_value,
        created_by=created_by,
        db=db
    )


@router.get("/customers/{customer_id}/timeline")
def get_customer_timeline(
    customer_id: UUID,
    business_id: Annotated[UUID, Query()],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
    event_types: Annotated[str | None, Query()] = None,
    channels: Annotated[str | None, Query()] = None,
):
    """Get customer timeline."""
    event_types_list = event_types.split(",") if event_types else None
    channels_list = channels.split(",") if channels else None

    return TimelineService.get_customer_timeline(
        customer_id=customer_id,
        business_id=business_id,
        limit=limit,
        offset=offset,
        event_types=event_types_list,
        channels=channels_list,
        db=db
    )


@router.get("/customers/{customer_id}/timeline/summary")
def get_timeline_summary(
    customer_id: UUID,
    business_id: Annotated[UUID, Query()],
    db: Annotated[Session, Depends(get_db)],
):
    """Get timeline summary."""
    return TimelineService.get_timeline_summary(
        customer_id=customer_id,
        business_id=business_id,
        db=db
    )


@router.get("/businesses/{business_id}/timeline/stream")
def get_event_stream(
    business_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    """Get live event stream."""
    return TimelineService.get_event_stream(
        business_id=business_id,
        limit=limit,
        db=db
    )


@router.get("/timeline/search")
def search_events(
    business_id: Annotated[UUID, Query()],
    query: Annotated[str, Query()],
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
):
    """Search events."""
    return TimelineService.search_events(
        business_id=business_id,
        query_text=query,
        limit=limit,
        db=db
    )


@router.post("/events/{event_id}/important")
def mark_event_important(
    event_id: UUID,
    is_important: Annotated[bool, Query()],
    db: Annotated[Session, Depends(get_db)],
):
    """Mark event as important."""
    return TimelineService.mark_event_important(
        event_id=event_id,
        is_important=is_important,
        db=db
    )


@router.post("/timeline/filters")
def save_event_filter(
    business_id: Annotated[UUID, Query()],
    user_id: Annotated[UUID, Query()],
    db: Annotated[Session, Depends(get_db)],
    request: SaveFilterRequest = None,
):
    """Save timeline filter."""
    return TimelineService.save_event_filter(
        business_id=business_id,
        user_id=user_id,
        name=request.name,
        event_types=request.event_types,
        channels=request.channels,
        outcomes=request.outcomes,
        db=db
    )


@router.get("/timeline/filters")
def get_event_filters(
    business_id: Annotated[UUID, Query()],
    user_id: Annotated[UUID, Query()],
    db: Annotated[Session, Depends(get_db)],
):
    """Get saved filters."""
    return TimelineService.get_event_filters(
        business_id=business_id,
        user_id=user_id,
        db=db
    )


@router.get("/timeline/metrics")
def get_timeline_metrics(
    business_id: Annotated[UUID, Query()],
    db: Annotated[Session, Depends(get_db)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
):
    """Get timeline metrics."""
    return TimelineService.get_timeline_metrics(
        business_id=business_id,
        days=days,
        db=db
    )
