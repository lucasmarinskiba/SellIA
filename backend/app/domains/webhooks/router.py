"""
Webhook Router
"""

import uuid
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User

from app.domains.webhooks import service as webhook_service
from app.domains.webhooks.schemas import (
    WebhookSubscriptionCreate,
    WebhookSubscriptionUpdate,
    WebhookSubscriptionResponse,
    WebhookDeliveryResponse,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ========== Subscriptions ==========

@router.post("/subscriptions", response_model=WebhookSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    data: WebhookSubscriptionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new webhook subscription."""
    sub = await webhook_service.create_subscription(
        db,
        user_id=current_user.id,
        url=data.url,
        events=data.events,
        secret=data.secret,
        active=data.active,
    )
    return sub


@router.get("/subscriptions", response_model=List[WebhookSubscriptionResponse])
async def list_subscriptions(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List current user's webhook subscriptions."""
    return await webhook_service.list_subscriptions(db, current_user.id)


@router.get("/subscriptions/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def get_subscription(
    subscription_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get a specific webhook subscription."""
    sub = await webhook_service.get_subscription(db, subscription_id, current_user.id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return sub


@router.patch("/subscriptions/{subscription_id}", response_model=WebhookSubscriptionResponse)
async def update_subscription(
    subscription_id: uuid.UUID,
    data: WebhookSubscriptionUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update a webhook subscription."""
    updates = data.model_dump(exclude_unset=True)
    sub = await webhook_service.update_subscription(db, subscription_id, current_user.id, **updates)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return sub


@router.delete("/subscriptions/{subscription_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subscription(
    subscription_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete a webhook subscription."""
    deleted = await webhook_service.delete_subscription(db, subscription_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found")
    return None


# ========== Deliveries ==========

@router.get("/deliveries/{subscription_id}", response_model=List[WebhookDeliveryResponse])
async def list_deliveries(
    subscription_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List webhook deliveries for a subscription."""
    deliveries = await webhook_service.list_deliveries(db, subscription_id, current_user.id)
    return deliveries


@router.post("/deliveries/{delivery_id}/retry", response_model=WebhookDeliveryResponse)
async def retry_delivery(
    delivery_id: uuid.UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Manually retry a failed webhook delivery."""
    delivery = await webhook_service.get_delivery(db, delivery_id)
    if not delivery:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Delivery not found")

    # Verify ownership through subscription
    sub = await webhook_service.get_subscription(db, delivery.subscription_id, current_user.id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    delivery = await webhook_service.retry_delivery(db, delivery)
    return delivery
