"""Computer Use Webhooks Router

Endpoints para recibir webhooks de plataformas:
- POST /webhooks/whatsapp — WhatsApp incoming messages
- POST /webhooks/instagram — Instagram DMs + comments
- POST /webhooks/tiktok — TikTok comments
- POST /webhooks/facebook — Facebook Messenger + comments
- POST /webhooks/mercadolibre — Mercado Libre messages
- POST /webhooks/amazon — Amazon messages
- POST /webhooks/hotmart — Hotmart messages

Webhooks sin autenticación (validar con tokens en headers).
"""

import logging
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status, Header, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import get_settings
from app.core.logger import get_logger
from app.domains.computer_use.services.webhook_receiver import (
    WebhookReceiverService,
    IncomingMessage,
)
from app.domains.computer_use.services.auto_responder import get_auto_responder_service

logger = get_logger(__name__)
settings = get_settings()
router = APIRouter()


async def _verify_webhook_token(
    x_webhook_token: str = Header(None),
    platform: str = None,
) -> str:
    """Verifica token de webhook."""
    if not x_webhook_token:
        raise HTTPException(status_code=401, detail="Missing webhook token")

    # Buscar token en env (formato: WEBHOOK_TOKEN_WHATSAPP, WEBHOOK_TOKEN_INSTAGRAM, etc)
    env_var = f"WEBHOOK_TOKEN_{platform.upper()}"
    expected_token = getattr(settings, env_var, None)

    if not expected_token or x_webhook_token != expected_token:
        raise HTTPException(status_code=401, detail="Invalid webhook token")

    return x_webhook_token


# ========== WhatsApp ==========

@router.post("/webhooks/whatsapp")
async def whatsapp_webhook(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    _token: str = Depends(lambda: _verify_webhook_token(platform="whatsapp")),
):
    """
    Webhook de WhatsApp Business API.

    Ejemplo de payload:
    {
      "object": "whatsapp_business_account",
      "entry": [{
        "changes": [{
          "value": {
            "messages": [{
              "from": "1234567890",
              "id": "msg_id",
              "timestamp": "1234567890",
              "text": {"body": "Hola"}
            }],
            "contacts": [{
              "profile": {"name": "John Doe"}
            }]
          }
        }]
      }]
    }
    """
    try:
        # Parsear webhook
        message = await WebhookReceiverService.process(
            platform="whatsapp",
            payload=payload,
            user_id="system",  # TODO: obtener del JWT o llevar track de accounts
        )

        if not message:
            return {"status": "no_message"}

        # Procesar en background (no bloquear respuesta)
        if background_tasks:
            background_tasks.add_task(_process_auto_response, db, message)

        return {"status": "received", "message_id": message.message_id}

    except Exception as e:
        logger.error(f"WhatsApp webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Instagram ==========

@router.post("/webhooks/instagram")
async def instagram_webhook(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    _token: str = Depends(lambda: _verify_webhook_token(platform="instagram")),
):
    """Webhook de Instagram (DMs + comments)."""
    try:
        message = await WebhookReceiverService.process(
            platform="instagram",
            payload=payload,
            user_id="system",
        )

        if not message:
            return {"status": "no_message"}

        if background_tasks:
            background_tasks.add_task(_process_auto_response, db, message)

        return {"status": "received", "message_id": message.message_id}

    except Exception as e:
        logger.error(f"Instagram webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== TikTok ==========

@router.post("/webhooks/tiktok")
async def tiktok_webhook(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    _token: str = Depends(lambda: _verify_webhook_token(platform="tiktok")),
):
    """Webhook de TikTok (comments)."""
    try:
        message = await WebhookReceiverService.process(
            platform="tiktok",
            payload=payload,
            user_id="system",
        )

        if not message:
            return {"status": "no_message"}

        if background_tasks:
            background_tasks.add_task(_process_auto_response, db, message)

        return {"status": "received", "message_id": message.message_id}

    except Exception as e:
        logger.error(f"TikTok webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Facebook ==========

@router.post("/webhooks/facebook")
async def facebook_webhook(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    _token: str = Depends(lambda: _verify_webhook_token(platform="facebook")),
):
    """Webhook de Facebook (Messenger + comments)."""
    try:
        message = await WebhookReceiverService.process(
            platform="facebook",
            payload=payload,
            user_id="system",
        )

        if not message:
            return {"status": "no_message"}

        if background_tasks:
            background_tasks.add_task(_process_auto_response, db, message)

        return {"status": "received", "message_id": message.message_id}

    except Exception as e:
        logger.error(f"Facebook webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Mercado Libre ==========

@router.post("/webhooks/mercadolibre")
async def mercadolibre_webhook(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    _token: str = Depends(lambda: _verify_webhook_token(platform="mercadolibre")),
):
    """Webhook de Mercado Libre (mensajes)."""
    try:
        message = await WebhookReceiverService.process(
            platform="mercadolibre",
            payload=payload,
            user_id="system",
        )

        if not message:
            return {"status": "no_message"}

        if background_tasks:
            background_tasks.add_task(_process_auto_response, db, message)

        return {"status": "received", "message_id": message.message_id}

    except Exception as e:
        logger.error(f"Mercado Libre webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Amazon ==========

@router.post("/webhooks/amazon")
async def amazon_webhook(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    _token: str = Depends(lambda: _verify_webhook_token(platform="amazon")),
):
    """Webhook de Amazon (mensajes)."""
    try:
        message = await WebhookReceiverService.process(
            platform="amazon",
            payload=payload,
            user_id="system",
        )

        if not message:
            return {"status": "no_message"}

        if background_tasks:
            background_tasks.add_task(_process_auto_response, db, message)

        return {"status": "received", "message_id": message.message_id}

    except Exception as e:
        logger.error(f"Amazon webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Hotmart ==========

@router.post("/webhooks/hotmart")
async def hotmart_webhook(
    payload: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
    background_tasks: BackgroundTasks = None,
    _token: str = Depends(lambda: _verify_webhook_token(platform="hotmart")),
):
    """Webhook de Hotmart (mensajes)."""
    try:
        message = await WebhookReceiverService.process(
            platform="hotmart",
            payload=payload,
            user_id="system",
        )

        if not message:
            return {"status": "no_message"}

        if background_tasks:
            background_tasks.add_task(_process_auto_response, db, message)

        return {"status": "received", "message_id": message.message_id}

    except Exception as e:
        logger.error(f"Hotmart webhook error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ========== Background Task ==========

async def _process_auto_response(db: AsyncSession, message: IncomingMessage) -> None:
    """
    Procesa respuesta automática en background.

    Ejecutado después de responder al webhook (no bloquea).
    """
    try:
        responder = get_auto_responder_service(db)

        # TODO: obtener user_id del owner de la account/business
        user_id = "system"  # placeholder

        response_text, status, confidence = await responder.process_message(
            user_id=user_id,
            message=message,
        )

        # TODO: enviar respuesta a la plataforma si status=success
        # - WhatsApp: usar API
        # - Instagram: usar API
        # - etc

        logger.info(
            f"Auto-response processed: {message.source.value} | "
            f"status={status} | confidence={confidence:.0%}"
        )

    except Exception as e:
        logger.error(f"Error processing auto-response: {e}")
