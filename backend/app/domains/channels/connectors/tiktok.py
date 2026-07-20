"""TikTok Organic Connector.

Handles TikTok direct messages (DMs) and comment webhooks.
Docs: https://developers.tiktok.com/doc/webhooks-webhook
"""

from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class TikTokConnector(BaseChannelConnector):
    """Conector para TikTok organic (DMs y comentarios)."""
    platform = "tiktok"
    BASE_URL = "https://open.tiktokapis.com"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.access_token = credentials.get("access_token")
        self.open_id = credentials.get("open_id")
        self.webhook_secret = credentials.get("webhook_secret")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        """TikTok DM messaging requires TikTok For Business API partnership.
        For most creators, direct messaging is not available via API.
        """
        import httpx
        if not self.access_token:
            raise ValueError("Falta access_token de TikTok")

        url = f"{self.BASE_URL}/api/im/message/send/"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "open_id": recipient_id,
            "message_type": "text",
            "content": {"text": content},
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 403:
                return {"status": "failed", "note": "TikTok DM API requiere permisos especiales"}
            response.raise_for_status()
            return response.json()

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        """Parse TikTok webhook payload.

        TikTok webhooks for DMs:
        {
            "event": "direct_message",
            "sender": {"open_id": "xxx", "nickname": "User"},
            "message": {"message_id": "xxx", "content": {"text": "Hola"}}
        }
        """
        event_type = raw_payload.get("event", "")

        if event_type == "direct_message":
            sender = raw_payload.get("sender", {})
            message = raw_payload.get("message", {})
            content = message.get("content", {})
            text = content.get("text", "")

            return WebhookPayload(
                platform=ChannelPlatform.TIKTOK,
                external_id=sender.get("open_id", "unknown"),
                sender_name=sender.get("nickname", "Usuario TikTok"),
                content=text or "Nuevo mensaje de TikTok",
                content_type="text",
                extra_data=raw_payload,
            )

        elif event_type == "comment":
            comment = raw_payload.get("comment", {})
            user = raw_payload.get("user", {})
            return WebhookPayload(
                platform=ChannelPlatform.TIKTOK,
                external_id=user.get("open_id", "unknown"),
                sender_name=user.get("nickname", "Usuario TikTok"),
                content=comment.get("text", "Nuevo comentario en TikTok"),
                content_type="comment",
                extra_data=raw_payload,
            )

        # Generic fallback
        return WebhookPayload(
            platform=ChannelPlatform.TIKTOK,
            external_id=raw_payload.get("open_id", "unknown"),
            sender_name="Usuario TikTok",
            content=f"Evento de TikTok: {event_type}",
            content_type="system",
            extra_data=raw_payload,
        )

    async def validate_credentials(self) -> bool:
        if not self.access_token:
            return False
        try:
            import httpx
            url = f"{self.BASE_URL}/api/user/info/"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception:
            return False
