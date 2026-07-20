"""Instagram Messaging Connector — Real DMs via Meta API.

Envía mensajes directos en Instagram (similar a WhatsApp pero en IG).
"""

import logging
from typing import Optional, Tuple
import httpx

logger = logging.getLogger(__name__)


class InstagramConnector:
    """Conector para Instagram DMs via Meta API."""

    API_VERSION = "v18.0"
    BASE_URL = "https://graph.instagram.com"

    def __init__(self, business_account_id: str, access_token: str):
        """
        business_account_id: Instagram Business Account ID
        access_token: Meta access token (instagram_manage_messages scope)
        """
        self.business_account_id = business_account_id
        self.access_token = access_token
        self.client = httpx.AsyncClient(timeout=30.0)

    async def send_text_message(
        self,
        recipient_id: str,
        message: str,
    ) -> Tuple[bool, Optional[str]]:
        """Envía texto por DM en Instagram."""
        try:
            url = f"{self.BASE_URL}/{self.API_VERSION}/{self.business_account_id}/messages"

            params = {"access_token": self.access_token}

            data = {
                "recipient": {"id": recipient_id},
                "message": {"text": message},
            }

            response = await self.client.post(url, params=params, json=data)
            response.raise_for_status()

            result = response.json()
            message_id = result.get("message_id")

            logger.info(f"Instagram message sent: {message_id}")

            return True, message_id

        except Exception as e:
            logger.error(f"Error sending Instagram message: {e}")
            return False, None

    async def send_media_message(
        self,
        recipient_id: str,
        media_type: str,  # image, video
        media_url: str,
    ) -> Tuple[bool, Optional[str]]:
        """Envía media por DM."""
        try:
            url = f"{self.BASE_URL}/{self.API_VERSION}/{self.business_account_id}/messages"

            params = {"access_token": self.access_token}

            data = {
                "recipient": {"id": recipient_id},
                media_type: {"url": media_url},
            }

            response = await self.client.post(url, params=params, json=data)
            response.raise_for_status()

            result = response.json()
            message_id = result.get("message_id")

            logger.info(f"Instagram media sent: {message_id}")

            return True, message_id

        except Exception as e:
            logger.error(f"Error sending Instagram media: {e}")
            return False, None

    async def close(self):
        await self.client.aclose()


def get_instagram_connector(
    business_account_id: str,
    access_token: str,
) -> InstagramConnector:
    return InstagramConnector(business_account_id, access_token)
