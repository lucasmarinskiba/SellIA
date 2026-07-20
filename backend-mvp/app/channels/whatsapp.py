"""WhatsApp Cloud API webhook · receive inbound + dispatch to AI."""
import hashlib
import hmac
import logging
import uuid

import httpx
from fastapi import APIRouter, Header, HTTPException, Query, Request
from sqlalchemy import select

from app.core.config import settings
from app.db.models import (
    Channel,
    ChannelKind,
    Contact,
    Conversation,
    Message,
    MessageRole,
)
from app.db.session import get_session


logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("")
async def verify_webhook(
    mode: str = Query(alias="hub.mode"),
    token: str = Query(alias="hub.verify_token"),
    challenge: str = Query(alias="hub.challenge"),
):
    """Meta GET verification handshake."""
    if mode == "subscribe" and token == settings.WA_VERIFY_TOKEN:
        return int(challenge)
    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("")
async def receive_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(None, alias="x-hub-signature-256"),
):
    """Receive inbound WhatsApp messages."""
    body = await request.body()

    # Verify signature
    if settings.WA_APP_SECRET and x_hub_signature_256:
        expected = "sha256=" + hmac.new(
            settings.WA_APP_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected, x_hub_signature_256):
            raise HTTPException(status_code=403, detail="Invalid signature")

    payload = await request.json()

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            if change.get("field") != "messages":
                continue
            value = change.get("value", {})
            phone_number_id = value.get("metadata", {}).get("phone_number_id")
            for msg in value.get("messages", []):
                await _process_inbound(phone_number_id, msg, value)

    return {"received": True}


async def _process_inbound(phone_number_id: str, msg: dict, value: dict) -> None:
    """Persist + route inbound message to AI."""
    from_phone = msg.get("from")
    text_body = msg.get("text", {}).get("body", "")

    if not from_phone or not text_body:
        return

    # Find tenant via channel.external_id == phone_number_id
    async with get_session() as db:
        ch_result = await db.execute(
            select(Channel).where(
                Channel.external_id == phone_number_id,
                Channel.kind == ChannelKind.WHATSAPP,
                Channel.is_active.is_(True),
            )
        )
        channel = ch_result.scalar_one_or_none()
        if not channel:
            logger.warning("channel_not_found", extra={"phone_number_id": phone_number_id})
            return

    async with get_session(tenant_id=str(channel.tenant_id)) as db:
        # Upsert contact
        contact_result = await db.execute(
            select(Contact).where(Contact.phone == from_phone)
        )
        contact = contact_result.scalar_one_or_none()
        if not contact:
            contact = Contact(
                tenant_id=channel.tenant_id,
                phone=from_phone,
                name=value.get("contacts", [{}])[0].get("profile", {}).get("name"),
            )
            db.add(contact)
            await db.flush()

        # Get/create conversation
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.contact_id == contact.id,
                Conversation.channel_id == channel.id,
            )
        )
        conv = conv_result.scalar_one_or_none()
        if not conv:
            conv = Conversation(
                tenant_id=channel.tenant_id,
                channel_id=channel.id,
                contact_id=contact.id,
            )
            db.add(conv)
            await db.flush()

        # Insert message
        message = Message(
            tenant_id=channel.tenant_id,
            conversation_id=conv.id,
            role=MessageRole.INBOUND,
            body=text_body,
            metadata_={"wa_msg_id": msg.get("id"), "phone": from_phone},
        )
        db.add(message)
        await db.flush()

    # Dispatch to AI (async background task in prod, blocking here for MVP)
    ai_reply = await _generate_ai_reply(text_body)

    # Send reply via Cloud API
    await send_whatsapp_message(phone_number_id, from_phone, ai_reply)

    # Persist outbound
    async with get_session(tenant_id=str(channel.tenant_id)) as db:
        out_msg = Message(
            tenant_id=channel.tenant_id,
            conversation_id=conv.id,
            role=MessageRole.OUTBOUND_AI,
            body=ai_reply,
        )
        db.add(out_msg)


async def _generate_ai_reply(user_text: str) -> str:
    """
    Call Claude (or Ollama fallback) for reply.
    Production: route via cost-router (cheap → premium based on complexity).
    """
    if settings.ANTHROPIC_API_KEY:
        try:
            from anthropic import AsyncAnthropic
            client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            resp = await client.messages.create(
                model="claude-haiku-3-5-20241022",
                max_tokens=512,
                system="Sos SellIA, vendedor experto. Respondé conciso, empático, orientado a cerrar venta.",
                messages=[{"role": "user", "content": user_text}],
            )
            return resp.content[0].text
        except Exception as e:
            logger.exception("anthropic_call_failed", extra={"error": str(e)})

    # Fallback to Ollama
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{settings.OLLAMA_URL}/api/generate",
                json={
                    "model": "llama3.3",
                    "prompt": f"Sos SellIA, vendedor experto. Cliente dice: {user_text}\nTu respuesta:",
                    "stream": False,
                },
            )
            resp.raise_for_status()
            return resp.json().get("response", "").strip()
    except Exception as e:
        logger.exception("ollama_call_failed", extra={"error": str(e)})
        return "Hola! Estoy procesando tu mensaje. Vuelvo en un momento."


async def send_whatsapp_message(phone_number_id: str, to_phone: str, text: str) -> dict:
    """Send outbound via WhatsApp Cloud API."""
    if not settings.WA_ACCESS_TOKEN:
        logger.warning("wa_send_skipped_no_token")
        return {}

    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.post(
            f"https://graph.facebook.com/v21.0/{phone_number_id}/messages",
            headers={
                "Authorization": f"Bearer {settings.WA_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            },
            json={
                "messaging_product": "whatsapp",
                "to": to_phone,
                "type": "text",
                "text": {"body": text},
            },
        )
        resp.raise_for_status()
        return resp.json()
