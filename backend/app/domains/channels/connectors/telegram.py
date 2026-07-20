"""Telegram Bot Connector."""

import httpx
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class TelegramConnector(BaseChannelConnector):
    """Conector para Telegram usando Bot API."""
    platform = "telegram"
    BASE_URL = "https://api.telegram.org"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.bot_token = credentials.get("bot_token")
        self.webhook_secret = credentials.get("webhook_secret")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        if not self.bot_token:
            raise ValueError("Falta el bot token de Telegram")

        url = f"{self.BASE_URL}/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": recipient_id,
            "text": content,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        message = raw_payload.get("message", {})
        chat = message.get("chat", {})
        from_user = message.get("from", {})

        return WebhookPayload(
            platform=ChannelPlatform.TELEGRAM,
            external_id=str(chat.get("id")),
            sender_name=f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip() or "Telegram User",
            sender_id=str(from_user.get("id")),
            content=message.get("text", ""),
            content_type="text",
            extra_data=raw_payload,
        )

    async def validate_credentials(self) -> bool:
        if not self.bot_token:
            return False
        try:
            url = f"{self.BASE_URL}/bot{self.bot_token}/getMe"
            async with httpx.AsyncClient() as client:
                response = await client.get(url)
                data = response.json()
                return data.get("ok", False)
        except Exception:
            return False
