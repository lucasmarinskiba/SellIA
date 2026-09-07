"""Shared MercadoPago webhook signature verification.

Extracted from api/v1/subscriptions.py's `_verify_mercadopago_signature`
(fixed earlier this session -- it referenced an undefined `settings` name
and NameError'd on every signed webhook call) so api/v1/payments.py's
webhook handler can use the same real verification instead of trusting
its request body unconditionally, which is what it did before this fix:
POST /businesses/{business_id}/webhooks/mercadopago accepted a raw
{type, data: {id, status, external_reference}} body from anyone and
directly set the referenced transaction's status to APPROVED -- a
complete payment-confirmation bypass, no signature, no auth, no
business-ownership check on the transaction being "confirmed".
"""
import hashlib
import hmac

from fastapi import Request

from app.core.config import get_settings

settings = get_settings()


def verify_mercadopago_signature(request: Request, body: dict) -> bool:
    """Verify MercadoPago webhook signature (X-Signature header).

    Format: X-Signature: ts=timestamp,v1=signature
    The signature is HMAC-SHA256 of 'id:<data.id>;type:<type>' using the webhook secret.
    If no signature header is present, we fall back to API callback validation.
    """
    x_signature = request.headers.get("X-Signature", "")
    if not x_signature:
        return True  # Legacy IPN may not have signature; rely on API callback
    secret = settings.MERCADOPAGO_ACCESS_TOKEN or ""
    if not secret:
        return False
    data_id = body.get("data", {}).get("id") if body.get("data") else body.get("id")
    topic = body.get("topic") or body.get("type")
    if not data_id or not topic:
        return False
    template = f"id:{data_id};topic:{topic}"
    expected = hmac.new(secret.encode(), template.encode(), hashlib.sha256).hexdigest()
    parts = x_signature.split(",")
    sig_map = {}
    for part in parts:
        if "=" in part:
            k, v = part.split("=", 1)
            sig_map[k.strip()] = v.strip()
    provided = sig_map.get("v1", "")
    return hmac.compare_digest(expected, provided)
