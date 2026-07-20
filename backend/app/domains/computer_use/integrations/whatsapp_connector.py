"""WhatsApp Business API Connector — Real integration.

Usa Meta WhatsApp Business API para enviar mensajes.
"""

import logging
from typing import Optional, Dict, Any, Tuple
import httpx

logger = logging.getLogger(__name__)


class WhatsAppConnector:
    """Conector real de WhatsApp Business API."""

    API_VERSION = "v18.0"
    BASE_URL = "https://graph.instagram.com"

    def __init__(self, business_account_id: str, access_token: str):
        """
        Inicializa connector.

        business_account_id: WhatsApp Business Account ID
        access_token: Long-lived access token from Meta
        """
        self.business_account_id = business_account_id
        self.access_token = access_token
        self.client = httpx.AsyncClient(
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30.0,
        )

    async def send_text_message(
        self,
        recipient_phone: str,
        message: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Envía mensaje de texto vía WhatsApp.

        Retorna: (success, message_id)
        """
        try:
            url = f"{self.BASE_URL}/{self.API_VERSION}/{self.business_account_id}/messages"

            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_phone,
                "type": "text",
                "text": {"body": message},
            }

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            message_id = result.get("messages", [{}])[0].get("id")

            logger.info(f"WhatsApp message sent: {message_id} to {recipient_phone}")

            return True, message_id

        except httpx.HTTPError as e:
            logger.error(f"WhatsApp API error: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False, None

    async def send_template_message(
        self,
        recipient_phone: str,
        template_name: str,
        template_language: str = "en",
        parameters: Optional[list] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Envía mensaje usando template pre-aprobado.

        Útil para transaccionales, confirmaciones, etc.

        Retorna: (success, message_id)
        """
        try:
            url = f"{self.BASE_URL}/{self.API_VERSION}/{self.business_account_id}/messages"

            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_phone,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": template_language},
                },
            }

            if parameters:
                payload["template"]["components"] = [
                    {"type": "body", "parameters": parameters}
                ]

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            message_id = result.get("messages", [{}])[0].get("id")

            logger.info(f"WhatsApp template sent: {message_id} to {recipient_phone}")

            return True, message_id

        except httpx.HTTPError as e:
            logger.error(f"WhatsApp API error: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error sending template: {e}")
            return False, None

    async def send_media_message(
        self,
        recipient_phone: str,
        media_type: str,  # image, video, document, audio
        media_url: str,
        caption: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Envía media (image, video, documento).

        media_type: image | video | document | audio
        media_url: URL publica del archivo
        caption: Descripción (solo para image y video)

        Retorna: (success, message_id)
        """
        try:
            url = f"{self.BASE_URL}/{self.API_VERSION}/{self.business_account_id}/messages"

            payload = {
                "messaging_product": "whatsapp",
                "to": recipient_phone,
                "type": media_type,
                media_type: {
                    "link": media_url,
                },
            }

            if caption and media_type in ("image", "video"):
                payload[media_type]["caption"] = caption

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            result = response.json()
            message_id = result.get("messages", [{}])[0].get("id")

            logger.info(f"WhatsApp media sent: {message_id} to {recipient_phone}")

            return True, message_id

        except httpx.HTTPError as e:
            logger.error(f"WhatsApp API error: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error sending media: {e}")
            return False, None

    async def mark_message_read(self, message_id: str) -> bool:
        """Marca mensaje como leído."""
        try:
            url = f"{self.BASE_URL}/{self.API_VERSION}/{message_id}"

            payload = {"status": "read"}

            response = await self.client.post(url, json=payload)
            response.raise_for_status()

            logger.info(f"Message marked as read: {message_id}")

            return True

        except Exception as e:
            logger.error(f"Error marking message as read: {e}")
            return False

    async def close(self):
        """Cierra la conexión HTTP."""
        await self.client.aclose()


def get_whatsapp_connector(
    business_account_id: str,
    access_token: str,
) -> WhatsAppConnector:
    """Factory para obtener connector."""
    return WhatsAppConnector(business_account_id, access_token)
