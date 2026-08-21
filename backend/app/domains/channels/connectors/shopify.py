"""Shopify Connector.

Handles webhooks for orders, customers, and abandoned checkouts, plus real
outbound catalog sync (push/pull) and order notes via the Admin REST API.
Docs: https://shopify.dev/docs/api/admin-rest
"""

import hmac
import hashlib
from typing import Any

import httpx

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform

_API_VERSION = "2024-01"


class ShopifyConnector(BaseChannelConnector):
    """Conector para Shopify: webhooks (pedidos, clientes, carritos abandonados)
    + catalog push/pull real vía Admin REST API."""
    platform = "shopify"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.shop_domain = credentials.get("shop_domain")
        self.api_key = credentials.get("api_key")
        self.api_secret = credentials.get("api_secret")
        self.admin_api_token = credentials.get("admin_api_token")
        self.webhook_secret = credentials.get("webhook_secret")

    def _admin_headers(self) -> dict[str, str]:
        if not self.admin_api_token:
            raise ValueError("Falta admin_api_token de Shopify")
        return {"X-Shopify-Access-Token": self.admin_api_token, "Content-Type": "application/json"}

    def _admin_url(self, path: str) -> str:
        if not self.shop_domain:
            raise ValueError("Falta shop_domain de Shopify")
        return f"https://{self.shop_domain}/admin/api/{_API_VERSION}/{path}"

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        """Shopify no tiene canal de mensajería directa al comprador vía Admin API.
        Lo más cercano real es agregar una nota interna a la orden (visible para
        el seller, no para el cliente) - eso sí lo hacemos de verdad."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    self._admin_url(f"orders/{recipient_id}.json"),
                    headers=self._admin_headers(),
                    json={"order": {"id": recipient_id, "note": content}},
                    timeout=30,
                )
                response.raise_for_status()
                return {"status": "logged", "note": "Nota agregada a la orden (Shopify no soporta mensajería directa al comprador)"}
        except Exception as e:
            return {"status": "failed", "error": str(e)}

    async def push_catalog_item(self, item: Any) -> dict[str, Any]:
        """Crea o actualiza un producto en Shopify vía Admin REST API."""
        payload = {
            "product": {
                "title": item.name,
                "body_html": item.description or "",
                "vendor": item.brand or "",
                "variants": [{"price": str(item.price)}] if getattr(item, "price", None) is not None else [],
            }
        }
        existing_id = getattr(item, "extra_data", {}).get("shopify_product_id") if getattr(item, "extra_data", None) else None

        async with httpx.AsyncClient() as client:
            if existing_id:
                response = await client.put(
                    self._admin_url(f"products/{existing_id}.json"),
                    headers=self._admin_headers(),
                    json=payload,
                    timeout=30,
                )
            else:
                response = await client.post(
                    self._admin_url("products.json"),
                    headers=self._admin_headers(),
                    json=payload,
                    timeout=30,
                )
            response.raise_for_status()
            return response.json().get("product", {})

    async def pull_catalog_items(self) -> list[dict[str, Any]]:
        """Trae el catálogo de productos desde Shopify vía Admin REST API."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self._admin_url("products.json"),
                headers=self._admin_headers(),
                params={"limit": 250},
                timeout=30,
            )
            response.raise_for_status()
            return response.json().get("products", [])

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
