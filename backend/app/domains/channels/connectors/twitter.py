"""X (Twitter) Connector — DMs, mentions, replies."""

import asyncio
import httpx
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform
from app.core.logger import get_logger

logger = get_logger(__name__)


class XConnector(BaseChannelConnector):
    """Connects to X (Twitter) API v2 for DMs and mentions."""

    platform = "twitter"
    BASE_URL = "https://api.twitter.com/2"
    MAX_RETRIES = 3
    BASE_BACKOFF = 1.0

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.bearer_token = credentials.get("bearer_token")
        self.api_key = credentials.get("api_key")
        self.api_secret = credentials.get("api_secret")
        self.access_token = credentials.get("access_token")
        self.access_secret = credentials.get("access_secret")

    def _get_bearer_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.bearer_token}",
            "Content-Type": "application/json",
        }

    async def _request_with_backoff(
        self,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        last_exception: Exception | None = None
        for attempt in range(self.MAX_RETRIES):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.request(
                        method, url, headers=headers, json=json, timeout=30.0
                    )
                if response.status_code == 429:
                    retry_after = int(response.headers.get("retry-after", "2"))
                    wait = retry_after if retry_after else (self.BASE_BACKOFF * (2**attempt))
                    logger.warning("X rate limit hit, waiting %ss before retry %s/%s", wait, attempt + 1, self.MAX_RETRIES)
                    await asyncio.sleep(wait)
                    continue
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code >= 500:
                    wait = self.BASE_BACKOFF * (2**attempt)
                    logger.warning("X server error %s, retrying in %ss (%s/%s)", exc.response.status_code, wait, attempt + 1, self.MAX_RETRIES)
                    await asyncio.sleep(wait)
                    last_exception = exc
                    continue
                raise
            except httpx.RequestError as exc:
                wait = self.BASE_BACKOFF * (2**attempt)
                logger.warning("X request error, retrying in %ss (%s/%s): %s", wait, attempt + 1, self.MAX_RETRIES, exc)
                await asyncio.sleep(wait)
                last_exception = exc
        if last_exception:
            raise last_exception
        raise RuntimeError("Max retries exceeded for X API request")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        if not self.bearer_token:
            raise ValueError("Faltan credenciales de X (bearer_token)")

        url = f"{self.BASE_URL}/dm_conversations/with/{recipient_id}/messages"
        headers = self._get_bearer_headers()
        payload: dict[str, Any] = {"text": content}
        if content_type != "text":
            payload["attachments"] = [{"media_key": content}]

        response = await self._request_with_backoff("POST", url, headers=headers, json=payload)
        data = response.json()
        logger.info("X DM sent to %s", recipient_id)
        return data

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        event_type = raw_payload.get("event_type")

        if event_type == "dm_event":
            dm = raw_payload.get("dm_event", {})
            sender = raw_payload.get("users", {}).get(dm.get("sender_id"), {})
            message_create = dm.get("message_create", {})
            text = message_create.get("message_data", {}).get("text", "")
            return WebhookPayload(
                platform=ChannelPlatform.TWITTER,
                external_id=dm.get("sender_id"),
                sender_name=sender.get("name", "X User"),
                sender_id=dm.get("sender_id"),
                content=text,
                content_type="text",
                extra_data=raw_payload,
            )

        if event_type in ("tweet_create", "mention"):
            tweet = raw_payload.get("tweet_create_events", [{}])[0]
            user = tweet.get("user", {})
            text = tweet.get("text", "")
            return WebhookPayload(
                platform=ChannelPlatform.TWITTER,
                external_id=str(user.get("id")),
                sender_name=user.get("name", "X User"),
                sender_id=str(user.get("id")),
                content=text,
                content_type="mention",
                extra_data=raw_payload,
            )

        # Fallback: try unified X API v2 format
        data = raw_payload.get("data", {})
        includes = raw_payload.get("includes", {})
        users = includes.get("users", [])
        sender = users[0] if users else {}
        text = data.get("text", "")
        return WebhookPayload(
            platform=ChannelPlatform.TWITTER,
            external_id=data.get("author_id", sender.get("id", "")),
            sender_name=sender.get("name", "X User"),
            sender_id=data.get("author_id", sender.get("id", "")),
            content=text,
            content_type="text",
            extra_data=raw_payload,
        )

    async def validate_credentials(self) -> bool:
        if not self.bearer_token:
            return False
        try:
            url = f"{self.BASE_URL}/users/me"
            headers = self._get_bearer_headers()
            response = await self._request_with_backoff("GET", url, headers=headers)
            return response.status_code == 200
        except Exception as exc:
            logger.error("X credential validation failed: %s", exc)
            return False

    async def get_user_profile(self, username: str) -> dict[str, Any]:
        if not self.bearer_token:
            raise ValueError("Faltan credenciales de X (bearer_token)")

        url = f"{self.BASE_URL}/users/by/username/{username}"
        headers = self._get_bearer_headers()
        response = await self._request_with_backoff("GET", url, headers=headers)
        data = response.json()
        logger.info("X user profile fetched for @%s", username)
        return data.get("data", {})
