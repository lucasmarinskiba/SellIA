"""
Instagram Shop Automation — Direct checkout, webhook, orders sync, analytics.

Flujo:
1. Usuario habilita Instagram Shop (Checkout feature)
2. Sistema sincroniza productos → Instagram Shop
3. Webhooks escuchan: checkout_started, payment_completed, order_status_updated
4. Sistema maneja fulfillment automático
5. Analytics: profile_views, website_clicks, conversion tracking

Instagram Graph API:
- /me/instagram_business_account (business profile)
- /business_account/catalog (product sync)
- /ig_hashtag_search (hashtag research)
- Webhooks: order_updates, product_updates

Rate Limit: 500 requests/hour per token
"""

import logging
import hashlib
import hmac
import httpx
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)


class InstagramCheckoutStatus(Enum):
    """Instagram checkout order statuses."""
    CHECKOUT_STARTED = "CHECKOUT_STARTED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_CONFIRMED = "PAYMENT_CONFIRMED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


class InstagramShopAutomation:
    """Instagram Shop complete automation."""

    IG_GRAPH_API = "https://graph.instagram.com/v18.0"
    TIMEOUT = 30

    def __init__(
        self,
        account_id: str,
        access_token: str,
        webhook_verify_token: str,
    ):
        """
        Initialize Instagram Shop automation.

        Args:
            account_id: Instagram business account ID
            access_token: Instagram Graph API token (encrypted in production)
            webhook_verify_token: Custom token for webhook verification
        """
        self.account_id = account_id
        self.access_token = access_token
        self.webhook_verify_token = webhook_verify_token
        self.http_client = httpx.AsyncClient(timeout=self.TIMEOUT)

    # ========== WEBHOOK HANDLING & VERIFICATION ==========

    def verify_webhook_signature(
        self,
        payload_body: bytes,
        signature: str,
    ) -> bool:
        """
        Verify Instagram webhook signature.

        Format: X-Hub-Signature: sha256=<signature>

        Args:
            payload_body: Raw webhook payload bytes
            signature: X-Hub-Signature header value

        Returns:
            bool: True if signature is valid
        """
        try:
            expected_signature = "sha256=" + hmac.new(
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
        Process incoming Instagram webhook.

        Payload structure:
        {
          "object": "instagram",
          "entry": [{
            "changes": [{
              "field": "order_updates",
              "value": {
                "id": "order_id",
                "status": "PAYMENT_CONFIRMED",
                ...
              }
            }]
          }]
        }

        Args:
            payload: Webhook payload from Instagram

        Returns:
            Processed webhook response
        """
        try:
            if not payload.get("entry"):
                return {"status": "success", "message": "No entries"}

            for entry in payload["entry"]:
                for change in entry.get("changes", []):
                    field = change.get("field")
                    value = change.get("value", {})

                    if field == "order_updates":
                        await self._handle_order_update(value)
                    elif field == "product_updates":
                        await self._handle_product_update(value)

            return {"status": "success"}

        except Exception as e:
            logger.error(f"Webhook processing error: {e}")
            return {"status": "error", "message": str(e)}

    async def _handle_order_update(self, order_data: Dict[str, Any]) -> None:
        """Handle order status change."""
        order_id = order_data.get("id")
        status = order_data.get("status")

        logger.info(f"Order update: {order_id} → {status}")

        if status == InstagramCheckoutStatus.PAYMENT_CONFIRMED.value:
            # Trigger fulfillment workflow
            await self.confirm_order(order_id)

    async def _handle_product_update(self, product_data: Dict[str, Any]) -> None:
        """Handle product changes."""
        product_id = product_data.get("id")
        logger.info(f"Product update: {product_id}")

    # ========== ORDER MANAGEMENT ==========

    async def get_order_details(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch order details from Instagram.

        API: GET /order_id?fields=id,status,buyer,items,total,shipping_address
        """
        try:
            url = f"{self.IG_GRAPH_API}/{order_id}"
            params = {
                "fields": (
                    "id,status,buyer,buyer_email,buyer_phone,items,"
                    "total_amount,currency,shipping_address,estimated_delivery_date"
                ),
                "access_token": self.access_token,
            }

            response = await self.http_client.get(url, params=params)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error fetching order {order_id}: {e}")
            return None

    async def confirm_order(self, order_id: str) -> bool:
        """
        Confirm order received and trigger fulfillment.

        After payment confirmed, mark order as received.

        Args:
            order_id: Instagram order ID

        Returns:
            Success boolean
        """
        try:
            logger.info(f"Confirming order: {order_id}")

            order_details = await self.get_order_details(order_id)
            if not order_details:
                return False

            # Update order status to indicate we received it
            url = f"{self.IG_GRAPH_API}/{order_id}"
            payload = {
                "status": "CONFIRMED",  # Custom status we can track
            }
            params = {"access_token": self.access_token}

            response = await self.http_client.post(url, json=payload, params=params)
            response.raise_for_status()

            logger.info(f"Order {order_id} confirmed")

            # Trigger fulfillment workflow
            # (send to warehouse, create shipment, etc)

            return True

        except httpx.HTTPError as e:
            logger.error(f"Error confirming order {order_id}: {e}")
            return False

    async def update_order_status(
        self,
        order_id: str,
        status: InstagramCheckoutStatus,
        tracking_info: Optional[Dict[str, str]] = None,
    ) -> bool:
        """
        Update order status and tracking.

        Args:
            order_id: Instagram order ID
            status: New status
            tracking_info: Optional {carrier, tracking_number, estimated_delivery}

        Returns:
            Success boolean
        """
        try:
            logger.info(f"Updating order {order_id} → {status.value}")

            url = f"{self.IG_GRAPH_API}/{order_id}"
            payload = {
                "status": status.value,
            }

            if tracking_info:
                payload.update(tracking_info)

            params = {"access_token": self.access_token}

            response = await self.http_client.post(url, json=payload, params=params)
            response.raise_for_status()

            logger.info(f"Order {order_id} status updated")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Error updating order {order_id}: {e}")
            return False

    # ========== PRODUCT CATALOG MANAGEMENT ==========

    async def sync_products_to_instagram(
        self,
        products: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Sync local products to Instagram Shop.

        Creates/updates products linked to Reels/Posts for direct checkout.

        Args:
            products: List of product dicts {name, price, description, images, sku}

        Returns:
            Sync result summary
        """
        try:
            logger.info(f"Syncing {len(products)} products to Instagram Shop")

            created_count = 0
            updated_count = 0

            for product in products:
                # Check if already exists
                existing = await self._find_product_by_sku(product.get("sku"))

                if existing:
                    success = await self._update_instagram_product(
                        existing["id"],
                        product,
                    )
                    if success:
                        updated_count += 1
                else:
                    success = await self._create_instagram_product(product)
                    if success:
                        created_count += 1

            return {
                "status": "success",
                "created": created_count,
                "updated": updated_count,
                "total": len(products),
            }

        except Exception as e:
            logger.error(f"Error syncing products to Instagram: {e}")
            return {"status": "error", "message": str(e)}

    async def _find_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Find product in Instagram catalog by SKU."""
        try:
            url = f"{self.IG_GRAPH_API}/{self.account_id}/shop_products"
            params = {
                "fields": "id,sku,name",
                "access_token": self.access_token,
            }

            response = await self.http_client.get(url, params=params)
            response.raise_for_status()

            products = response.json().get("data", [])
            for product in products:
                if product.get("sku") == sku:
                    return product

            return None

        except httpx.HTTPError as e:
            logger.error(f"Error finding product by SKU {sku}: {e}")
            return None

    async def _create_instagram_product(self, product: Dict[str, Any]) -> bool:
        """Create product in Instagram Shop."""
        try:
            url = f"{self.IG_GRAPH_API}/{self.account_id}/shop_products"
            payload = {
                "name": product.get("name"),
                "description": product.get("description", ""),
                "price": int(float(product.get("price", 0)) * 100),  # Cents
                "sku": product.get("sku"),
                "currency": product.get("currency", "USD"),
                "images": product.get("images", []),
            }
            params = {"access_token": self.access_token}

            response = await self.http_client.post(url, json=payload, params=params)
            response.raise_for_status()

            logger.info(f"Created product in Instagram: {product.get('sku')}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Error creating Instagram product: {e}")
            return False

    async def _update_instagram_product(
        self,
        product_id: str,
        product: Dict[str, Any],
    ) -> bool:
        """Update product in Instagram Shop."""
        try:
            url = f"{self.IG_GRAPH_API}/{product_id}"
            payload = {
                "name": product.get("name"),
                "description": product.get("description", ""),
                "price": int(float(product.get("price", 0)) * 100),
            }
            params = {"access_token": self.access_token}

            response = await self.http_client.post(url, json=payload, params=params)
            response.raise_for_status()

            logger.info(f"Updated product in Instagram: {product_id}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Error updating Instagram product: {e}")
            return False

    # ========== ANALYTICS & INSIGHTS ==========

    async def get_shop_analytics(self) -> Optional[Dict[str, Any]]:
        """
        Fetch Instagram Shop analytics.

        Metrics:
        - Profile views
        - Website clicks
        - Shopping impressions
        - Conversion rate
        """
        try:
            logger.info(f"Fetching analytics for account {self.account_id}")

            url = f"{self.IG_GRAPH_API}/{self.account_id}/insights"
            params = {
                "metric": (
                    "impressions,profile_views,website_clicks,"
                    "reach,follower_count,post_engagement"
                ),
                "period": "lifetime",
                "access_token": self.access_token,
            }

            response = await self.http_client.get(url, params=params)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Error fetching analytics: {e}")
            return None

    async def get_order_analytics(self, date_range_days: int = 30) -> Dict[str, Any]:
        """Get order analytics for recent period."""
        # Implementation: Query DB for order metrics
        logger.info(f"Fetching order analytics for last {date_range_days} days")
        return {
            "total_orders": 0,
            "total_revenue": 0,
            "avg_order_value": 0,
            "conversion_rate": 0,
        }

    # ========== DIRECT CHECKOUT LINKS ==========

    async def create_checkout_link(
        self,
        product_id: str,
        customer_email: Optional[str] = None,
    ) -> Optional[str]:
        """
        Generate direct checkout link for Instagram product.

        Can be shared in DMs, posts, stories for direct purchasing.

        Args:
            product_id: Instagram product ID
            customer_email: Optional pre-fill customer email

        Returns:
            Checkout URL or None
        """
        try:
            # Instagram checkout links are in format:
            # https://instagram.com/{business_account}/shop/{product_id}

            checkout_url = (
                f"https://instagram.com/p/{product_id}/"
                f"?share=checkout&email={customer_email or ''}"
            )

            logger.info(f"Generated checkout link: {checkout_url}")
            return checkout_url

        except Exception as e:
            logger.error(f"Error creating checkout link: {e}")
            return None

    # ========== SHIPPING & FULFILLMENT ==========

    async def update_tracking(
        self,
        order_id: str,
        carrier: str,
        tracking_number: str,
        estimated_delivery: Optional[str] = None,
    ) -> bool:
        """
        Update order tracking information.

        Args:
            order_id: Instagram order ID
            carrier: Shipping carrier name
            tracking_number: Tracking number
            estimated_delivery: ISO format delivery date

        Returns:
            Success boolean
        """
        try:
            logger.info(f"Updating tracking: {order_id} via {carrier}")

            tracking_info = {
                "carrier": carrier,
                "tracking_number": tracking_number,
            }

            if estimated_delivery:
                tracking_info["estimated_delivery_date"] = estimated_delivery

            return await self.update_order_status(
                order_id,
                InstagramCheckoutStatus.SHIPPED,
                tracking_info,
            )

        except Exception as e:
            logger.error(f"Error updating tracking: {e}")
            return False

    # ========== MESSAGE INTEGRATION ==========

    async def send_order_confirmation_dm(
        self,
        order_id: str,
        customer_ig_user_id: str,
        message: str,
    ) -> bool:
        """
        Send order confirmation via Instagram DM.

        Args:
            order_id: Order ID
            customer_ig_user_id: Instagram user ID to message
            message: Confirmation message

        Returns:
            Success boolean
        """
        try:
            logger.info(f"Sending order confirmation DM to {customer_ig_user_id}")

            # Use Instagram Messaging API
            url = f"{self.IG_GRAPH_API}/me/messages"
            payload = {
                "recipient": {"id": customer_ig_user_id},
                "message": {"text": message},
            }
            params = {"access_token": self.access_token}

            response = await self.http_client.post(url, json=payload, params=params)
            response.raise_for_status()

            return True

        except httpx.HTTPError as e:
            logger.error(f"Error sending DM: {e}")
            return False
