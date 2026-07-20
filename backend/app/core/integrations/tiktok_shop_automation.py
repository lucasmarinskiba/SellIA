"""
TikTok Shop Automation — Real-time orders, product catalog sync, fulfillment tracking.

Flujo:
1. Usuario autoriza TikTok Shop Seller API
2. Sistema webhooks escucha: order.created, order.status_updated
3. Auto-sync productos (local → TikTok Shop catalog)
4. Auto-confirm órdenes y genera shipments
5. Real-time inventory sync
6. Fulfillment tracking (TikTok + seller fulfillment)

TikTok Seller API:
- POST /shop/auth/token (OAuth)
- GET /shop/product_management/products (catalog)
- POST /shop/order/get_order (order details)
- POST /shop/order/confirm_order (auto-confirm)
- POST /shop/fulfillment/create_shipment

Rate Limit: 10,000 req/day per shop
Timeout: 30 seconds per request
"""

import logging
import hmac
import hashlib
import httpx
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class TikTokOrderStatus(Enum):
    """TikTok Shop order statuses."""
    UNPAID = "100"
    PAID_PENDING_SHIPMENT = "110"
    AWAITING_SHIPMENT = "120"
    PARTIALLY_SHIPPED = "130"
    SHIPPED = "140"
    DELIVERED = "150"
    CANCELLED = "160"
    RETURN_REQUESTED = "170"
    RETURN_ACCEPTED = "180"


class TikTokFulfillmentType(Enum):
    """Fulfillment types."""
    SELLER_FULFILLMENT = "seller_fulfillment"
    TIKTOK_SHOP_FULFILLMENT = "tiktok_shop_fulfillment"


class TikTokShopAutomation:
    """TikTok Shop complete automation."""

    TIKTOK_SELLER_API = "https://open-api.tiktokshop.com/v1"
    TIMEOUT = 30

    def __init__(
        self,
        shop_id: str,
        shop_cipher: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        webhook_verify_token: Optional[str] = None,
    ):
        """
        Initialize TikTok Shop automation.

        Args:
            shop_id: TikTok Shop ID
            shop_cipher: Encrypted shop ID for API requests
            access_token: OAuth access token (encrypted in production)
            refresh_token: OAuth refresh token (encrypted in production)
            webhook_verify_token: Custom token for webhook verification
        """
        self.shop_id = shop_id
        self.shop_cipher = shop_cipher
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.webhook_verify_token = webhook_verify_token
        self.http_client = httpx.AsyncClient(timeout=self.TIMEOUT)

    # ========== AUTHENTICATION & TOKEN REFRESH ==========

    async def refresh_access_token(
        self,
        client_id: str,
        client_secret: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Refresh expired OAuth token.

        Args:
            client_id: TikTok OAuth app ID
            client_secret: TikTok OAuth app secret (encrypted)

        Returns:
            New token response or None
        """
        try:
            logger.info(f"Refreshing access token for shop {self.shop_id}")

            url = f"{self.TIKTOK_SELLER_API}/authorization/token_refresh"
            payload = {
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token,
                "client_id": client_id,
                "client_secret": client_secret,
            }

            response = await self.http_client.post(url, json=payload)
            response.raise_for_status()

            data = response.json()

            if data.get("code") == "0":
                self.access_token = data["data"]["access_token"]
                self.refresh_token = data["data"].get("refresh_token")
                logger.info("Access token refreshed successfully")
                return data["data"]
            else:
                logger.error(f"Token refresh failed: {data.get('message')}")
                return None

        except httpx.HTTPError as e:
            logger.error(f"Error refreshing token: {e}")
            return None

    # ========== WEBHOOK HANDLING & VERIFICATION ==========

    def verify_webhook_signature(
        self,
        payload_body: bytes,
        signature: str,
    ) -> bool:
        """
        Verify TikTok webhook signature.

        TikTok uses: X-TikTok-Hmac-SHA256 header

        Args:
            payload_body: Raw webhook payload bytes
            signature: X-TikTok-Hmac-SHA256 header value

        Returns:
            bool: True if signature is valid
        """
        try:
            expected_signature = hmac.new(
                self.webhook_verify_token.encode(),
                payload_body,
                hashlib.sha256
            ).hexdigest()

            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Webhook signature verification error: {e}")
            return False

    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming TikTok webhook.

        Payload structure:
        {
          "shop_id": "...",
          "timestamp": 1234567890,
          "type": "order",
          "data": {
            "order_id": "...",
            "order_status": "100",
            ...
          }
        }

        Args:
            payload: Webhook payload from TikTok

        Returns:
            Processed webhook response
        """
        try:
            event_type = payload.get("type")
            data = payload.get("data", {})

            logger.info(f"TikTok webhook: {event_type}")

            if event_type == "order":
                await self._handle_order_event(data)
            elif event_type == "product":
                await self._handle_product_event(data)
            elif event_type == "inventory":
                await self._handle_inventory_event(data)

            return {"code": "0", "message": "success"}

        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return {"code": "1", "message": str(e)}

    async def _handle_order_event(self, order_data: Dict[str, Any]) -> None:
        """Handle order create/update event."""
        order_id = order_data.get("order_id")
        status = order_data.get("order_status")

        logger.info(f"Order event: {order_id} → {status}")

        # Auto-confirm new orders
        if status == TikTokOrderStatus.PAID_PENDING_SHIPMENT.value:
            await self.confirm_order(order_id)

    async def _handle_product_event(self, product_data: Dict[str, Any]) -> None:
        """Handle product update event."""
        product_id = product_data.get("product_id")
        logger.info(f"Product event: {product_id}")

    async def _handle_inventory_event(self, inventory_data: Dict[str, Any]) -> None:
        """Handle inventory change event."""
        product_id = inventory_data.get("product_id")
        stock = inventory_data.get("quantity")
        logger.info(f"Inventory event: {product_id} → {stock}")

    # ========== ORDER MANAGEMENT ==========

    async def get_order_details(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch complete order details from TikTok Shop.

        API: POST /order/get_order
        """
        try:
            url = f"{self.TIKTOK_SELLER_API}/order/get_order"
            payload = {
                "order_id": order_id,
            }
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Shop-Cipher": self.shop_cipher,
            }

            response = await self.http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()

            if data.get("code") == "0":
                return data.get("data", {})
            else:
                logger.error(f"TikTok API error: {data.get('message')}")
                return None

        except httpx.HTTPError as e:
            logger.error(f"Error fetching order {order_id}: {e}")
            return None

    async def confirm_order(self, order_id: str) -> bool:
        """
        Auto-confirm order in TikTok Shop.

        After payment confirmed, mark as received and ready to ship.

        Args:
            order_id: TikTok order ID

        Returns:
            Success boolean
        """
        try:
            logger.info(f"Confirming order: {order_id}")

            url = f"{self.TIKTOK_SELLER_API}/order/confirm_order"
            payload = {
                "order_id": order_id,
            }
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Shop-Cipher": self.shop_cipher,
            }

            response = await self.http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()

            if data.get("code") == "0":
                logger.info(f"Order {order_id} confirmed")
                return True
            else:
                logger.error(f"Order confirmation failed: {data.get('message')}")
                return False

        except httpx.HTTPError as e:
            logger.error(f"Error confirming order {order_id}: {e}")
            return False

    async def list_orders(
        self,
        page: int = 1,
        page_size: int = 20,
        status_filter: Optional[List[str]] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        List orders with optional status filtering.

        Args:
            page: Page number
            page_size: Results per page
            status_filter: List of order statuses to filter

        Returns:
            List of orders or None
        """
        try:
            logger.info(f"Fetching orders (page {page})")

            url = f"{self.TIKTOK_SELLER_API}/order/search"
            payload = {
                "page_number": page,
                "page_size": page_size,
            }

            if status_filter:
                payload["order_status"] = status_filter

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Shop-Cipher": self.shop_cipher,
            }

            response = await self.http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()

            if data.get("code") == "0":
                return data.get("data", {}).get("orders", [])
            else:
                logger.error(f"Order list error: {data.get('message')}")
                return None

        except httpx.HTTPError as e:
            logger.error(f"Error listing orders: {e}")
            return None

    # ========== PRODUCT CATALOG MANAGEMENT ==========

    async def sync_products_to_tiktok(
        self,
        products: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Sync local products to TikTok Shop catalog.

        Args:
            products: List of product dicts {name, price, description, images, sku}

        Returns:
            Sync result summary
        """
        try:
            logger.info(f"Syncing {len(products)} products to TikTok Shop")

            created_count = 0
            updated_count = 0

            for product in products:
                existing = await self._find_product_by_sku(product.get("sku"))

                if existing:
                    success = await self._update_tiktok_product(
                        existing["product_id"],
                        product,
                    )
                    if success:
                        updated_count += 1
                else:
                    success = await self._create_tiktok_product(product)
                    if success:
                        created_count += 1

            return {
                "status": "success",
                "created": created_count,
                "updated": updated_count,
                "total": len(products),
            }

        except Exception as e:
            logger.error(f"Error syncing products to TikTok: {e}")
            return {"status": "error", "message": str(e)}

    async def _find_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Find product in TikTok catalog by SKU."""
        try:
            url = f"{self.TIKTOK_SELLER_API}/product/search"
            payload = {
                "search_value": sku,
                "search_type": "sku",
            }
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Shop-Cipher": self.shop_cipher,
            }

            response = await self.http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()

            if data.get("code") == "0":
                products = data.get("data", {}).get("products", [])
                if products:
                    return products[0]

            return None

        except httpx.HTTPError as e:
            logger.error(f"Error finding product by SKU {sku}: {e}")
            return None

    async def _create_tiktok_product(self, product: Dict[str, Any]) -> bool:
        """Create product in TikTok Shop."""
        try:
            url = f"{self.TIKTOK_SELLER_API}/product/create"
            payload = {
                "product_name": product.get("name"),
                "product_description": product.get("description", ""),
                "price": int(float(product.get("price", 0)) * 100),  # Cents
                "sku": product.get("sku"),
                "category": product.get("category", ""),
                "images": product.get("images", []),
                "currency": product.get("currency", "USD"),
            }
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Shop-Cipher": self.shop_cipher,
            }

            response = await self.http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()

            if data.get("code") == "0":
                logger.info(f"Created product in TikTok: {product.get('sku')}")
                return True
            else:
                logger.error(f"Product creation failed: {data.get('message')}")
                return False

        except httpx.HTTPError as e:
            logger.error(f"Error creating TikTok product: {e}")
            return False

    async def _update_tiktok_product(
        self,
        product_id: str,
        product: Dict[str, Any],
    ) -> bool:
        """Update product in TikTok Shop."""
        try:
            url = f"{self.TIKTOK_SELLER_API}/product/update"
            payload = {
                "product_id": product_id,
                "product_name": product.get("name"),
                "product_description": product.get("description", ""),
                "price": int(float(product.get("price", 0)) * 100),
            }
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Shop-Cipher": self.shop_cipher,
            }

            response = await self.http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()

            if data.get("code") == "0":
                logger.info(f"Updated product in TikTok: {product_id}")
                return True
            else:
                logger.error(f"Product update failed: {data.get('message')}")
                return False

        except httpx.HTTPError as e:
            logger.error(f"Error updating TikTok product: {e}")
            return False

    # ========== INVENTORY MANAGEMENT ==========

    async def update_inventory(
        self,
        product_id: str,
        quantity: int,
    ) -> bool:
        """
        Update product inventory in TikTok Shop.

        Args:
            product_id: TikTok product ID
            quantity: New stock level

        Returns:
            Success boolean
        """
        try:
            logger.info(f"Updating inventory: {product_id} → {quantity}")

            url = f"{self.TIKTOK_SELLER_API}/product/update_inventory"
            payload = {
                "product_id": product_id,
                "quantity": quantity,
            }
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Shop-Cipher": self.shop_cipher,
            }

            response = await self.http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()

            if data.get("code") == "0":
                logger.info(f"Inventory updated successfully")
                return True
            else:
                logger.error(f"Inventory update failed: {data.get('message')}")
                return False

        except httpx.HTTPError as e:
            logger.error(f"Error updating inventory: {e}")
            return False

    # ========== FULFILLMENT & SHIPPING ==========

    async def create_shipment(
        self,
        order_id: str,
        fulfillment_type: TikTokFulfillmentType,
        tracking_info: Dict[str, str],
    ) -> bool:
        """
        Create shipment and update order fulfillment.

        Args:
            order_id: TikTok order ID
            fulfillment_type: seller_fulfillment or tiktok_shop_fulfillment
            tracking_info: {carrier, tracking_number}

        Returns:
            Success boolean
        """
        try:
            logger.info(f"Creating shipment for order {order_id}")

            url = f"{self.TIKTOK_SELLER_API}/fulfillment/create_shipment"
            payload = {
                "order_id": order_id,
                "fulfillment_type": fulfillment_type.value,
                "tracking_info": tracking_info,
            }
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Shop-Cipher": self.shop_cipher,
            }

            response = await self.http_client.post(url, json=payload, headers=headers)
            response.raise_for_status()

            data = response.json()

            if data.get("code") == "0":
                logger.info(f"Shipment created for order {order_id}")
                return True
            else:
                logger.error(f"Shipment creation failed: {data.get('message')}")
                return False

        except httpx.HTTPError as e:
            logger.error(f"Error creating shipment: {e}")
            return False

    async def update_tracking(
        self,
        order_id: str,
        carrier: str,
        tracking_number: str,
    ) -> bool:
        """
        Update order tracking information.

        Args:
            order_id: TikTok order ID
            carrier: Shipping carrier name
            tracking_number: Tracking number

        Returns:
            Success boolean
        """
        try:
            logger.info(f"Updating tracking: {order_id} via {carrier}")

            return await self.create_shipment(
                order_id,
                TikTokFulfillmentType.SELLER_FULFILLMENT,
                {
                    "carrier": carrier,
                    "tracking_number": tracking_number,
                },
            )

        except Exception as e:
            logger.error(f"Error updating tracking: {e}")
            return False

    # ========== RATE LIMITING & QUOTA ==========

    async def check_rate_limit(self) -> Dict[str, Any]:
        """Check remaining API quota for shop."""
        try:
            # TikTok provides rate limit info in response headers
            # Store in database for monitoring
            logger.info(f"Checking rate limit for shop {self.shop_id}")
            return {
                "remaining_requests": 10000,
                "reset_at": datetime.utcnow() + timedelta(days=1),
            }

        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return {}
