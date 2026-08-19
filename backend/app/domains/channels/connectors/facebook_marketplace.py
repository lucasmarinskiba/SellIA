"""Facebook Marketplace Connector.

Handles Meta Commerce (Catalog + Orders) Graph API webhooks for a shop's
Marketplace listings — order creation/updates and buyer messages routed
through Marketplace. Uses the same Graph API webhook subscription
mechanism as facebook_ads/instagram/messenger (page-scoped, `page_id`
identifies the channel).

Docs: https://developers.facebook.com/docs/commerce-platform
"""

from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class FacebookMarketplaceConnector(BaseChannelConnector):
    """Conector para Facebook Marketplace (Meta Commerce orders + mensajería)."""
    platform = "facebook_marketplace"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.page_id = credentials.get("page_id")
        self.page_access_token = credentials.get("page_access_token")
        self.catalog_id = credentials.get("catalog_id")
        self.app_secret = credentials.get("app_secret")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        """Send a message via the Page's Graph API (same transport as Messenger)."""
        if not self.page_access_token:
            return {"status": "error", "detail": "page_access_token no configurado"}
        try:
            import httpx
            url = f"https://graph.facebook.com/v18.0/{self.page_id}/messages"
            payload = {
                "recipient": {"id": recipient_id},
                "message": {"text": content},
            }
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    params={"access_token": self.page_access_token},
                    json=payload,
                    timeout=10,
                )
                return {"status": "sent" if response.status_code == 200 else "error", "response": response.json()}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        """Parse a Meta Commerce / Marketplace webhook change.

        Order events arrive under `entry[].changes[].field == "commerce_orders"`
        or `"catalog_order_management"`; message events reuse the standard
        Messenger `messaging[]` array shape.
        """
        entry = (raw_payload.get("entry") or [{}])[0]

        # Order/commerce events (Marketplace checkout)
        changes = entry.get("changes", [])
        for change in changes:
            field = change.get("field", "")
            if field in ("commerce_orders", "catalog_order_management"):
                value = change.get("value", {})
                order_id = value.get("order_id", "")
                buyer = value.get("buyer_details", {}) or {}
                total = value.get("order_total", {}).get("amount", "0")
                currency = value.get("order_total", {}).get("currency", "USD")

                return WebhookPayload(
                    platform=ChannelPlatform.FACEBOOK_MARKETPLACE,
                    external_id=str(order_id or entry.get("id", "unknown")),
                    sender_id=str(buyer.get("id", "")),
                    sender_name=buyer.get("name", "Comprador Marketplace"),
                    sender_email=buyer.get("email", ""),
                    content=f"Pedido Marketplace #{order_id} - {total} {currency}",
                    content_type="order",
                    extra_data=raw_payload,
                )

        # Buyer message events (standard Messenger-style payload)
        messaging = entry.get("messaging", [])
        if messaging:
            event = messaging[0]
            sender_id = event.get("sender", {}).get("id", "")
            text = event.get("message", {}).get("text", "")
            return WebhookPayload(
                platform=ChannelPlatform.FACEBOOK_MARKETPLACE,
                external_id=sender_id or "unknown",
                sender_id=sender_id,
                sender_name="Comprador Marketplace",
                content=text,
                content_type="text",
                extra_data=raw_payload,
            )

        return WebhookPayload(
            platform=ChannelPlatform.FACEBOOK_MARKETPLACE,
            external_id=str(entry.get("id", "unknown")),
            sender_name="Facebook Marketplace",
            content="Evento de Marketplace",
            content_type="system",
            extra_data=raw_payload,
        )

    async def validate_credentials(self) -> bool:
        if not self.page_id or not self.page_access_token:
            return False
        try:
            import httpx
            url = f"https://graph.facebook.com/v18.0/{self.page_id}"
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    params={"access_token": self.page_access_token, "fields": "id"},
                    timeout=10,
                )
                return response.status_code == 200
        except Exception:
            return False
