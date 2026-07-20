import httpx
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class WhatsAppConnector(BaseChannelConnector):
    platform = "whatsapp"
    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.api_token = credentials.get("api_token")
        self.phone_number_id = credentials.get("phone_number_id")
        self.business_account_id = credentials.get("business_account_id")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        if not self.api_token or not self.phone_number_id:
            raise ValueError("Faltan credenciales de WhatsApp Business API")

        url = f"{self.BASE_URL}/{self.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient_id,
            "type": content_type,
            "text": {"body": content},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        entry = raw_payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            raise ValueError("No hay mensajes en el payload")

        msg = messages[0]
        sender = value.get("contacts", [{}])[0]

        return WebhookPayload(
            platform=ChannelPlatform.WHATSAPP,
            external_id=msg.get("from"),
            sender_name=sender.get("profile", {}).get("name"),
            sender_phone=msg.get("from"),
            content=msg.get("text", {}).get("body", ""),
            content_type="text",
            extra_data=raw_payload,
        )

    async def validate_credentials(self) -> bool:
        if not self.api_token or not self.phone_number_id:
            return False
        try:
            url = f"{self.BASE_URL}/{self.phone_number_id}"
            headers = {"Authorization": f"Bearer {self.api_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception:
            return False
