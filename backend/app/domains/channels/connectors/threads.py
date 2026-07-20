"""Threads Connector — Replies and mentions via Meta Threads API."""

import httpx
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform
from app.core.logger import get_logger

logger = get_logger(__name__)


class ThreadsConnector(BaseChannelConnector):
    """Connects to Meta Threads API."""

    platform = "threads"
    BASE_URL = "https://graph.threads.net"
    API_VERSION = "v1.0"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.access_token = credentials.get("access_token")
        self.user_id = credentials.get("user_id")

    def _get_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        if not self.access_token or not self.user_id:
            raise ValueError("Faltan credenciales de Threads (access_token o user_id)")

        # recipient_id is treated as the parent thread ID to reply to
        url = f"{self.BASE_URL}/{self.API_VERSION}/{self.user_id}/replies"
        headers = self._get_headers()
        params = {
            "media_type": "TEXT",
            "text": content,
            "reply_to_id": recipient_id,
            "access_token": self.access_token,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, params=params, timeout=30.0)
            response.raise_for_status()
            data = response.json()
            logger.info("Threads reply sent to %s", recipient_id)
            return data

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        entry = raw_payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        # Threads replies via Meta webhooks
        thread_id = value.get("thread_id", "")
        from_id = value.get("from", {}).get("id", "")
        from_username = value.get("from", {}).get("username", "Threads User")
        message = value.get("message", "")

        if not message:
            # Fallback for mention payload shape
            mention_data = value.get("mention_data", {})
            thread_id = mention_data.get("thread_id", thread_id)
            from_id = mention_data.get("user_id", from_id)
            from_username = mention_data.get("username", from_username)
            message = mention_data.get("text", "")

        return WebhookPayload(
            platform=ChannelPlatform.THREADS,
            external_id=from_id or thread_id,
            sender_name=from_username,
            sender_id=from_id,
            content=message,
            content_type="text",
            extra_data=raw_payload,
        )

    async def validate_credentials(self) -> bool:
        if not self.access_token:
            return False
        try:
            url = f"{self.BASE_URL}/{self.API_VERSION}/me"
            headers = self._get_headers()
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=30.0)
                return response.status_code == 200
        except Exception as exc:
            logger.error("Threads credential validation failed: %s", exc)
            return False
