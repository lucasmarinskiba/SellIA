"""Stripe webhook handler · provision/cancel/dunning."""
import logging
import uuid

import stripe
from fastapi import APIRouter, Header, HTTPException, Request
from sqlalchemy import select

from app.core.config import settings
from app.db.models import Tenant
from app.db.session import get_session


logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("")
async def stripe_webhook(
    request: Request,
    stripe_signature: str | None = Header(None, alias="stripe-signature"),
):
    """
    Handle Stripe events:
      - checkout.session.completed → upgrade tenant.plan
      - customer.subscription.updated → sync plan
      - customer.subscription.deleted → downgrade to trial
      - invoice.payment_failed → dunning email
    """
    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=503, detail="Webhook not configured")

    body = await request.body()

    try:
        event = stripe.Webhook.construct_event(
            payload=body,
            sig_header=stripe_signature,
            secret=settings.STRIPE_WEBHOOK_SECRET,
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")

    event_type = event["type"]
    data = event["data"]["object"]

    logger.info("stripe_event_received", extra={"event_type": event_type})

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(data)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(data)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(data)
    elif event_type == "invoice.payment_failed":
        await _handle_payment_failed(data)
    else:
        logger.debug("stripe_event_unhandled", extra={"event_type": event_type})

    return {"received": True}


async def _handle_checkout_completed(data: dict) -> None:
    tenant_id = data.get("client_reference_id") or data.get("metadata", {}).get("tenant_id")
    plan = data.get("metadata", {}).get("plan", "starter")
    customer_id = data.get("customer")
    subscription_id = data.get("subscription")

    if not tenant_id:
        logger.warning("checkout_completed_no_tenant", extra={"data": data})
        return

    async with get_session() as db:
        result = await db.execute(select(Tenant).where(Tenant.id == uuid.UUID(tenant_id)))
        tenant = result.scalar_one_or_none()
        if not tenant:
            logger.error("tenant_not_found", extra={"tenant_id": tenant_id})
            return
        tenant.plan = plan
        tenant.stripe_customer_id = customer_id
        tenant.stripe_subscription_id = subscription_id
        await db.flush()
        logger.info("tenant_upgraded", extra={"tenant_id": tenant_id, "plan": plan})


async def _handle_subscription_updated(data: dict) -> None:
    customer_id = data.get("customer")
    status = data.get("status")
    async with get_session() as db:
        result = await db.execute(select(Tenant).where(Tenant.stripe_customer_id == customer_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            return
        if status in ("past_due", "unpaid"):
            tenant.plan = "trial"  # downgrade until paid
        await db.flush()


async def _handle_subscription_deleted(data: dict) -> None:
    customer_id = data.get("customer")
    async with get_session() as db:
        result = await db.execute(select(Tenant).where(Tenant.stripe_customer_id == customer_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            return
        tenant.plan = "trial"
        tenant.stripe_subscription_id = None
        await db.flush()


async def _handle_payment_failed(data: dict) -> None:
    customer_id = data.get("customer")
    logger.warning("payment_failed", extra={"customer_id": customer_id})
    # TODO: enqueue dunning email job
