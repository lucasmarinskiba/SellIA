"""Web Chat Widget Connector."""

from datetime import UTC, datetime
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.models import ChannelPlatform
from app.domains.channels.schemas import WebhookPayload


class WebChatConnector(BaseChannelConnector):
    """Conector para el widget de chat web embebido en sitios del usuario."""

    platform = "webchat"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.widget_id = credentials.get("widget_id")
        self.allowed_domains = settings.get("allowed_domains", [])

    async def send_message(
        self, recipient_id: str, content: str, content_type: str = "text"
    ) -> dict[str, Any]:
        """En WebChat, el mensaje se envía via websocket/SSE al frontend.
        Este método retorna el payload para ser entregado por el backend."""
        return {
            "status": "queued",
            "platform": "webchat",
            "recipient_id": recipient_id,
            "content": content,
            "content_type": content_type,
            "timestamp": datetime.now(UTC).isoformat(),
        }

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        return WebhookPayload(
            platform=ChannelPlatform.WEBCHAT,
            external_id=raw_payload.get("visitor_id"),
            sender_name=raw_payload.get("visitor_name", "Visitante"),
            sender_email=raw_payload.get("visitor_email"),
            content=raw_payload.get("message", ""),
            content_type=raw_payload.get("content_type", "text"),
            extra_data=raw_payload,
        )

    async def validate_credentials(self) -> bool:
        return bool(self.widget_id)
