"""Email delivery · Resend primary · SES fallback · stdout in dev."""
import logging
from typing import Any

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


class EmailError(Exception):
    pass


async def send_email(
    to: str | list[str],
    subject: str,
    html: str,
    *,
    text: str | None = None,
    from_addr: str | None = None,
    reply_to: str | None = None,
    tags: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Send email via Resend.

    Falls back to stdout in dev (no RESEND_API_KEY).
    Returns provider response (`{"id": "..."}`).
    """
    recipients = [to] if isinstance(to, str) else to
    sender = from_addr or getattr(settings, "EMAIL_FROM", None) or "SellIA <no-reply@sellia.app>"

    api_key = getattr(settings, "RESEND_API_KEY", None)
    if not api_key:
        logger.info("email_stub", extra={"to": recipients, "subject": subject})
        return {"id": "stub", "stub": True}

    body: dict[str, Any] = {
        "from": sender,
        "to": recipients,
        "subject": subject,
        "html": html,
    }
    if text:
        body["text"] = text
    if reply_to:
        body["reply_to"] = reply_to
    if tags:
        body["tags"] = [{"name": k, "value": v} for k, v in tags.items()]

    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=body,
        )
        if r.status_code >= 300:
            logger.warning("resend_failed", extra={"status": r.status_code, "body": r.text})
            raise EmailError(f"Resend {r.status_code}: {r.text}")
        return r.json()


# ─── Templates ──────────────────────────────────────────────────────────────


def template_welcome(name: str, login_url: str) -> tuple[str, str]:
    """Returns (subject, html). Plain-template · no Jinja dep for MVP."""
    subject = f"Bienvenido a SellIA, {name}"
    html = f"""
<!doctype html>
<html><body style="font-family:-apple-system,system-ui,sans-serif;background:#0a0e1a;color:#fff;padding:24px">
  <div style="max-width:520px;margin:auto;background:#0c0a1a;border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:32px">
    <h1 style="background:linear-gradient(90deg,#06b6d4,#a855f7,#ec4899);-webkit-background-clip:text;background-clip:text;color:transparent;font-size:20px;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 8px">SellIA</h1>
    <p style="font-size:14px;color:rgba(255,255,255,0.6);margin:0 0 24px">Tu Brain Hub está activo</p>
    <p style="font-size:16px;color:#fff">Hola {name},</p>
    <p style="font-size:14px;color:rgba(255,255,255,0.85);line-height:1.6">Tu cuenta SellIA está lista. Iniciá sesión y dejá que el cerebro empiece a vender por vos.</p>
    <p style="margin:24px 0"><a href="{login_url}" style="background:linear-gradient(90deg,#06b6d4,#ec4899);color:#fff;text-decoration:none;padding:12px 24px;border-radius:8px;font-weight:bold;display:inline-block">Ir al Dashboard →</a></p>
    <p style="font-size:11px;color:rgba(255,255,255,0.4);margin-top:32px">Si no creaste esta cuenta, ignorá este email.</p>
  </div>
</body></html>"""
    return subject, html


def template_payment_failed(name: str, amount_cents: int, retry_url: str) -> tuple[str, str]:
    subject = "Acción requerida · pago pendiente"
    html = f"""<!doctype html>
<html><body style="font-family:system-ui,sans-serif;padding:24px;background:#0a0e1a;color:#fff">
  <div style="max-width:520px;margin:auto;background:#0c0a1a;border:1px solid rgba(239,68,68,0.3);border-radius:16px;padding:32px">
    <p style="font-size:14px;color:#ef4444;text-transform:uppercase;letter-spacing:0.1em;margin:0">⚠ Pago pendiente</p>
    <p style="font-size:16px">Hola {name}, no pudimos procesar tu pago de ${amount_cents / 100:.2f}.</p>
    <p><a href="{retry_url}" style="background:#ef4444;color:#fff;padding:12px 24px;border-radius:8px;text-decoration:none;display:inline-block;font-weight:bold">Reintentar pago →</a></p>
  </div>
</body></html>"""
    return subject, html


def template_deal_won(customer_name: str, amount_cents: int, technique: str) -> tuple[str, str]:
    subject = f"🎉 Cerraste con {customer_name} · ${amount_cents / 100:.2f}"
    html = f"""<!doctype html>
<html><body style="font-family:system-ui,sans-serif;padding:24px;background:#0a0e1a;color:#fff">
  <div style="max-width:520px;margin:auto;background:linear-gradient(135deg,rgba(34,197,94,0.1),transparent);border:1px solid rgba(34,197,94,0.3);border-radius:16px;padding:32px">
    <p style="font-size:32px;margin:0">🎉</p>
    <p style="font-size:18px;color:#22c55e;font-weight:bold;margin:8px 0">¡Cerraste una venta!</p>
    <p style="font-size:14px;color:rgba(255,255,255,0.8)">{customer_name} · <strong style="color:#22c55e">${amount_cents / 100:.2f}</strong></p>
    <p style="font-size:12px;color:rgba(168,85,247,0.8);font-style:italic">Técnica usada: {technique}</p>
  </div>
</body></html>"""
    return subject, html
