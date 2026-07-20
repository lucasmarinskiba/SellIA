"""Stripe Billing Integration

Complete Stripe Checkout, Customer Portal and Webhook handling
for the SellIA SaaS subscription system.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any

from app.core.config import get_settings
from app.core.logger import get_logger
from app.core.circuit_breaker import stripe_breaker

logger = get_logger(__name__)

# Optional import so the app can boot even if stripe is not installed.
try:
    import stripe as stripe_lib
except Exception as _import_exc:  # pragma: no cover
    stripe_lib = None  # type: ignore[assignment]
    logger.warning("stripe library not installed: %s", _import_exc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_stripe_client() -> Any:
    """Return an initialized Stripe client or raise a clear error."""
    if stripe_lib is None:
        raise RuntimeError(
            "The 'stripe' Python library is not installed. "
            "Install it with: pip install stripe"
        )

    settings = get_settings()
    secret_key = getattr(settings, "STRIPE_SECRET_KEY", None)
    if not secret_key:
        raise RuntimeError("STRIPE_SECRET_KEY is not configured in settings.")

    stripe_lib.api_key = secret_key
    return stripe_lib


def _cents_from_usd(amount_usd: float) -> int:
    """Convert a USD float amount to integer cents for Stripe."""
    return int(round(amount_usd * 100))


# ---------------------------------------------------------------------------
# Customers
# ---------------------------------------------------------------------------

@stripe_breaker
async def create_stripe_customer(
    email: str,
    name: str | None = None,
    user_id: str | None = None,
) -> dict[str, Any]:
    """Create a Stripe Customer and return its data.

    Args:
        email: Customer email address.
        name: Full name (optional).
        user_id: Internal user UUID/id to store in metadata.

    Returns:
        Dictionary with ``customer_id``, ``email``, ``name``, ``metadata``.
    """
    stripe = _get_stripe_client()

    metadata: dict[str, str] = {}
    if user_id:
        metadata["user_id"] = str(user_id)

    try:
        # stripe_lib.Customer.create is synchronous I/O – run in a thread
        # so we do not block the event loop.
        customer = await asyncio.to_thread(
            stripe.Customer.create,
            email=email,
            name=name or email,
            metadata=metadata,
        )
    except stripe.error.StripeError as exc:
        logger.error("Stripe error creating customer for %s: %s", email, exc)
        raise
    except Exception as exc:
        logger.error("Unexpected error creating Stripe customer for %s: %s", email, exc)
        raise

    result = {
        "customer_id": customer.id,
        "email": getattr(customer, "email", email),
        "name": getattr(customer, "name", name),
        "metadata": dict(getattr(customer, "metadata", {})),
    }
    logger.info("Stripe customer created: %s", customer.id)
    return result


# ---------------------------------------------------------------------------
# Checkout Sessions
# ---------------------------------------------------------------------------

@stripe_breaker
async def create_checkout_session(
    plan_name: str,
    plan_slug: str,
    price_usd: float,
    user_id: str,
    customer_id: str,
    billing_cycle: str = "monthly",
    success_url: str | None = None,
    cancel_url: str | None = None,
) -> dict[str, Any]:
    """Create a Stripe Checkout Session for a subscription plan.

    Args:
        plan_name: Human-readable plan name (e.g. "Pro").
        plan_slug: Internal plan slug (e.g. "pro").
        price_usd: Price in US dollars (e.g. 49.0).
        user_id: Internal user id stored in metadata.
        customer_id: Existing Stripe Customer ID.
        billing_cycle: ``monthly`` or ``yearly``.
        success_url: Redirect URL after successful payment.
        cancel_url: Redirect URL after cancellation.

    Returns:
        Dictionary with ``session_id``, ``url``, ``client_secret`` (if applicable),
        ``price_id``, ``customer_id`` and ``metadata``.
    """
    stripe = _get_stripe_client()
    settings = get_settings()

    frontend_url = getattr(settings, "FRONTEND_URL", None) or "http://localhost:3000"
    success_url = success_url or f"{frontend_url}/dashboard/planes?status=success&session_id={{CHECKOUT_SESSION_ID}}"
    cancel_url = cancel_url or f"{frontend_url}/dashboard/planes?status=cancelled"

    interval = "month" if billing_cycle == "monthly" else "year"
    unit_amount = _cents_from_usd(price_usd)
    lookup_key = f"{plan_slug}-{billing_cycle}"

    try:
        # 1. Try to reuse an existing Price via lookup_key.
        price_list = await asyncio.to_thread(
            stripe.Price.list,
            lookup_keys=[lookup_key],
            limit=1,
        )

        if price_list and price_list.data:
            price = price_list.data[0]
            logger.debug("Reusing existing Stripe Price %s for %s", price.id, lookup_key)
        else:
            # 2. Create a Product (idempotent via idempotency_key).
            product = await asyncio.to_thread(
                stripe.Product.create,
                name=f"SellIA – Plan {plan_name}",
                description=f"Suscripción {billing_cycle} al plan {plan_name}",
                metadata={"plan_slug": plan_slug, "billing_cycle": billing_cycle},
                idempotency_key=f"product-{plan_slug}-{billing_cycle}",
            )

            # 3. Create a recurring Price.
            price = await asyncio.to_thread(
                stripe.Price.create,
                product=product.id,
                unit_amount=unit_amount,
                currency="usd",
                recurring={"interval": interval},
                lookup_key=lookup_key,
                metadata={"plan_slug": plan_slug, "billing_cycle": billing_cycle},
                idempotency_key=f"price-{plan_slug}-{billing_cycle}-{unit_amount}",
            )
            logger.info("Created Stripe Price %s for %s", price.id, lookup_key)

        # 4. Create Checkout Session.
        session = await asyncio.to_thread(
            stripe.checkout.Session.create,
            customer=customer_id,
            line_items=[
                {
                    "price": price.id,
                    "quantity": 1,
                }
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "user_id": str(user_id),
                "plan_slug": plan_slug,
                "plan_name": plan_name,
                "billing_cycle": billing_cycle,
            },
            subscription_data={
                "metadata": {
                    "user_id": str(user_id),
                    "plan_slug": plan_slug,
                    "plan_name": plan_name,
                    "billing_cycle": billing_cycle,
                }
            },
        )
    except stripe.error.StripeError as exc:
        logger.error(
            "Stripe error creating checkout session for user %s plan %s: %s",
            user_id, plan_slug, exc,
        )
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error creating checkout session for user %s plan %s: %s",
            user_id, plan_slug, exc,
        )
        raise

    result = {
        "session_id": session.id,
        "url": getattr(session, "url", None),
        "client_secret": getattr(session, "client_secret", None),
        "price_id": price.id,
        "customer_id": customer_id,
        "metadata": dict(getattr(session, "metadata", {})),
    }
    logger.info(
        "Stripe Checkout Session created: %s for user %s plan %s",
        session.id, user_id, plan_slug,
    )
    return result


# ---------------------------------------------------------------------------
# Customer Portal
# ---------------------------------------------------------------------------

@stripe_breaker
async def create_billing_portal_session(
    customer_id: str,
    return_url: str | None = None,
) -> dict[str, Any]:
    """Create a Stripe Customer Portal session.

    Args:
        customer_id: Stripe Customer ID.
        return_url: URL to redirect the customer back after managing billing.

    Returns:
        Dictionary with ``portal_session_id`` and ``url``.
    """
    stripe = _get_stripe_client()
    settings = get_settings()

    return_url = return_url or (
        getattr(settings, "FRONTEND_URL", None) or "http://localhost:3000"
    ) + "/dashboard/billing"

    try:
        session = await asyncio.to_thread(
            stripe.billing_portal.Session.create,
            customer=customer_id,
            return_url=return_url,
        )
    except stripe.error.StripeError as exc:
        logger.error(
            "Stripe error creating billing portal for customer %s: %s",
            customer_id, exc,
        )
        raise
    except Exception as exc:
        logger.error(
            "Unexpected error creating billing portal for customer %s: %s",
            customer_id, exc,
        )
        raise

    result = {
        "portal_session_id": session.id,
        "url": getattr(session, "url", None),
    }
    logger.info("Stripe Billing Portal session created: %s", session.id)
    return result


# ---------------------------------------------------------------------------
# Webhooks
# ---------------------------------------------------------------------------

def construct_webhook_event(
    payload: bytes,
    sig_header: str,
    webhook_secret: str | None = None,
) -> Any:
    """Verify and construct a Stripe webhook event.

    Args:
        payload: Raw request body bytes.
        sig_header: Value of the ``Stripe-Signature`` header.
        webhook_secret: Optional explicit webhook secret. If not provided,
            ``STRIPE_WEBHOOK_SECRET`` from settings is used.

    Returns:
        The verified Stripe Event object.

    Raises:
        ValueError: If the secret is missing or verification fails.
    """
    stripe = _get_stripe_client()

    if webhook_secret is None:
        settings = get_settings()
        webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", None)

    if not webhook_secret:
        raise ValueError(
            "STRIPE_WEBHOOK_SECRET is not configured. "
            "Provide it via settings or pass webhook_secret explicitly."
        )

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except stripe.error.SignatureVerificationError as exc:
        logger.warning("Stripe webhook signature verification failed: %s", exc)
        raise ValueError(f"Invalid Stripe signature: {exc}") from exc
    except Exception as exc:
        logger.error("Unexpected error constructing Stripe webhook event: %s", exc)
        raise ValueError(f"Webhook construction failed: {exc}") from exc

    logger.debug("Stripe webhook event constructed: type=%s id=%s", event.type, event.id)
    return event


def process_stripe_webhook(event: Any) -> dict[str, Any]:
    """Process a Stripe webhook event and return actionable data.

    Supported events:
        - ``checkout.session.completed``
        - ``invoice.paid``
        - ``invoice.payment_failed``
        - ``customer.subscription.deleted``

    Args:
        event: A verified Stripe Event object (from ``construct_webhook_event``).

    Returns:
        Dictionary with ``event_type``, ``event_id``, ``processed``,
        and subscription-related fields for the caller to update the DB.
    """
    event_type: str = getattr(event, "type", "unknown")
    event_id: str = getattr(event, "id", "unknown")
    data_object = getattr(event.data, "object", {})

    logger.info("Processing Stripe webhook: %s (id=%s)", event_type, event_id)

    result: dict[str, Any] = {
        "event_type": event_type,
        "event_id": event_id,
        "processed": False,
    }

    # ------------------------------------------------------------------
    # checkout.session.completed
    # ------------------------------------------------------------------
    if event_type == "checkout.session.completed":
        session = data_object
        subscription_id = getattr(session, "subscription", None)
        customer_id = getattr(session, "customer", None)
        metadata = dict(getattr(session, "metadata", {}))

        result.update(
            {
                "processed": True,
                "session_id": getattr(session, "id", None),
                "stripe_subscription_id": subscription_id,
                "stripe_customer_id": customer_id,
                "user_id": metadata.get("user_id"),
                "plan_slug": metadata.get("plan_slug"),
                "plan_name": metadata.get("plan_name"),
                "billing_cycle": metadata.get("billing_cycle"),
                "payment_status": getattr(session, "payment_status", None),
                "amount_total": getattr(session, "amount_total", None),
                "currency": getattr(session, "currency", None),
                "metadata": metadata,
            }
        )
        logger.info(
            "Checkout session completed: session=%s subscription=%s customer=%s",
            result["session_id"], subscription_id, customer_id,
        )

    # ------------------------------------------------------------------
    # invoice.paid
    # ------------------------------------------------------------------
    elif event_type == "invoice.paid":
        invoice = data_object
        subscription_id = getattr(invoice, "subscription", None)
        customer_id = getattr(invoice, "customer", None)
        lines = getattr(invoice, "lines", {}).get("data", [])
        plan_slug = None
        if lines:
            plan_slug = lines[0].get("plan", {}).get("metadata", {}).get("plan_slug")

        period_start = getattr(invoice, "period_start", None)
        period_end = getattr(invoice, "period_end", None)

        result.update(
            {
                "processed": True,
                "invoice_id": getattr(invoice, "id", None),
                "stripe_subscription_id": subscription_id,
                "stripe_customer_id": customer_id,
                "plan_slug": plan_slug,
                "amount_paid": getattr(invoice, "amount_paid", None),
                "currency": getattr(invoice, "currency", None),
                "status": "paid",
                "billing_reason": getattr(invoice, "billing_reason", None),
                "period_start": (
                    datetime.fromtimestamp(period_start, tz=timezone.utc)
                    if period_start else None
                ),
                "period_end": (
                    datetime.fromtimestamp(period_end, tz=timezone.utc)
                    if period_end else None
                ),
                "hosted_invoice_url": getattr(invoice, "hosted_invoice_url", None),
                "invoice_pdf": getattr(invoice, "invoice_pdf", None),
            }
        )
        logger.info(
            "Invoice paid: invoice=%s subscription=%s customer=%s",
            result["invoice_id"], subscription_id, customer_id,
        )

    # ------------------------------------------------------------------
    # invoice.payment_failed
    # ------------------------------------------------------------------
    elif event_type == "invoice.payment_failed":
        invoice = data_object
        subscription_id = getattr(invoice, "subscription", None)
        customer_id = getattr(invoice, "customer", None)
        attempt_count = getattr(invoice, "attempt_count", 0)
        next_payment_attempt = getattr(invoice, "next_payment_attempt", None)

        # Extract the last payment error if available.
        payment_intent = getattr(invoice, "payment_intent", None)
        last_error: dict[str, Any] | None = None
        if payment_intent and hasattr(stripe_lib, "PaymentIntent"):
            try:
                pi = stripe_lib.PaymentIntent.retrieve(payment_intent)
                last_charge = getattr(pi, "last_payment_error", None)
                if last_charge:
                    last_error = {
                        "code": getattr(last_charge, "code", None),
                        "decline_code": getattr(last_charge, "decline_code", None),
                        "message": getattr(last_charge, "message", None),
                    }
            except Exception as exc:
                logger.debug("Could not retrieve payment intent %s: %s", payment_intent, exc)

        result.update(
            {
                "processed": True,
                "invoice_id": getattr(invoice, "id", None),
                "stripe_subscription_id": subscription_id,
                "stripe_customer_id": customer_id,
                "amount_due": getattr(invoice, "amount_due", None),
                "currency": getattr(invoice, "currency", None),
                "status": "payment_failed",
                "attempt_count": attempt_count,
                "next_payment_attempt": (
                    datetime.fromtimestamp(next_payment_attempt, tz=timezone.utc)
                    if next_payment_attempt else None
                ),
                "last_error": last_error,
            }
        )
        logger.warning(
            "Invoice payment failed: invoice=%s subscription=%s attempt=%s",
            result["invoice_id"], subscription_id, attempt_count,
        )

    # ------------------------------------------------------------------
    # customer.subscription.deleted
    # ------------------------------------------------------------------
    elif event_type == "customer.subscription.deleted":
        subscription = data_object
        customer_id = getattr(subscription, "customer", None)
        metadata = dict(getattr(subscription, "metadata", {}))

        canceled_at = getattr(subscription, "canceled_at", None)
        ended_at = getattr(subscription, "ended_at", None)

        result.update(
            {
                "processed": True,
                "stripe_subscription_id": getattr(subscription, "id", None),
                "stripe_customer_id": customer_id,
                "user_id": metadata.get("user_id"),
                "plan_slug": metadata.get("plan_slug"),
                "plan_name": metadata.get("plan_name"),
                "billing_cycle": metadata.get("billing_cycle"),
                "status": "cancelled",
                "cancel_at_period_end": getattr(subscription, "cancel_at_period_end", False),
                "canceled_at": (
                    datetime.fromtimestamp(canceled_at, tz=timezone.utc)
                    if canceled_at else None
                ),
                "ended_at": (
                    datetime.fromtimestamp(ended_at, tz=timezone.utc)
                    if ended_at else None
                ),
                "metadata": metadata,
            }
        )
        logger.info(
            "Subscription deleted: subscription=%s customer=%s",
            result["stripe_subscription_id"], customer_id,
        )

    else:
        logger.debug("Unhandled Stripe webhook event type: %s", event_type)

    return result
