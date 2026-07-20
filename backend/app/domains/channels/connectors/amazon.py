"""Amazon Seller Central / Selling Partner API Connector.

Handles order notifications, inventory updates, and buyer messages.
Docs: https://developer-docs.amazon.com/sp-api/docs
"""

import hmac
import hashlib
import base64
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class AmazonSellerConnector(BaseChannelConnector):
    """Conector para Amazon Selling Partner API (SP-API)."""
    platform = "amazon"
    BASE_URL = "https://sellingpartnerapi-na.amazon.com"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.refresh_token = credentials.get("refresh_token")
        self.lwa_app_id = credentials.get("lwa_app_id")
        self.lwa_client_secret = credentials.get("lwa_client_secret")
        self.aws_access_key = credentials.get("aws_access_key")
        self.aws_secret_key = credentials.get("aws_secret_key")
        self.role_arn = credentials.get("role_arn")
        self.marketplace_id = credentials.get("marketplace_id", "ATVPDKIKX0DER")
        self.seller_id = credentials.get("seller_id")
        self.access_token = credentials.get("access_token")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        """Send buyer-seller messaging via SP-API."""
        if not self.access_token:
            raise ValueError("Falta access_token de Amazon")

        import httpx
        url = f"{self.BASE_URL}/messaging/v1/orders/{recipient_id}/messages"
        headers = {
            "x-amz-access-token": self.access_token,
            "Content-Type": "application/json",
        }
        payload = {"text": content}

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        """Parse Amazon SP-API notification payload.
        
        Amazon SNS sends notifications with structure:
        {
            "NotificationType": "ORDER_CHANGE",
            "Payload": {
                "OrderChangeNotification": {
                    "SellerId": "...",
                    "MarketplaceId": "...",
                    "OrderChange": {
                        "OrderId": "...",
                        "BuyerEmail": "...",
                        "PurchaseDate": "...",
                        "OrderStatus": "Shipped",
                        "OrderItems": [...]
                    }
                }
            }
        }
        """
        notification_type = raw_payload.get("NotificationType", "")
        payload = raw_payload.get("Payload", {})

        if notification_type == "ORDER_CHANGE":
            order_change = payload.get("OrderChangeNotification", {}).get("OrderChange", {})
            order_id = order_change.get("OrderId", "")
            buyer_email = order_change.get("BuyerEmail", "")
            order_status = order_change.get("OrderStatus", "")
            order_items = order_change.get("OrderItems", [])
            
            items_text = ", ".join([item.get("Title", "") for item in order_items[:3]]) if order_items else ""
            
            content = f"Pedido Amazon {order_id}: {order_status}"
            if items_text:
                content += f"\nProductos: {items_text}"

            return WebhookPayload(
                platform=ChannelPlatform.AMAZON,
                external_id=order_id,
                sender_id=buyer_email or order_id,
                sender_name="Comprador Amazon",
                sender_email=buyer_email,
                content=content,
                content_type="order",
                extra_data=raw_payload,
            )

        elif notification_type == "BUYER_MESSAGE":
            msg = payload.get("BuyerMessageNotification", {}).get("BuyerMessage", {})
            order_id = msg.get("OrderId", "")
            buyer_email = msg.get("BuyerEmail", "")
            message = msg.get("Message", "")

            return WebhookPayload(
                platform=ChannelPlatform.AMAZON,
                external_id=order_id,
                sender_id=buyer_email or order_id,
                sender_name="Comprador Amazon",
                sender_email=buyer_email,
                content=message or f"Nuevo mensaje de comprador - Pedido {order_id}",
                content_type="text",
                extra_data=raw_payload,
            )

        elif notification_type == "FEED_PROCESSING_FINISHED":
            feed = payload.get("FeedProcessingFinishedNotification", {}).get("FeedProcessingFinished", {})
            feed_id = feed.get("FeedId", "")
            
            return WebhookPayload(
                platform=ChannelPlatform.AMAZON,
                external_id=feed_id,
                sender_name="Amazon",
                content=f"Feed procesado: {feed_id}",
                content_type="system",
                extra_data=raw_payload,
            )

        # Generic fallback
        return WebhookPayload(
            platform=ChannelPlatform.AMAZON,
            external_id=str(raw_payload.get("SellerId", "unknown")),
            sender_name="Amazon",
            content=f"Notificación: {notification_type}",
            content_type="system",
            extra_data=raw_payload,
        )

    async def _refresh_access_token(self) -> str:
        """Refresh LWA access token using refresh_token."""
        if not self.refresh_token or not self.lwa_app_id or not self.lwa_client_secret:
            raise ValueError("Faltan credenciales LWA para refrescar token")
        
        import httpx
        url = "https://api.amazon.com/auth/o2/token"
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "client_id": self.lwa_app_id,
            "client_secret": self.lwa_client_secret,
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=payload)
            response.raise_for_status()
            data = response.json()
            self.access_token = data["access_token"]
            return self.access_token

    async def _get_sp_api_headers(self) -> dict[str, str]:
        """Return headers for SP-API requests."""
        if not self.access_token:
            await self._refresh_access_token()
        return {
            "x-amz-access-token": self.access_token,
            "Content-Type": "application/json",
        }

    async def get_orders(self, created_after: str | None = None) -> list[dict[str, Any]]:
        """Fetch orders from SP-API."""
        import httpx
        headers = await self._get_sp_api_headers()
        params = {"MarketplaceIds": self.marketplace_id}
        if created_after:
            params["CreatedAfter"] = created_after
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/orders/v0/orders",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            return response.json().get("payload", {}).get("Orders", [])

    async def get_order_items(self, order_id: str) -> list[dict[str, Any]]:
        """Fetch items for a specific order."""
        import httpx
        headers = await self._get_sp_api_headers()
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/orders/v0/orders/{order_id}/orderItems",
                headers=headers,
            )
            response.raise_for_status()
            return response.json().get("payload", {}).get("OrderItems", [])

    async def get_inventory(self) -> list[dict[str, Any]]:
        """Fetch FBA inventory summaries."""
        import httpx
        headers = await self._get_sp_api_headers()
        params = {"details": "true", "granularityType": "Marketplace", "granularityId": self.marketplace_id}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/fba/inventory/v1/summaries",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            return response.json().get("payload", {}).get("inventorySummaries", [])

    async def push_catalog_item(self, item: Any) -> dict[str, Any]:
        """Push a CatalogItem to Amazon via SP-API feeds (simplified)."""
        import httpx
        headers = await self._get_sp_api_headers()
        payload = {
            "productType": item.extra_data.get("product_type", "PRODUCT"),
            "requirements": "LISTING",
            "attributes": {
                "item_name": [{"value": item.name}],
                "brand": [{"value": item.brand or "Generic"}],
                "bullet_point": [{"value": b} for b in (item.description or "").split("\n") if b],
            },
        }
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.BASE_URL}/listings/2021-08-01/items/{self.seller_id}/{item.sku or item.id}",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def pull_catalog_items(self) -> list[dict[str, Any]]:
        """Pull catalog items from Amazon via SP-API search."""
        import httpx
        headers = await self._get_sp_api_headers()
        params = {"marketplaceIds": self.marketplace_id, "includedData": "summaries,attributes"}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.BASE_URL}/catalog/2022-04-01/items",
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            return response.json().get("items", [])

    async def validate_credentials(self) -> bool:
        if not self.access_token and self.refresh_token:
            try:
                await self._refresh_access_token()
            except Exception:
                return False
        if not self.access_token:
            return False
        try:
            import httpx
            url = f"{self.BASE_URL}/sellers/v1/marketplaceParticipations"
            headers = {"x-amz-access-token": self.access_token}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception:
            return False
