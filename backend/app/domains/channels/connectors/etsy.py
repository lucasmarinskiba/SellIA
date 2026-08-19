"""Etsy Connector.

Handles Etsy Open API v3 order (receipt) notifications. Etsy has no
outbound-messaging webhook system for sellers, so this connector is
order/webhook-driven — the shop is expected to poll receipts via the API
or receive them through a proxy webhook relay configured with the shop's
credentials; either way the normalized shape below is what reaches us.

Auth: Etsy uses OAuth2 (PKCE). `credentials` stores the API keystring,
shared secret, and the OAuth access/refresh tokens obtained during
connection setup.

Docs: https://developer.etsy.com/documentation/reference
"""

from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform

_RECEIPT_STATUS_LABELS = {
    "paid": "pagado",
    "unpaid": "sin pagar",
    "unshipped": "sin enviar",
    "shipped": "enviado",
    "completed": "completado",
    "canceled": "cancelado",
}


class EtsyConnector(BaseChannelConnector):
    """Conector para Etsy (pedidos/receipts de la tienda)."""
    platform = "etsy"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.api_keystring = credentials.get("api_keystring")
        self.shared_secret = credentials.get("shared_secret")
        self.access_token = credentials.get("access_token")
        self.refresh_token = credentials.get("refresh_token")
        self.shop_id = credentials.get("shop_id")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        """Etsy's Conversations API requires elevated app permissions rarely
        granted to third-party apps; not implemented — log instead."""
        return {"status": "logged", "note": "Etsy no soporta mensajería directa en este conector"}

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        """Parse an Etsy receipt (order) notification.

        Expects the receipt resource shape returned by
        `GET /application/shops/{shop_id}/receipts/{receipt_id}`.
        """
        event = raw_payload.get("_topic", "receipt")

        if event.startswith("receipt"):
            receipt = raw_payload
            receipt_id = receipt.get("receipt_id", "")
            buyer_email = receipt.get("buyer_email", "")
            name = receipt.get("name", "") or "Cliente Etsy"
            grandtotal = (receipt.get("grandtotal") or {}).get("amount", 0)
            divisor = (receipt.get("grandtotal") or {}).get("divisor", 100)
            currency = (receipt.get("grandtotal") or {}).get("currency_code", "USD")
            total = grandtotal / divisor if divisor else grandtotal
            status = "paid" if receipt.get("is_paid") else "unpaid"
            if receipt.get("is_shipped"):
                status = "shipped"

            transactions = receipt.get("transactions", [])
            content = f"Pedido Etsy #{receipt_id} ({_RECEIPT_STATUS_LABELS.get(status, status)}) - {total} {currency}"
            if transactions:
                items_text = ", ".join(t.get("title", "") for t in transactions[:3])
                content += f"\nProductos: {items_text}"

            return WebhookPayload(
                platform=ChannelPlatform.ETSY,
                external_id=str(receipt_id),
                sender_id=buyer_email or str(receipt_id),
                sender_name=name,
                sender_email=buyer_email,
                content=content,
                content_type="order",
                extra_data=raw_payload,
            )

        return WebhookPayload(
            platform=ChannelPlatform.ETSY,
            external_id=str(raw_payload.get("receipt_id") or raw_payload.get("shop_id") or "unknown"),
            sender_name="Etsy",
            content=f"Evento: {event}",
            content_type="system",
            extra_data=raw_payload,
        )

    async def validate_credentials(self) -> bool:
        if not self.api_keystring or not self.access_token or not self.shop_id:
            return False
        try:
            import httpx
            url = f"https://openapi.etsy.com/v3/application/shops/{self.shop_id}"
            headers = {
                "x-api-key": self.api_keystring,
                "Authorization": f"Bearer {self.access_token}",
            }
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, timeout=10)
                return response.status_code == 200
        except Exception:
            return False
