"""
WhatsApp webhook endpoint for Railway deployment.
Receives Meta webhook events → generates AI reply → sends via WhatsApp API.
Self-contained: no DB, no ORM. Uses httpx + Anthropic directly.
"""
import os
import logging
import httpx
from fastapi import APIRouter, Request, Response

logger = logging.getLogger(__name__)
router = APIRouter()

WHATSAPP_API_VERSION = "v19.0"
WHATSAPP_API_BASE = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"

SALES_SYSTEM_PROMPT = """Sos SellIA, un agente de ventas con IA que responde en nombre del negocio.
Tu objetivo es atender consultas de clientes, resolver dudas sobre productos/servicios,
y ayudar a cerrar ventas de forma natural y amigable.

Reglas:
- Respondé siempre en el mismo idioma del cliente
- Sé conciso (máximo 3 párrafos)
- Si el cliente pregunta por precio o disponibilidad que no conocés, decí que lo vas a confirmar
- No inventés información del negocio
- Usá un tono profesional pero cercano
- Si el cliente quiere hablar con una persona, decí que lo vas a conectar con el equipo"""


async def _call_anthropic(message: str) -> str:
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key or api_key.startswith("sk-ant-sellia-placeholder"):
        return "Hola! Recibí tu mensaje. En breve te contactamos."

    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 512,
        "system": SALES_SYSTEM_PROMPT,
        "messages": [{"role": "user", "content": message}],
    }
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["content"][0]["text"]


async def _send_whatsapp_message(to: str, text: str, phone_number_id: str, token: str):
    url = f"{WHATSAPP_API_BASE}/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {"body": text},
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            logger.error(f"WhatsApp send failed {resp.status_code}: {resp.text[:200]}")
        return resp.status_code == 200


@router.get("/webhooks/whatsapp")
async def whatsapp_verify(request: Request):
    """Meta webhook verification."""
    params = dict(request.query_params)
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    verify_token = os.getenv("META_WEBHOOK_VERIFY_TOKEN", "")
    if mode == "subscribe" and token == verify_token:
        logger.info("WhatsApp webhook verified")
        return Response(content=challenge, media_type="text/plain")
    logger.warning(f"Webhook verification failed: mode={mode}, token={token}")
    return Response(content="Forbidden", status_code=403)


@router.post("/webhooks/whatsapp")
async def whatsapp_receive(request: Request):
    """Receive WhatsApp messages from Meta and reply with AI."""
    try:
        body = await request.json()
    except Exception:
        return {"status": "ok"}

    try:
        entry = body.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return {"status": "ok"}

        msg = messages[0]
        msg_type = msg.get("type", "")

        # Only handle text messages for now
        if msg_type != "text":
            return {"status": "ok"}

        sender = msg.get("from", "")
        text = msg.get("text", {}).get("body", "").strip()

        if not sender or not text:
            return {"status": "ok"}

        phone_number_id = os.getenv("META_PHONE_NUMBER_ID", "")
        token = os.getenv("META_WHATSAPP_TOKEN", "")

        if not phone_number_id or not token:
            logger.error("Missing META_PHONE_NUMBER_ID or META_WHATSAPP_TOKEN")
            return {"status": "ok"}

        logger.info(f"Message from {sender}: {text[:80]}")

        # Generate AI reply
        reply = await _call_anthropic(text)

        # Send reply
        sent = await _send_whatsapp_message(sender, reply, phone_number_id, token)
        logger.info(f"Reply sent to {sender}: {sent}")

    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")

    return {"status": "ok"}
