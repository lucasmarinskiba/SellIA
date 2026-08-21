"""Resend webhook receiver — cierra el loop de tracking que email_sender.py
ya tenía definido (mark_opened/mark_clicked/mark_bounced/mark_unsubscribed)
pero que nadie llamaba: no había receptor de los eventos reales de entrega.

Resend firma sus webhooks con Svix (no HMAC simple tipo Meta/Shopify):
  headers: svix-id, svix-timestamp, svix-signature
  signed_content = "{svix-id}.{svix-timestamp}.{raw_body}"
  secret = RESEND_WEBHOOK_SECRET, formato "whsec_<base64>"
  signature = base64(HMAC-SHA256(base64_decode(secret_sin_prefijo), signed_content))
  svix-signature trae 1+ firmas espacio-separadas, formato "v1,<sig>"

Docs: https://resend.com/docs/dashboard/webhooks/event-types
      https://docs.svix.com/receiving/verifying-payloads/how-manual
"""
import base64
import hashlib
import hmac
import logging
import os
import time

from fastapi import APIRouter, Header, HTTPException, Request

from app.core.email_sender import EmailSender, EmailProvider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhooks/resend", tags=["resend-webhooks"])

_TOLERANCE_SECONDS = 60 * 5  # rechazar timestamps con más de 5 min de desvío


def verify_svix_signature(
    raw_body: bytes,
    svix_id: str,
    svix_timestamp: str,
    svix_signature: str,
    secret: str,
) -> bool:
    """Verifica la firma Svix de un webhook de Resend."""
    try:
        if abs(time.time() - int(svix_timestamp)) > _TOLERANCE_SECONDS:
            logger.warning("Resend webhook: timestamp fuera de tolerancia")
            return False
    except ValueError:
        return False

    if not secret.startswith("whsec_"):
        logger.error("RESEND_WEBHOOK_SECRET con formato inesperado (debe empezar con whsec_)")
        return False

    secret_bytes = base64.b64decode(secret[len("whsec_"):])
    signed_content = f"{svix_id}.{svix_timestamp}.{raw_body.decode('utf-8')}"
    expected = base64.b64encode(
        hmac.new(secret_bytes, signed_content.encode("utf-8"), hashlib.sha256).digest()
    ).decode("utf-8")

    # svix-signature puede traer varias firmas espacio-separadas ("v1,<sig> v1,<sig2>")
    for candidate in svix_signature.split(" "):
        version, _, sig = candidate.partition(",")
        if version == "v1" and hmac.compare_digest(sig, expected):
            return True
    return False


@router.post("")
async def receive_resend_webhook(
    request: Request,
    svix_id: str = Header(..., alias="svix-id"),
    svix_timestamp: str = Header(..., alias="svix-timestamp"),
    svix_signature: str = Header(..., alias="svix-signature"),
) -> dict:
    """Recibe eventos reales de entrega de Resend y los despacha a los
    handlers mark_* que ya existían pero nunca se llamaban."""
    raw_body = await request.body()

    secret = os.getenv("RESEND_WEBHOOK_SECRET")
    if not secret:
        logger.error("RESEND_WEBHOOK_SECRET no configurado - rechazando webhook")
        raise HTTPException(status_code=503, detail="Resend webhook no configurado")

    if not verify_svix_signature(raw_body, svix_id, svix_timestamp, svix_signature, secret):
        raise HTTPException(status_code=401, detail="Firma inválida")

    payload = await request.json()
    event_type = payload.get("type", "")
    data = payload.get("data", {})

    sender = EmailSender(EmailProvider.RESEND)
    email_to = (data.get("to") or [None])[0]
    tracking_id = None
    for tag in data.get("tags", []) or []:
        if tag.get("name") == "tracking_id":
            tracking_id = tag.get("value")
            break

    if event_type == "email.opened" and tracking_id:
        result = await sender.mark_opened(tracking_id)
    elif event_type == "email.clicked" and tracking_id:
        result = await sender.mark_clicked(tracking_id, data.get("click", {}).get("link", ""))
    elif event_type in ("email.bounced", "email.delivery_delayed") and email_to:
        result = await sender.mark_bounced(email_to, data.get("bounce", {}).get("message", event_type))
    elif event_type == "email.complained" and email_to:
        result = await sender.mark_unsubscribed(email_to)
    else:
        logger.info(f"Resend webhook: evento {event_type} recibido, sin handler específico")
        result = {"status": "received", "event_type": event_type}

    return {"status": "ok", "event_type": event_type, "handled": result}
