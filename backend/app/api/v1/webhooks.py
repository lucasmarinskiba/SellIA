"""Webhook API — event delivery & streaming."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.domains.webhooks.webhook_service import WebhookService

router = APIRouter(prefix="/api/v1", tags=["webhooks"])


class RegisterWebhookRequest(BaseModel):
    url: str
    subscribed_events: list[str]
    description: str | None = None


class TriggerEventRequest(BaseModel):
    event_type: str
    event_data: dict


@router.post("/businesses/{business_id}/webhooks")
def register_webhook(
    business_id: UUID,
    request: RegisterWebhookRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Register webhook endpoint."""
    return WebhookService.register_webhook(
        business_id=business_id,
        url=request.url,
        subscribed_events=request.subscribed_events,
        description=request.description,
        db=db,
    )


@router.post("/businesses/{business_id}/webhooks/trigger")
def trigger_event(
    business_id: UUID,
    request: TriggerEventRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Trigger webhook event."""
    return WebhookService.trigger_event(
        business_id=business_id,
        event_type=request.event_type,
        event_data=request.event_data,
        db=db,
    )


@router.post("/businesses/{business_id}/events/queue")
def queue_event(
    business_id: UUID,
    request: TriggerEventRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """Queue event for async processing."""
    return WebhookService.queue_event(
        business_id=business_id,
        event_type=request.event_type,
        event_data=request.event_data,
        db=db,
    )


@router.get("/businesses/{business_id}/webhooks/stats")
def get_webhook_stats(
    business_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
):
    """Get webhook delivery statistics."""
    return WebhookService.get_webhook_stats(business_id=business_id, days=days, db=db)
