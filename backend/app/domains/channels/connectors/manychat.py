"""ManyChat Connector.

ManyChat drives its own conversation flow (IG/FB/WA) and calls out to SellIA via
an "External Request" step configured by the business inside ManyChat, POSTing
the subscriber id + last message to our generic webhook
(`POST /api/v1/webhook/manychat?token=<channel.webhook_token>`).

Outbound: SellIA can send content back via the ManyChat API, and — this is the
actual lead-filtering mechanism — tag/set custom fields on the subscriber so the
business's own ManyChat flow can branch on SellIA's qualification result
(e.g. a "sellia_qualified" tag routes to a human, "sellia_disqualified" ends the flow).
"""

import httpx
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class ManyChatConnector(BaseChannelConnector):
    """Conector para ManyChat (IG/FB/WA automation) usando su API REST."""
    platform = "manychat"
    BASE_URL = "https://api.manychat.com"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.api_token = credentials.get("api_token")

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        if not self.api_token:
            raise ValueError("Falta el api_token de ManyChat")

        url = f"{self.BASE_URL}/fb/sending/sendContent"
        payload = {
            "subscriber_id": recipient_id,
            "data": {
                "version": "v2",
                "content": {
                    "messages": [{"type": "text", "text": content}],
                },
            },
            "message_tag": "ACCOUNT_UPDATE",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=self._headers())
            response.raise_for_status()
            return response.json()

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        """Parses the payload ManyChat's 'External Request' action sends.

        Expected shape (configured by the business inside ManyChat's flow builder,
        as ManyChat lets you choose which subscriber fields to forward):
        {
          "subscriber_id": "123456",
          "first_name": "Juan",
          "last_name": "Perez",
          "phone": "+5491100000000",
          "email": "juan@example.com",
          "last_input_text": "Hola, quiero info del producto"
        }
        """
        subscriber_id = str(raw_payload.get("subscriber_id") or raw_payload.get("id") or "")
        first_name = raw_payload.get("first_name", "")
        last_name = raw_payload.get("last_name", "")
        sender_name = f"{first_name} {last_name}".strip() or "ManyChat Subscriber"

        return WebhookPayload(
            platform=ChannelPlatform.MANYCHAT,
            external_id=subscriber_id,
            sender_name=sender_name,
            sender_id=subscriber_id,
            sender_phone=raw_payload.get("phone"),
            sender_email=raw_payload.get("email"),
            content=raw_payload.get("last_input_text") or raw_payload.get("text") or "",
            content_type="text",
            extra_data=raw_payload,
        )

    async def validate_credentials(self) -> bool:
        if not self.api_token:
            return False
        try:
            url = f"{self.BASE_URL}/fb/page/getInfo"
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self._headers())
                data = response.json()
                return data.get("status") == "success"
        except Exception:
            return False

    # -- ManyChat-specific (not part of BaseChannelConnector): lead-filtering hooks --

    async def tag_subscriber(self, subscriber_id: str, tag_name: str) -> bool:
        """Tags a subscriber so the business's ManyChat flow can branch on it."""
        if not self.api_token:
            return False
        try:
            url = f"{self.BASE_URL}/fb/subscriber/addTagByName"
            payload = {"subscriber_id": subscriber_id, "tag_name": tag_name}
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self._headers())
                return response.status_code == 200
        except Exception:
            return False

    async def set_custom_field(self, subscriber_id: str, field_name: str, value: Any) -> bool:
        """Sets a ManyChat custom field (e.g. sellia_score) on a subscriber."""
        if not self.api_token:
            return False
        try:
            url = f"{self.BASE_URL}/fb/subscriber/setCustomField"
            payload = {"subscriber_id": subscriber_id, "field_name": field_name, "field_value": value}
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=self._headers())
                return response.status_code == 200
        except Exception:
            return False
