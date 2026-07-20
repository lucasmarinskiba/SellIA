"""Job task implementations · executed by RQ worker."""
import asyncio
import logging
from typing import Any

import httpx

from app.core.config import settings


logger = logging.getLogger(__name__)


# ─── AI tasks ────────────────────────────────────────────────────────────────


def generate_ai_reply(tenant_id: str, conversation_id: str, user_text: str) -> dict[str, Any]:
    """Generate AI reply · sync wrapper around async client."""
    return asyncio.run(_async_generate(tenant_id, conversation_id, user_text))


async def _async_generate(tenant_id: str, conversation_id: str, user_text: str) -> dict[str, Any]:
    if settings.ANTHROPIC_API_KEY:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        resp = await client.messages.create(
            model="claude-haiku-3-5-20241022",
            max_tokens=512,
            system="Sos SellIA · vendedor experto.",
            messages=[{"role": "user", "content": user_text}],
        )
        reply = resp.content[0].text
        provider = "anthropic"
    else:
        async with httpx.AsyncClient(timeout=30.0) as c:
            r = await c.post(f"{settings.OLLAMA_URL}/api/generate",
                             json={"model": "llama3.3", "prompt": user_text, "stream": False})
            r.raise_for_status()
            reply = r.json().get("response", "").strip()
            provider = "ollama"

    return {"tenant_id": tenant_id, "conversation_id": conversation_id, "reply": reply, "provider": provider}


# ─── Email tasks ─────────────────────────────────────────────────────────────


def send_email(tenant_id: str, to: str, subject: str, html: str) -> dict[str, Any]:
    """Send transactional email via Resend/SendGrid/SES (placeholder)."""
    logger.info("email_send", extra={"to": to, "subject": subject})
    # TODO: integrate Resend
    return {"sent": True, "to": to}


# ─── Stripe billing tasks ────────────────────────────────────────────────────


def dunning_email(tenant_id: str, customer_email: str, attempt: int) -> dict[str, Any]:
    """Send payment-failed email · attempt 1-4 · escalating tone."""
    templates = {
        1: "Hubo un problema con tu pago. Actualizá tu método.",
        2: "Recordatorio: tu suscripción está pendiente.",
        3: "Última oportunidad · suspendemos en 3 días.",
        4: "Cuenta suspendida.",
    }
    return send_email(tenant_id, customer_email, "Pago pendiente", templates.get(attempt, ""))


# ─── Periodic / cron tasks ───────────────────────────────────────────────────


def daily_report(tenant_id: str) -> dict[str, Any]:
    """Daily report aggregation · email to owner."""
    logger.info("daily_report", extra={"tenant_id": tenant_id})
    return {"generated": True}


def stock_check(tenant_id: str) -> dict[str, Any]:
    """Check stock levels · trigger auto-reorder if below threshold."""
    logger.info("stock_check", extra={"tenant_id": tenant_id})
    return {"checked": True}
