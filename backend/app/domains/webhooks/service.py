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


async def trigger_event(db: AsyncSession, user_id: uuid.UUID, event_type: str, payload: dict) -> int:
    """Fan out a real business event to every active subscription this user
    has for it, actually delivering (real signed HTTP POST) and recording
    each attempt. This was the one piece missing from an otherwise-complete
    real webhook system -- everything else here (create/list/update/delete
    subscription, list/retry delivery, HMAC-signed deliver_webhook) already
    existed and was already wired with real auth; nothing called this fan
    -out step from anywhere the app's real events (a lead created, a deal
    won/lost, a payment received) actually happen. Returns how many
    subscriptions were triggered.
    """
    result = await db.execute(
        select(WebhookSubscription).where(WebhookSubscription.user_id == user_id, WebhookSubscription.active == True)
    )
    subscriptions = [s for s in result.scalars().all() if event_type in (s.events or [])]

    for sub in subscriptions:
        success, status_code, body = await deliver_webhook(sub, event_type, payload)
        await record_delivery(db, sub.id, event_type, payload, success, status_code, body)
        sub.updated_at = datetime.now(timezone.utc)
    if subscriptions:
        await db.commit()

    return len(subscriptions)


async def fire_business_event(db: AsyncSession, business_id: uuid.UUID, event_type: str, payload: dict) -> int:
    """Convenience wrapper for the real trigger points (lead/deal/payment
    events) -- they know a business_id, not a user_id (subscriptions are
    owned by users, since one user can own several businesses). Resolves
    the business's owner and delegates to trigger_event. Swallows lookup
    failures (unknown business_id) rather than raising, since a webhook
    firing is never allowed to break the real operation that triggered it
    (creating a deal, recording an outcome, confirming a payment must all
    succeed regardless of whether anyone is subscribed or a delivery
    fails).
    """
    from app.domains.businesses.models import Business
    from sqlalchemy import select as _select

    try:
        result = await db.execute(_select(Business).where(Business.id == business_id))
        business = result.scalar_one_or_none()
        if not business:
            return 0
        return await trigger_event(db, business.user_id, event_type, payload)
    except Exception:
        return 0


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
