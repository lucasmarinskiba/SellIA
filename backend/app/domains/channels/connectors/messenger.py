"""Facebook Messenger Connector via Meta Graph API."""

import httpx
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class MessengerConnector(BaseChannelConnector):
    """Conector para Facebook Messenger usando Meta Graph API."""
    platform = "messenger"
    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.api_token = credentials.get("api_token")
        self.page_id = credentials.get("page_id")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        if not self.api_token:
            raise ValueError("Faltan credenciales de Messenger")

        url = f"{self.BASE_URL}/me/messages"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": content},
            "messaging_type": "RESPONSE",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        entry = raw_payload.get("entry", [{}])[0]
        messaging = entry.get("messaging", [{}])[0]
        sender = messaging.get("sender", {})
        message = messaging.get("message", {})

        return WebhookPayload(
            platform=ChannelPlatform.MESSENGER,
            external_id=sender.get("id"),
            sender_name=sender.get("name", "Messenger User"),
            sender_id=sender.get("id"),
            content=message.get("text", ""),
            content_type="text",
            extra_data=raw_payload,
        )

    async def validate_credentials(self) -> bool:
        if not self.api_token:
            return False
        try:
            url = f"{self.BASE_URL}/me"
            headers = {"Authorization": f"Bearer {self.api_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception:
            return False
