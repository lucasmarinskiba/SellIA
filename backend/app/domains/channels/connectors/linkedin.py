"""LinkedIn Messaging Connector."""

import httpx
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class LinkedInConnector(BaseChannelConnector):
    """Conector para LinkedIn Messages usando LinkedIn API."""
    platform = "linkedin"
    BASE_URL = "https://api.linkedin.com/v2"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.access_token = credentials.get("access_token")
        self.sender_urn = credentials.get("sender_urn")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        if not self.access_token:
            raise ValueError("Faltan credenciales de LinkedIn")

        url = f"{self.BASE_URL}/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }
        payload = {
            "recipients": [f"urn:li:person:{recipient_id}"],
            "body": content,
            "subject": self.settings.get("subject", "Mensaje de tu negocio"),
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        event = raw_payload.get("event", {})
        from_entity = event.get("from", {})

        return WebhookPayload(
            platform=ChannelPlatform.LINKEDIN,
            external_id=from_entity.get("id"),
            sender_name=from_entity.get("name", "LinkedIn User"),
            sender_id=from_entity.get("id"),
            content=event.get("content", ""),
            content_type="text",
            extra_data=raw_payload,
        )

    async def validate_credentials(self) -> bool:
        if not self.access_token:
            return False
        try:
            url = f"{self.BASE_URL}/me"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception:
            return False
