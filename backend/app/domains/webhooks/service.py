"""
Webhook Service
"""

import uuid
import hmac
import hashlib
import json
from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.webhooks.models import WebhookSubscription, WebhookDelivery

import httpx


async def create_subscription(
    db: AsyncSession,
    user_id: uuid.UUID,
    url: str,
    events: list,
    secret: str,
    active: bool = True,
) -> WebhookSubscription:
    sub = WebhookSubscription(
        user_id=user_id,
        url=url,
        events=events,
        secret=secret,
        active=active,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub


async def list_subscriptions(db: AsyncSession, user_id: uuid.UUID) -> List[WebhookSubscription]:
    result = await db.execute(
        select(WebhookSubscription).where(WebhookSubscription.user_id == user_id)
    )
    return result.scalars().all()


async def get_subscription(
    db: AsyncSession, subscription_id: uuid.UUID, user_id: uuid.UUID
) -> Optional[WebhookSubscription]:
    result = await db.execute(
        select(WebhookSubscription).where(
            WebhookSubscription.id == subscription_id,
            WebhookSubscription.user_id == user_id,
        )
    )
    return result.scalar_one_or_none()


async def update_subscription(
    db: AsyncSession, subscription_id: uuid.UUID, user_id: uuid.UUID, **kwargs
) -> Optional[WebhookSubscription]:
    sub = await get_subscription(db, subscription_id, user_id)
    if not sub:
        return None
    for key, value in kwargs.items():
        if value is not None:
            setattr(sub, key, value)
    sub.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(sub)
    return sub


async def delete_subscription(
    db: AsyncSession, subscription_id: uuid.UUID, user_id: uuid.UUID
) -> bool:
    sub = await get_subscription(db, subscription_id, user_id)
    if not sub:
        return False
    await db.delete(sub)
    await db.commit()
    return True


async def list_deliveries(
    db: AsyncSession, subscription_id: uuid.UUID, user_id: uuid.UUID
) -> List[WebhookDelivery]:
    sub = await get_subscription(db, subscription_id, user_id)
    if not sub:
        return []
    result = await db.execute(
        select(WebhookDelivery)
        .where(WebhookDelivery.subscription_id == subscription_id)
        .order_by(WebhookDelivery.delivered_at.desc())
    )
    return result.scalars().all()


async def get_delivery(db: AsyncSession, delivery_id: uuid.UUID) -> Optional[WebhookDelivery]:
    result = await db.execute(
        select(WebhookDelivery).where(WebhookDelivery.id == delivery_id)
    )
    return result.scalar_one_or_none()


async def deliver_webhook(
    subscription: WebhookSubscription, event_type: str, payload: dict
) -> tuple[bool, Optional[int], Optional[str]]:
    body = json.dumps(payload, default=str)
    signature = hmac.new(
        subscription.secret.encode(), body.encode(), hashlib.sha256
    ).hexdigest()

    headers = {
        "Content-Type": "application/json",
        "X-Webhook-Signature": signature,
        "X-Webhook-Event": event_type,
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                subscription.url, content=body, headers=headers, timeout=30.0
            )
            success = 200 <= response.status_code < 300
            return success, response.status_code, response.text
        except Exception as e:
            return False, None, str(e)


async def record_delivery(
    db: AsyncSession,
    subscription_id: uuid.UUID,
    event_type: str,
    payload: dict,
    success: bool,
    response_status: Optional[int],
    response_body: Optional[str],
) -> WebhookDelivery:
    delivery = WebhookDelivery(
        subscription_id=subscription_id,
        event_type=event_type,
        payload=payload,
        success=success,
        response_status=response_status,
        response_body=response_body,
    )
    db.add(delivery)
    await db.commit()
    await db.refresh(delivery)
    return delivery


async def retry_delivery(db: AsyncSession, delivery: WebhookDelivery) -> WebhookDelivery:
    result = await db.execute(
        select(WebhookSubscription).where(
            WebhookSubscription.id == delivery.subscription_id
        )
    )
    subscription = result.scalar_one_or_none()

    if not subscription or not subscription.active:
        delivery.success = False
        delivery.retry_count += 1
        await db.commit()
        await db.refresh(delivery)
        return delivery

    success, response_status, response_body = await deliver_webhook(
        subscription, delivery.event_type, delivery.payload
    )

    delivery.success = success
    delivery.response_status = response_status
    delivery.response_body = response_body
    delivery.retry_count += 1
    delivery.delivered_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(delivery)
    return delivery
