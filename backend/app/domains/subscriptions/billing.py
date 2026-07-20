"""Billing & Payment Gateway Integration

MercadoPago checkout and webhook handling.
"""

import os
from typing import Any, Optional
from datetime import datetime, timezone, timedelta

import httpx

from app.core.config import get_settings
from app.core.circuit_breaker import mercadopago_breaker

settings = get_settings()

MERCADOPAGO_API_BASE = "https://api.mercadopago.com"


def _get_headers() -> dict:
    token = settings.MERCADOPAGO_ACCESS_TOKEN or os.getenv("MERCADOPAGO_ACCESS_TOKEN")
    if not token:
        raise ValueError("MERCADOPAGO_ACCESS_TOKEN no configurado")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@mercadopago_breaker
async def create_checkout_preference(
    plan_name: str,
    plan_slug: str,
    price_ars: float,
    user_id: str,
    subscription_id: str,
    back_urls: Optional[dict] = None,
) -> dict[str, Any]:
    """Create a MercadoPago checkout preference for a subscription plan."""
    headers = _get_headers()

    payload = {
        "items": [
            {
                "title": f"SellIA - Plan {plan_name}",
                "description": f"Suscripción mensual al plan {plan_name}",
                "quantity": 1,
                "currency_id": "ARS",
                "unit_price": float(price_ars),
            }
        ],
        "payer": {"email": "user@example.com"},  # Will be updated with real email
        "external_reference": f"{user_id}:{subscription_id}:{plan_slug}",
        "auto_return": "approved",
        "back_urls": back_urls or {
            "success": f"{settings.FRONTEND_URL or 'http://localhost:3000'}/dashboard/planes?status=success",
            "failure": f"{settings.FRONTEND_URL or 'http://localhost:3000'}/dashboard/planes?status=failure",
            "pending": f"{settings.FRONTEND_URL or 'http://localhost:3000'}/dashboard/planes?status=pending",
        },
        "notification_url": f"{settings.TRACKING_BASE_URL or settings.FRONTEND_URL or 'http://localhost:8000'}/api/v1/subscriptions/webhook/mercadopago",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MERCADOPAGO_API_BASE}/checkout/preferences",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        return response.json()


@mercadopago_breaker
async def get_payment_info(payment_id: str) -> dict[str, Any]:
    """Get payment details from MercadoPago."""
    headers = _get_headers()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MERCADOPAGO_API_BASE}/v1/payments/{payment_id}",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()


async def process_mercadopago_webhook(
    topic: str,
    payment_id: Optional[str] = None,
    data_id: Optional[str] = None,
) -> dict[str, Any]:
    """Process MercadoPago IPN/webhook notification.

    Returns parsed payment info for the caller to update the subscription.
    """
    if topic == "payment" and payment_id:
        payment_info = await get_payment_info(payment_id)
        external_ref = payment_info.get("external_reference", "")
        status = payment_info.get("status")

        result = {
            "payment_id": payment_id,
            "status": status,
            "external_reference": external_ref,
            "amount": payment_info.get("transaction_amount"),
            "payment_method": payment_info.get("payment_method_id"),
        }

        if external_ref and ":" in external_ref:
            parts = external_ref.split(":")
            if len(parts) >= 3:
                result["user_id"] = parts[0]
                result["subscription_id"] = parts[1]
                result["plan_slug"] = parts[2]

        return result

    return {"status": "ignored", "topic": topic}


# =============================================================================
# MercadoPago Preapproval (Recurring Payments)
# =============================================================================

@mercadopago_breaker
async def create_preapproval(
    plan_name: str,
    plan_slug: str,
    price_ars: float,
    user_id: str,
    subscription_id: str,
    user_email: str,
    billing_cycle: str = "monthly",
) -> dict[str, Any]:
    """Create a MercadoPago preapproval for automatic recurring billing.

    Returns:
        {
            "preapproval_id": str,
            "init_point": str,
            "sandbox_init_point": str,
            "status": str,
        }
    """
    headers = _get_headers()

    frequency = 1
    frequency_type = "months"
    if billing_cycle == "yearly":
        frequency = 12

    external_reference = f"{user_id}:{subscription_id}:{plan_slug}:{billing_cycle}"
    back_url = f"{settings.FRONTEND_URL or 'http://localhost:3000'}/dashboard/suscripcion?mp_preapproval=success"

    payload = {
        "reason": f"SellIA - Plan {plan_name}",
        "external_reference": external_reference,
        "payer_email": user_email,
        "auto_recurring": {
            "frequency": frequency,
            "frequency_type": frequency_type,
            "transaction_amount": float(price_ars),
            "currency_id": "ARS",
        },
        "back_url": back_url,
        "status": "pending",
        "notification_url": f"{settings.TRACKING_BASE_URL or settings.FRONTEND_URL or 'http://localhost:8000'}/api/v1/subscriptions/webhook/mercadopago",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{MERCADOPAGO_API_BASE}/preapproval",
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    return {
        "preapproval_id": data.get("id"),
        "init_point": data.get("init_point"),
        "sandbox_init_point": data.get("sandbox_init_point"),
        "status": data.get("status"),
    }


@mercadopago_breaker
async def get_preapproval_status(preapproval_id: str) -> dict[str, Any]:
    """Get preapproval details from MercadoPago."""
    headers = _get_headers()
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{MERCADOPAGO_API_BASE}/preapproval/{preapproval_id}",
            headers=headers,
        )
        response.raise_for_status()
        return response.json()


@mercadopago_breaker
async def cancel_preapproval(preapproval_id: str) -> dict[str, Any]:
    """Cancel a MercadoPago preapproval."""
    headers = _get_headers()
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"{MERCADOPAGO_API_BASE}/preapproval/{preapproval_id}",
            headers=headers,
            json={"status": "cancelled"},
        )
        response.raise_for_status()
        return response.json()


async def process_preapproval_webhook(
    preapproval_id: str,
) -> dict[str, Any]:
    """Process MercadoPago preapproval webhook notification.

    Returns parsed preapproval info for the caller to update the subscription.
    """
    preapproval_info = await get_preapproval_status(preapproval_id)
    external_ref = preapproval_info.get("external_reference", "")
    status = preapproval_info.get("status")

    result = {
        "preapproval_id": preapproval_id,
        "status": status,
        "external_reference": external_ref,
        "reason": preapproval_info.get("reason"),
        "auto_recurring": preapproval_info.get("auto_recurring"),
        "next_payment_date": preapproval_info.get("next_payment_date"),
        "payment_method_id": preapproval_info.get("payment_method_id"),
    }

    if external_ref and ":" in external_ref:
        parts = external_ref.split(":")
        if len(parts) >= 3:
            result["user_id"] = parts[0]
            result["subscription_id"] = parts[1]
            result["plan_slug"] = parts[2]
        if len(parts) >= 4:
            result["billing_cycle"] = parts[3]

    return result
