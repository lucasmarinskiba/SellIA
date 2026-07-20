"""MercadoLibre Connector.

Handles buyer messages via MercadoLibre Messaging API and order notifications.
Docs: https://developers.mercadolibre.com.ar/
"""

import httpx
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class MercadoLibreConnector(BaseChannelConnector):
    """Conector para MercadoLibre mensajes y notificaciones de ventas."""
    platform = "mercadolibre"
    BASE_URL = "https://api.mercadolibre.com"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.access_token = credentials.get("access_token")
        self.refresh_token = credentials.get("refresh_token")
        self.seller_id = credentials.get("seller_id")
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        if not self.access_token:
            raise ValueError("Falta access_token de MercadoLibre")

        # MercadoLibre messaging API: POST /messages
        # recipient_id is typically the order_id or buyer_id + item combination
        url = f"{self.BASE_URL}/messages"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        payload = {
            "from": {"user_id": self.seller_id},
            "to": {"user_id": recipient_id},
            "text": content,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        """Parse MercadoLibre notification payload.
        
        ML sends topics like:
        - messages: new buyer message
        - orders: new order, payment, shipping update
        - questions: product question
        """
        topic = raw_payload.get("topic", "")
        resource = raw_payload.get("resource", "")
        user_id = raw_payload.get("user_id")

        # Try to extract data from the resource URL or nested data
        data = raw_payload.get("data", {})
        
        if topic == "messages" or "messages" in resource:
            # Message notification
            message_data = data.get("message", {})
            from_data = message_data.get("from", {})
            to_data = message_data.get("to", {})
            
            # Determine if this is inbound (from buyer to seller)
            from_user_id = str(from_data.get("user_id", ""))
            is_inbound = from_user_id != str(self.seller_id) if self.seller_id else True
            
            if is_inbound:
                return WebhookPayload(
                    platform=ChannelPlatform.MERCADOLIBRE,
                    external_id=from_user_id,
                    sender_id=from_user_id,
                    sender_name=from_data.get("name", "Comprador ML"),
                    content=message_data.get("text", ""),
                    content_type="text",
                    extra_data=raw_payload,
                )
        
        elif topic == "questions" or "questions" in resource:
            # Product question
            question_data = data.get("question", {})
            from_data = question_data.get("from", {})
            
            return WebhookPayload(
                platform=ChannelPlatform.MERCADOLIBRE,
                external_id=str(from_data.get("id", user_id or "unknown")),
                sender_id=str(from_data.get("id", "")),
                sender_name=from_data.get("name", "Comprador ML"),
                content=question_data.get("text", ""),
                content_type="text",
                extra_data=raw_payload,
            )
        
        elif topic == "orders" or "orders" in resource:
            # Order notification - create a system message
            order_data = data.get("order", {})
            buyer_data = order_data.get("buyer", {})
            order_id = order_data.get("id", "")
            
            return WebhookPayload(
                platform=ChannelPlatform.MERCADOLIBRE,
                external_id=str(buyer_data.get("id", user_id or "unknown")),
                sender_id=str(buyer_data.get("id", "")),
                sender_name=buyer_data.get("nickname", "Comprador ML"),
                content=f"Nueva orden #{order_id} en MercadoLibre",
                content_type="system",
                extra_data=raw_payload,
            )

        # Generic fallback
        return WebhookPayload(
            platform=ChannelPlatform.MERCADOLIBRE,
            external_id=str(user_id or "unknown"),
            sender_name="MercadoLibre",
            content=f"Notificación: {topic}",
            content_type="system",
            extra_data=raw_payload,
        )

    async def validate_credentials(self) -> bool:
        if not self.access_token:
            return False
        try:
            url = f"{self.BASE_URL}/users/me"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception:
            return False
