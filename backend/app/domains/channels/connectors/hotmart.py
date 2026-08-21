"""Hotmart Connector.

Handles webhooks for purchases (approved/complete/canceled/refunded/chargeback)
and subscription events. Hotmart has no native messaging channel — this
connector is order/webhook-driven, following the same pattern as Shopify.

Auth: Hotmart webhooks carry a "Hottok" token, either as a top-level
`hottok` field in the JSON body (legacy v1 payloads) or in the
`X-Hotmart-Hottok` header (v2 payloads). The seller configures this token
in Hotmart's webhook settings and it must match `credentials["hottok"]`.

Pull methods (list_sales/list_subscribers) use Hotmart's separate OAuth2
Payments API (client_credentials grant, client_id/client_secret). Hotmart's
public API has no product-creation endpoint for third-party sellers —
products are managed only via Hotmart's own producer dashboard — so unlike
Shopify/Amazon there is no push_catalog_item here; adding a fake one would
claim a capability the platform doesn't expose.

Docs: https://developers.hotmart.com/docs/en/webhooks/
      https://developers.hotmart.com/docs/en/api-docs/sales/sales-api/
"""

import hmac
import time
from typing import Any

import httpx

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform

_TOKEN_URL = "https://api-sec-vlc.hotmart.com/security/oauth/token"
_SALES_API = "https://developers.hotmart.com/payments/api/v1"

# Purchase/subscription statuses that represent a completed sale.
_PAID_STATUSES = {"APPROVED", "COMPLETE", "COMPLETED"}
_CANCELLED_STATUSES = {"CANCELLED", "CANCELED"}
_REFUND_EVENTS = {"PURCHASE_REFUNDED", "PURCHASE_CHARGEBACK", "PURCHASE_PROTEST"}
_CANCEL_EVENTS = {"PURCHASE_CANCELED", "PURCHASE_CANCELLED", "SUBSCRIPTION_CANCELLATION"}
_ABANDONED_EVENTS = {"PURCHASE_OUT_OF_SHOPPING_CART"}

_EVENT_LABELS = {
    "PURCHASE_APPROVED": "Compra aprobada",
    "PURCHASE_COMPLETE": "Compra completada",
    "PURCHASE_COMPLETED": "Compra completada",
    "PURCHASE_CANCELED": "Compra cancelada",
    "PURCHASE_CANCELLED": "Compra cancelada",
    "PURCHASE_REFUNDED": "Compra reembolsada",
    "PURCHASE_CHARGEBACK": "Contracargo",
    "PURCHASE_PROTEST": "Compra disputada",
    "PURCHASE_DELAYED": "Pago demorado",
    "PURCHASE_EXPIRED": "Compra expirada",
    "PURCHASE_OUT_OF_SHOPPING_CART": "Carrito abandonado",
    "SUBSCRIPTION_CANCELLATION": "Suscripción cancelada",
    "CLUB_FIRST_ACCESS": "Primer acceso al curso",
    "CLUB_MODULE_COMPLETED": "Módulo completado",
}


class HotmartConnector(BaseChannelConnector):
    """Conector para Hotmart webhooks (compras, suscripciones, área de miembros)."""
    platform = "hotmart"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.hottok = credentials.get("hottok")
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        self.basic_token = credentials.get("basic_token")
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        """Hotmart doesn't have a native messaging channel."""
        return {"status": "logged", "note": "Hotmart no soporta mensajería directa"}

    async def _get_access_token(self) -> str:
        """OAuth2 client_credentials grant para la Payments API de Hotmart."""
        if not self.client_id or not self.client_secret or not self.basic_token:
            raise ValueError("Faltan client_id/client_secret/basic_token de Hotmart")

        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token

        async with httpx.AsyncClient() as client:
            response = await client.post(
                _TOKEN_URL,
                params={"grant_type": "client_credentials"},
                headers={"Authorization": f"Basic {self.basic_token}"},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            self._access_token = data["access_token"]
            self._token_expires_at = time.time() + data.get("expires_in", 3600) - 60
            return self._access_token

    async def list_sales(self, start_date: str | None = None, end_date: str | None = None) -> list[dict[str, Any]]:
        """Pull real de historial de ventas (Hotmart Payments API)."""
        token = await self._get_access_token()
        params: dict[str, Any] = {}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_SALES_API}/sales/history",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            return response.json().get("items", [])

    async def list_subscribers(self, subscriber_status: str | None = None) -> list[dict[str, Any]]:
        """Pull real de suscriptores activos (Hotmart Payments API)."""
        token = await self._get_access_token()
        params: dict[str, Any] = {}
        if subscriber_status:
            params["status"] = subscriber_status

        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{_SALES_API}/subscriptions",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            return response.json().get("items", [])

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        """Parse a Hotmart webhook payload (v2.0.0 event format)."""
        event = raw_payload.get("event", "")
        data = raw_payload.get("data", {})

        buyer = data.get("buyer", {})
        product = data.get("product", {})
        purchase = data.get("purchase", {})
        subscription = data.get("subscription", {})

        transaction = purchase.get("transaction", "")
        product_name = product.get("name", "Producto")
        price = purchase.get("price", {})
        price_value = price.get("value", 0)
        currency = price.get("currency_value", "BRL")

        label = _EVENT_LABELS.get(event, event or "Evento de Hotmart")
        content = f"{label}: {product_name}"
        if price_value:
            content += f" - {price_value} {currency}"

        if event in _ABANDONED_EVENTS:
            content_type = "abandoned_cart"
        elif event in _REFUND_EVENTS or event in _CANCEL_EVENTS:
            content_type = "order"
        elif event.startswith("PURCHASE") or event.startswith("SUBSCRIPTION"):
            content_type = "order"
        else:
            content_type = "system"

        buyer_name = buyer.get("name", "") or (subscription.get("subscriber", {}) or {}).get("name", "")

        return WebhookPayload(
            platform=ChannelPlatform.HOTMART,
            external_id=transaction or str(product.get("id", "unknown")),
            sender_id=buyer.get("email", ""),
            sender_name=buyer_name or "Cliente Hotmart",
            sender_email=buyer.get("email", ""),
            sender_phone=buyer.get("checkout_phone", ""),
            content=content,
            content_type=content_type,
            extra_data=raw_payload,
        )

    def verify_hottok(self, hottok_from_request: str | None) -> bool:
        """Verify the Hottok token sent by Hotmart matches the configured one."""
        if not self.hottok:
            return True
        if not hottok_from_request:
            return False
        return hmac.compare_digest(self.hottok, hottok_from_request)

    async def validate_credentials(self) -> bool:
        """Hotmart doesn't expose a lightweight endpoint to ping; a configured
        Hottok is the minimum requirement for the connector to be usable."""
        return bool(self.hottok)
