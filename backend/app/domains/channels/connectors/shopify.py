"""Shopify Connector.

Handles webhooks for orders, customers, and abandoned checkouts.
Docs: https://shopify.dev/docs/api/admin-rest
"""

import hmac
import hashlib
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class ShopifyConnector(BaseChannelConnector):
    """Conector para Shopify webhooks (pedidos, clientes, carritos abandonados)."""
    platform = "shopify"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.shop_domain = credentials.get("shop_domain")
        self.api_key = credentials.get("api_key")
        self.api_secret = credentials.get("api_secret")
        self.admin_api_token = credentials.get("admin_api_token")
        self.webhook_secret = credentials.get("webhook_secret")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        """Shopify doesn't have a native messaging channel, but we can log it."""
        # In a real implementation, this might send an email via Shopify Email
        # or create a draft order note
        return {"status": "logged", "note": "Shopify no soporta mensajería directa"}

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        """Parse Shopify webhook payload.
        
        Shopify sends webhooks with topic headers like:
        - orders/create
        - orders/paid
        - customers/create
        - checkouts/create (abandoned cart)
        """
        topic = raw_payload.get("_topic", "")
        
        if "orders" in topic:
            order = raw_payload
            customer = order.get("customer", {})
            order_id = order.get("id", "")
            order_name = order.get("name", f"#{order_id}")
            
            # Calculate total
            total_price = order.get("total_price", "0.00")
            currency = order.get("currency", "USD")
            
            content = f"Nuevo pedido {order_name} - ${total_price} {currency}"
            if order.get("financial_status") == "paid":
                content += " (Pagado)"
            
            line_items = order.get("line_items", [])
            if line_items:
                items_text = ", ".join([item.get("title", "") for item in line_items[:3]])
                content += f"\nProductos: {items_text}"

            return WebhookPayload(
                platform=ChannelPlatform.SHOPIFY,
                external_id=str(customer.get("id", order_id)),
                sender_id=str(customer.get("id", "")),
                sender_name=f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or "Cliente Shopify",
                sender_email=customer.get("email", ""),
                sender_phone=customer.get("phone", ""),
                content=content,
                content_type="order",
                extra_data=raw_payload,
            )
        
        elif "customers" in topic:
            customer = raw_payload
            customer_id = customer.get("id", "")
            
            return WebhookPayload(
                platform=ChannelPlatform.SHOPIFY,
                external_id=str(customer_id),
                sender_id=str(customer_id),
                sender_name=f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or "Cliente Shopify",
                sender_email=customer.get("email", ""),
                sender_phone=customer.get("phone", ""),
                content="Nuevo cliente registrado en Shopify",
                content_type="customer",
                extra_data=raw_payload,
            )
        
        elif "checkouts" in topic:
            checkout = raw_payload
            customer = checkout.get("customer", {})
            
            line_items = checkout.get("line_items", [])
            items_text = ", ".join([item.get("title", "") for item in line_items[:3]]) if line_items else ""
            
            return WebhookPayload(
                platform=ChannelPlatform.SHOPIFY,
                external_id=str(customer.get("id", checkout.get("id", "unknown"))),
                sender_id=str(customer.get("id", "")),
                sender_name=f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or "Cliente Shopify",
                sender_email=customer.get("email", checkout.get("email", "")),
                content=f"Carrito abandonado: {items_text}" if items_text else "Carrito abandonado en Shopify",
                content_type="abandoned_cart",
                extra_data=raw_payload,
            )
        
        # Generic fallback
        return WebhookPayload(
            platform=ChannelPlatform.SHOPIFY,
            external_id=str(raw_payload.get("id", "unknown")),
            sender_name="Shopify",
            content=f"Evento: {topic}",
            content_type="system",
            extra_data=raw_payload,
        )

    def verify_webhook(self, raw_body: bytes, hmac_header: str) -> bool:
        """Verify Shopify webhook HMAC signature."""
        if not self.webhook_secret:
            return True
        digest = hmac.new(
            self.webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(digest, hmac_header)

    async def validate_credentials(self) -> bool:
        if not self.shop_domain or not self.admin_api_token:
            return False
        try:
            import httpx
            url = f"https://{self.shop_domain}/admin/api/2024-01/shop.json"
            headers = {"X-Shopify-Access-Token": self.admin_api_token}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception:
            return False
