"""WhatsApp Business connector — Mensajes automáticos."""

import aiohttp, logging
from typing import Dict, List, Any
from .base_connector import BaseConnector, ConnectorType

logger = logging.getLogger(__name__)


class WhatsAppConnector(BaseConnector):
    """WhatsApp Business API integration."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("whatsapp", ConnectorType.MESSAGING, config)
        self.base_url = "https://graph.instagram.com/v18.0"
        self.access_token = config.get("access_token")
        self.phone_number_id = config.get("phone_number_id")

    async def authenticate(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.phone_number_id}"
                async with session.get(url, params={"access_token": self.access_token}) as resp:
                    if resp.status == 200:
                        self.authenticated = True
                        return True
                    return False
        except Exception as e:
            logger.error(f"WhatsApp auth failed: {str(e)}")
            return False

    async def send_message(self, recipient: str, message: str) -> Dict[str, Any]:
        """Envía mensaje WhatsApp."""
        try:
            payload = {
                "messaging_product": "whatsapp",
                "to": recipient,
                "type": "text",
                "text": {"body": message},
            }

            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.phone_number_id}/messages"
                async with session.post(url, json=payload, params={"access_token": self.access_token}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"WhatsApp message sent: {data.get('messages', [{}])[0].get('id')}")
                        return {"status": "sent", "message_id": data.get("messages", [{}])[0].get("id")}
                    return {"status": "error"}
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def list_products(self) -> List[Dict[str, Any]]:
        return []
    
    async def create_listing(self, product: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "not_applicable"}
    
    async def get_orders(self) -> List[Dict[str, Any]]:
        return []
    
    async def create_campaign(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        return {"status": "not_applicable"}
    
    async def get_metrics(self) -> Dict[str, Any]:
        return {}
