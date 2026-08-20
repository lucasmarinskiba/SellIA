"""Customer timeline API endpoints."""

from uuid import UUID
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.timeline.timeline_service import TimelineService

router = APIRouter(prefix="/api/v1", tags=["timeline"])


class LogEventRequest(BaseModel):
    event_type: str
    channel: str
    title: str
    event_data: Dict
    description: Optional[str] = None
    outcome: Optional[str] = "success"
    revenue_impact: Optional[str] = None
    estimated_value: Optional[int] = None


class SaveFilterRequest(BaseModel):
    name: str
    event_types: Optional[List[str]] = None
    channels: Optional[List[str]] = None
    outcomes: Optional[List[str]] = None


@router.post("/customers/{customer_id}/events")
def log_event(
    customer_id: UUID,
    business_id: UUID = Query(...),
    request: LogEventRequest = None,
    created_by: Optional[UUID] = None,
    db: Session = Depends(get_db)
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
    business_id: UUID = Query(...),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    event_types: Optional[str] = Query(None),
    channels: Optional[str] = Query(None),
    db: Session = Depends(get_db)
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
    business_id: UUID = Query(...),
    db: Session = Depends(get_db)
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
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get live event stream."""
    return TimelineService.get_event_stream(
        business_id=business_id,
        limit=limit,
        db=db
    )


@router.get("/timeline/search")
def search_events(
    business_id: UUID = Query(...),
    query: str = Query(...),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
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
    is_important: bool = Query(...),
    db: Session = Depends(get_db)
):
    """Mark event as important."""
    return TimelineService.mark_event_important(
        event_id=event_id,
        is_important=is_important,
        db=db
    )


@router.post("/timeline/filters")
def save_event_filter(
    business_id: UUID = Query(...),
    user_id: UUID = Query(...),
    request: SaveFilterRequest = None,
    db: Session = Depends(get_db)
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
    business_id: UUID = Query(...),
    user_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get saved filters."""
    return TimelineService.get_event_filters(
        business_id=business_id,
        user_id=user_id,
        db=db
    )


@router.get("/timeline/metrics")
def get_timeline_metrics(
    business_id: UUID = Query(...),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get timeline metrics."""
    return TimelineService.get_timeline_metrics(
        business_id=business_id,
        days=days,
        db=db
    )
