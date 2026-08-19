"""WooCommerce Connector.

Handles native WooCommerce (WordPress) webhooks for orders and customers.
No native messaging channel — order/webhook-driven, same pattern as Shopify.

Auth: WooCommerce signs webhook payloads with an HMAC-SHA256 digest,
base64-encoded, sent in the `X-WC-Webhook-Signature` header, using the
webhook secret configured when the webhook was created in WP-Admin.

Docs: https://woocommerce.github.io/woocommerce-rest-api-docs/#webhooks
"""

import base64
import hmac
import hashlib
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform

_ORDER_STATUS_LABELS = {
    "pending": "pendiente de pago",
    "processing": "en proceso",
    "on-hold": "en espera",
    "completed": "completado",
    "cancelled": "cancelado",
    "refunded": "reembolsado",
    "failed": "fallido",
}


class WooCommerceConnector(BaseChannelConnector):
    """Conector para WooCommerce webhooks (pedidos, clientes)."""
    platform = "woocommerce"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.site_url = credentials.get("site_url")
        self.consumer_key = credentials.get("consumer_key")
        self.consumer_secret = credentials.get("consumer_secret")
        self.webhook_secret = credentials.get("webhook_secret")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        """WooCommerce doesn't have a native messaging channel."""
        return {"status": "logged", "note": "WooCommerce no soporta mensajería directa"}

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        """Parse a WooCommerce webhook payload.

        WooCommerce sends the resource's REST representation directly as the
        body, with the event topic in the `X-WC-Webhook-Topic` header
        (injected by the API layer as `_topic`, e.g. "order.created",
        "order.updated", "customer.created").
        """
        topic = raw_payload.get("_topic", "")

        if topic.startswith("order"):
            order = raw_payload
            order_id = order.get("id", "")
            order_number = order.get("number", str(order_id))
            billing = order.get("billing", {})
            total = order.get("total", "0.00")
            currency = order.get("currency", "USD")
            status = order.get("status", "pending")

            line_items = order.get("line_items", [])
            content = f"Pedido #{order_number} ({_ORDER_STATUS_LABELS.get(status, status)}) - {total} {currency}"
            if line_items:
                items_text = ", ".join(li.get("name", "") for li in line_items[:3])
                content += f"\nProductos: {items_text}"

            return WebhookPayload(
                platform=ChannelPlatform.WOOCOMMERCE,
                external_id=str(order_id),
                sender_id=str(billing.get("email", order_id)),
                sender_name=f"{billing.get('first_name', '')} {billing.get('last_name', '')}".strip() or "Cliente WooCommerce",
                sender_email=billing.get("email", ""),
                sender_phone=billing.get("phone", ""),
                content=content,
                content_type="order",
                extra_data=raw_payload,
            )

        elif topic.startswith("customer"):
            customer = raw_payload
            customer_id = customer.get("id", "")
            billing = customer.get("billing", {})

            return WebhookPayload(
                platform=ChannelPlatform.WOOCOMMERCE,
                external_id=str(customer_id),
                sender_id=str(customer_id),
                sender_name=f"{customer.get('first_name', '')} {customer.get('last_name', '')}".strip() or "Cliente WooCommerce",
                sender_email=customer.get("email", billing.get("email", "")),
                sender_phone=billing.get("phone", ""),
                content="Nuevo cliente registrado en WooCommerce",
                content_type="customer",
                extra_data=raw_payload,
            )

        return WebhookPayload(
            platform=ChannelPlatform.WOOCOMMERCE,
            external_id=str(raw_payload.get("id", "unknown")),
            sender_name="WooCommerce",
            content=f"Evento: {topic}" if topic else "Evento de WooCommerce",
            content_type="system",
            extra_data=raw_payload,
        )

    def verify_webhook(self, raw_body: bytes, signature_header: str) -> bool:
        """Verify WooCommerce's base64-encoded HMAC-SHA256 signature."""
        if not self.webhook_secret:
            return True
        digest = hmac.new(
            self.webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).digest()
        expected = base64.b64encode(digest).decode("utf-8")
        return hmac.compare_digest(expected, signature_header)

    async def validate_credentials(self) -> bool:
        if not self.site_url or not self.consumer_key or not self.consumer_secret:
            return False
        try:
            import httpx
            url = f"{self.site_url.rstrip('/')}/wp-json/wc/v3/system_status"
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    auth=(self.consumer_key, self.consumer_secret),
                    timeout=10,
                )
                return response.status_code == 200
        except Exception:
            return False
