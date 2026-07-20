"""Webhook Receiver — Unified message ingestion from all platforms.

Recibe mensajes de:
- WhatsApp → direct message
- Instagram → DM + comments
- TikTok → comments
- Facebook → comments
- Mercado Libre → messages
- Amazon → messages
- Hotmart → messages

Normaliza a formato estándar → Message Queue.
"""

import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class MessageSource(str, Enum):
    """Origen del mensaje."""
    WHATSAPP = "whatsapp"
    INSTAGRAM_DM = "instagram_dm"
    INSTAGRAM_COMMENT = "instagram_comment"
    TIKTOK_COMMENT = "tiktok_comment"
    FACEBOOK_COMMENT = "facebook_comment"
    MERCADOLIBRE_MESSAGE = "mercadolibre_message"
    AMAZON_MESSAGE = "amazon_message"
    HOTMART_MESSAGE = "hotmart_message"


class MessageType(str, Enum):
    """Tipo de mensaje."""
    DIRECT_MESSAGE = "direct_message"
    COMMENT = "comment"
    REVIEW = "review"


@dataclass
class IncomingMessage:
    """Mensaje normalizado desde cualquier plataforma."""

    # Identidades
    customer_id: str  # ID único en plataforma
    customer_name: str
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None

    # Mensaje
    message_id: str  # ID único en plataforma
    source: MessageSource
    message_type: MessageType
    content: str
    media_urls: Optional[list] = None

    # Contexto
    product_id: Optional[str] = None  # Si es comentario de producto
    order_id: Optional[str] = None  # Si es sobre orden
    previous_messages: Optional[list] = None  # Historial (últimos 5)

    # Metadata
    received_at: datetime = None
    platform_timestamp: Optional[datetime] = None
    raw_data: Optional[Dict[str, Any]] = None  # Datos crudos para debug

    def __post_init__(self):
        if self.received_at is None:
            self.received_at = datetime.utcnow()


class WhatsAppWebhookHandler:
    """Maneja webhooks de WhatsApp."""

    @staticmethod
    def parse(payload: Dict[str, Any], user_id: str) -> Optional[IncomingMessage]:
        """
        Parsea webhook de WhatsApp.

        Espera estructura Meta WhatsApp Business API.
        """
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})

            messages = value.get("messages", [])
            if not messages:
                return None

            msg_data = messages[0]
            contact_data = value.get("contacts", [{}])[0]

            customer_id = msg_data.get("from")
            message_id = msg_data.get("id")
            content = msg_data.get("text", {}).get("body", "")

            if not customer_id or not content:
                return None

            return IncomingMessage(
                customer_id=customer_id,
                customer_name=contact_data.get("profile", {}).get("name", "Unknown"),
                customer_phone=customer_id,
                message_id=message_id,
                source=MessageSource.WHATSAPP,
                message_type=MessageType.DIRECT_MESSAGE,
                content=content,
                platform_timestamp=datetime.utcfromtimestamp(int(msg_data.get("timestamp", 0))),
                raw_data=payload,
            )

        except Exception as e:
            logger.error(f"WhatsApp parse error: {e}")
            return None


class InstagramWebhookHandler:
    """Maneja webhooks de Instagram (comments + DMs)."""

    @staticmethod
    def parse(payload: Dict[str, Any], user_id: str) -> Optional[IncomingMessage]:
        """
        Parsea webhook de Instagram.

        Puede ser DM o comment → detecta automáticamente.
        """
        try:
            entry = payload.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            field = changes.get("field")
            value = changes.get("value", {})

            # DMs
            if field == "messages":
                msg = value.get("message_type") == "text" and value.get("text", "")
                if not msg:
                    return None

                return IncomingMessage(
                    customer_id=value.get("sender", {}).get("id"),
                    customer_name=value.get("sender", {}).get("name", "Unknown"),
                    message_id=value.get("id"),
                    source=MessageSource.INSTAGRAM_DM,
                    message_type=MessageType.DIRECT_MESSAGE,
                    content=msg,
                    raw_data=payload,
                )

            # Comments
            elif field == "comments":
                return IncomingMessage(
                    customer_id=value.get("from", {}).get("id"),
                    customer_name=value.get("from", {}).get("username", "Unknown"),
                    message_id=value.get("id"),
                    source=MessageSource.INSTAGRAM_COMMENT,
                    message_type=MessageType.COMMENT,
                    content=value.get("text", ""),
                    product_id=value.get("object", {}).get("id"),
                    raw_data=payload,
                )

            return None

        except Exception as e:
            logger.error(f"Instagram parse error: {e}")
            return None


class TikTokWebhookHandler:
    """Maneja webhooks de TikTok (comments)."""

    @staticmethod
    def parse(payload: Dict[str, Any], user_id: str) -> Optional[IncomingMessage]:
        """Parsea webhook de TikTok comments."""
        try:
            events = payload.get("events", [])
            if not events:
                return None

            event = events[0]
            properties = event.get("properties", {})

            return IncomingMessage(
                customer_id=properties.get("comment_author_id"),
                customer_name=properties.get("comment_author_name", "Unknown"),
                message_id=properties.get("comment_id"),
                source=MessageSource.TIKTOK_COMMENT,
                message_type=MessageType.COMMENT,
                content=properties.get("comment_text", ""),
                product_id=properties.get("video_id"),
                raw_data=payload,
            )

        except Exception as e:
            logger.error(f"TikTok parse error: {e}")
            return None


class FacebookWebhookHandler:
    """Maneja webhooks de Facebook (comments + Messenger)."""

    @staticmethod
    def parse(payload: Dict[str, Any], user_id: str) -> Optional[IncomingMessage]:
        """Parsea webhook de Facebook."""
        try:
            entry = payload.get("entry", [{}])[0]
            messaging = entry.get("messaging", [])

            if messaging:
                # Messenger DM
                msg_event = messaging[0]
                return IncomingMessage(
                    customer_id=msg_event.get("sender", {}).get("id"),
                    customer_name=f"User {msg_event.get('sender', {}).get('id')}",
                    message_id=msg_event.get("message", {}).get("mid"),
                    source=MessageSource.FACEBOOK_COMMENT,
                    message_type=MessageType.DIRECT_MESSAGE,
                    content=msg_event.get("message", {}).get("text", ""),
                    raw_data=payload,
                )

            # Comment
            changes = entry.get("changes", [{}])[0]
            if changes.get("field") == "feed":
                value = changes.get("value", {})
                return IncomingMessage(
                    customer_id=value.get("from", {}).get("id"),
                    customer_name=value.get("from", {}).get("name", "Unknown"),
                    message_id=value.get("id"),
                    source=MessageSource.FACEBOOK_COMMENT,
                    message_type=MessageType.COMMENT,
                    content=value.get("message", ""),
                    product_id=value.get("object", {}).get("id"),
                    raw_data=payload,
                )

            return None

        except Exception as e:
            logger.error(f"Facebook parse error: {e}")
            return None


class WebhookReceiverService:
    """Unificador de webhooks — distribuidores a handlers."""

    HANDLERS = {
        "whatsapp": WhatsAppWebhookHandler,
        "instagram": InstagramWebhookHandler,
        "tiktok": TikTokWebhookHandler,
        "facebook": FacebookWebhookHandler,
    }

    @staticmethod
    async def process(
        platform: str,
        payload: Dict[str, Any],
        user_id: str,
    ) -> Optional[IncomingMessage]:
        """
        Procesa webhook de cualquier plataforma.

        Normaliza → IncomingMessage → lista para auto-responder.
        """
        handler_class = WebhookReceiverService.HANDLERS.get(platform.lower())

        if not handler_class:
            logger.warning(f"No handler for platform: {platform}")
            return None

        message = handler_class.parse(payload, user_id)

        if message:
            logger.info(
                f"Webhook processed: {platform} | "
                f"type={message.message_type.value} | "
                f"from={message.customer_id}"
            )

        return message
