"""TikTok Shop Connector — envuelve TikTokShopAutomation (código real, ya
existía en app/core/integrations/tiktok_shop_automation.py pero nunca se
conectó al CONNECTOR_REGISTRY ni a la API pública). Órdenes/catálogo/
fulfillment reales vía TikTok Seller API, no simulado.
"""
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform
from app.core.integrations.tiktok_shop_automation import TikTokShopAutomation, TikTokFulfillmentType


class TikTokShopConnector(BaseChannelConnector):
    """Conector para TikTok Shop Seller API (órdenes, catálogo, fulfillment)."""
    platform = "tiktok_shop"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self._automation = TikTokShopAutomation(
            shop_id=credentials.get("shop_id", ""),
            shop_cipher=credentials.get("shop_cipher", ""),
            access_token=credentials.get("access_token", ""),
            refresh_token=credentials.get("refresh_token"),
            webhook_verify_token=credentials.get("webhook_verify_token"),
        )
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        """TikTok Shop no tiene buyer messaging vía este connector; se usa order-status updates."""
        raise NotImplementedError(
            "TikTok Shop Seller API no expone buyer-messaging genérico en esta integración. "
            "Usar confirm_order/update_tracking para comunicar estado de la orden."
        )

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        data = raw_payload.get("data", {})
        event_type = raw_payload.get("type", "unknown")
        order_id = data.get("order_id", "")

        return WebhookPayload(
            platform=ChannelPlatform.TIKTOK_SHOP,
            external_id=order_id or raw_payload.get("shop_id", "unknown"),
            sender_id=order_id,
            sender_name="TikTok Shop",
            content=f"TikTok Shop {event_type}: {data.get('order_status', data)}",
            content_type=event_type,
            extra_data=raw_payload,
        )

    async def validate_credentials(self) -> bool:
        if not self._automation.access_token or not self._automation.shop_id:
            return False
        result = await self._automation.list_orders(page=1, page_size=1)
        return result is not None

    async def verify_webhook_signature(self, payload_body: bytes, signature: str) -> bool:
        return self._automation.verify_webhook_signature(payload_body, signature)

    async def handle_webhook_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._automation.handle_webhook(payload)

    async def list_orders(self, page: int = 1, page_size: int = 20, status_filter: list[str] | None = None):
        return await self._automation.list_orders(page, page_size, status_filter)

    async def get_order_details(self, order_id: str):
        return await self._automation.get_order_details(order_id)

    async def sync_products_to_tiktok(self, products: list[dict[str, Any]]) -> dict[str, Any]:
        return await self._automation.sync_products_to_tiktok(products)

    async def update_inventory(self, product_id: str, quantity: int) -> bool:
        return await self._automation.update_inventory(product_id, quantity)

    async def create_shipment(
        self, order_id: str, tracking_number: str, carrier: str,
        fulfillment_type: str = "seller_fulfillment",
    ) -> bool:
        ft = (
            TikTokFulfillmentType.TIKTOK_SHOP_FULFILLMENT
            if fulfillment_type == "tiktok_shop_fulfillment"
            else TikTokFulfillmentType.SELLER_FULFILLMENT
        )
        tracking_info = {"tracking_number": tracking_number, "carrier": carrier}
        return await self._automation.create_shipment(order_id, ft, tracking_info)

    async def refresh_access_token(self) -> dict[str, Any] | None:
        if not self.client_id or not self.client_secret:
            raise ValueError("Faltan client_id/client_secret de TikTok Shop para refrescar el token")
        return await self._automation.refresh_access_token(self.client_id, self.client_secret)
