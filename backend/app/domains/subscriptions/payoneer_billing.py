"""Payoneer Checkout Integration

Provides helpers to create Payoneer Checkout payment requests
and process webhook notifications for international (USD) payments.

Payoneer Checkout API v4 flow:
1. Obtain OAuth2 access token (client_credentials)
2. Create a charge/payment request
3. Redirect customer to Payoneer checkout URL
4. Receive webhook confirmation when payment is completed
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.logger import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Payoneer API base URLs
PAYONEER_SANDBOX_BASE = "https://api.sandbox.payoneer.com/v4"
PAYONEER_LIVE_BASE = "https://api.payoneer.com/v4"


def _get_base_url() -> str:
    """Return the appropriate Payoneer API base URL."""
    if settings.ENVIRONMENT == "production":
        return PAYONEER_LIVE_BASE
    return PAYONEER_SANDBOX_BASE


def _has_credentials() -> bool:
    """Check if Payoneer credentials are configured."""
    return bool(
        settings.PAYONEER_PROGRAM_ID
        and settings.PAYONEER_CLIENT_ID
        and settings.PAYONEER_CLIENT_SECRET
    )


async def _get_access_token() -> str:
    """Obtain an OAuth2 access token from Payoneer."""
    if not _has_credentials():
        raise RuntimeError("Payoneer credentials not configured")

    base_url = _get_base_url()
    token_url = f"{base_url}/oauth/token"

    payload = {
        "grant_type": "client_credentials",
        "client_id": settings.PAYONEER_CLIENT_ID,
        "client_secret": settings.PAYONEER_CLIENT_SECRET,
        "scope": "read write",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(token_url, data=payload)
        response.raise_for_status()
        data = response.json()

    token = data.get("access_token")
    if not token:
        raise RuntimeError("Payoneer access_token not found in response")
    return token


async def create_payoneer_checkout(
    plan_name: str,
    plan_slug: str,
    price_usd: float,
    user_id: str,
    subscription_id: str,
    billing_cycle: str,
    success_url: str | None = None,
    cancel_url: str | None = None,
) -> dict[str, Any]:
    """Create a Payoneer Checkout payment request.

    Returns a dictionary with:
        - charge_id: str
        - checkout_url: str
        - status: str
        - metadata: dict
    """
    if not _has_credentials():
        raise RuntimeError(
            "Payoneer no está configurado. "
            "Faltan PAYONEER_PROGRAM_ID, PAYONEER_CLIENT_ID o PAYONEER_CLIENT_SECRET"
        )

    token = await _get_access_token()
    base_url = _get_base_url()
    program_id = settings.PAYONEER_PROGRAM_ID

    charges_url = f"{base_url}/programs/{program_id}/charges"

    frontend_url = settings.FRONTEND_URL or "http://localhost:3000"
    success = success_url or f"{frontend_url}/dashboard/planes?status=success&provider=payoneer"
    cancel = cancel_url or f"{frontend_url}/dashboard/planes?status=cancel"

    payload = {
        "amount": float(price_usd),
        "currency": "USD",
        "description": f"SellIA - Plan {plan_name} ({billing_cycle})",
        "metadata": {
            "user_id": user_id,
            "subscription_id": subscription_id,
            "plan_slug": plan_slug,
            "billing_cycle": billing_cycle,
            "sellia_version": "1.0",
        },
        "redirect_url": success,
        "cancel_url": cancel,
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(charges_url, json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()

    charge_id = data.get("id")
    checkout_url = data.get("checkout_url")

    if not charge_id or not checkout_url:
        raise RuntimeError(f"Payoneer response missing id or checkout_url: {data}")

    logger.info(f"Payoneer checkout created: charge={charge_id}, plan={plan_slug}, user={user_id}")

    return {
        "charge_id": charge_id,
        "checkout_url": checkout_url,
        "status": data.get("status", "pending"),
        "amount": float(price_usd),
        "currency": "USD",
        "metadata": payload["metadata"],
    }


async def get_payoneer_charge_status(charge_id: str) -> dict[str, Any]:
    """Query the status of a Payoneer charge."""
    if not _has_credentials():
        raise RuntimeError("Payoneer credentials not configured")

    token = await _get_access_token()
    base_url = _get_base_url()
    program_id = settings.PAYONEER_PROGRAM_ID

    url = f"{base_url}/programs/{program_id}/charges/{charge_id}"
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()

    return {
        "charge_id": data.get("id"),
        "status": data.get("status"),  # pending, paid, failed, cancelled
        "amount": data.get("amount"),
        "currency": data.get("currency"),
        "paid_at": data.get("paid_at"),
        "metadata": data.get("metadata", {}),
    }


def process_payoneer_webhook(payload: dict[str, Any]) -> dict[str, Any]:
    """Process a Payoneer webhook event.

    Expected payload structure:
    {
        "event": "charge.completed" | "charge.failed" | "charge.cancelled",
        "data": {
            "id": "charge_xxx",
            "status": "paid" | "failed" | "cancelled",
            "amount": 49.00,
            "currency": "USD",
            "metadata": { ... }
        }
    }
    """
    event_type = payload.get("event", "")
    data = payload.get("data", {})

    charge_id = data.get("id")
    status = data.get("status")
    metadata = data.get("metadata", {})

    logger.info(f"Payoneer webhook: event={event_type}, charge={charge_id}, status={status}")

    result = {
        "processed": False,
        "event_type": event_type,
        "charge_id": charge_id,
        "status": status,
        "user_id": metadata.get("user_id"),
        "subscription_id": metadata.get("subscription_id"),
        "plan_slug": metadata.get("plan_slug"),
        "billing_cycle": metadata.get("billing_cycle"),
        "amount": data.get("amount"),
        "currency": data.get("currency"),
    }

    if event_type in ("charge.completed", "charge.paid") and status == "paid":
        result["processed"] = True
        result["payment_status"] = "approved"
    elif event_type == "charge.failed":
        result["processed"] = True
        result["payment_status"] = "failed"
    elif event_type == "charge.cancelled":
        result["processed"] = True
        result["payment_status"] = "cancelled"

    return result


async def verify_payoneer_signature(
    payload: bytes,
    signature_header: str | None,
) -> bool:
    """Verify Payoneer webhook signature if a webhook secret is configured.

    Payoneer webhooks can optionally include a signature header for verification.
    If PAYONEER_WEBHOOK_SECRET is not set, verification is skipped (returns True).
    """
    webhook_secret = getattr(settings, "PAYONEER_WEBHOOK_SECRET", None)
    if not webhook_secret:
        return True  # No secret configured, skip verification

    if not signature_header:
        return False

    try:
        import hmac
        import hashlib

        expected = hmac.new(
            webhook_secret.encode(),
            payload,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature_header)
    except Exception:
        return False
