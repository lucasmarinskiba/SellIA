"""Beacons Connector.

Handles link-in-bio analytics, monetization events, and contact form submissions.
Docs: https://beacons.ai/developers
"""

from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class BeaconsConnector(BaseChannelConnector):
    """Conector para Beacons (link-in-bio, monetización, forms)."""
    platform = "beacons"
    BASE_URL = "https://api.beacons.ai/v1"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.api_key = credentials.get("api_key")
        self.creator_id = credentials.get("creator_id")
        self.webhook_secret = credentials.get("webhook_secret")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        """Beacons no tiene mensajería directa; log para tracking."""
        return {"status": "logged", "note": "Beacons no soporta mensajería directa"}

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        """Parse Beacons webhook payload.
        
        Beacons sends events like:
        - contact_form_submission
        - store_purchase
        - link_click
        - monetization_payout
        {
            "event": "contact_form_submission",
            "data": {
                "creator_id": "...",
                "fan_id": "...",
                "name": "John Doe",
                "email": "john@example.com",
                "message": "Hola, quiero colaborar",
                "submitted_at": "2024-01-01T00:00:00Z"
            }
        }
        """
        event = raw_payload.get("event", "")
        data = raw_payload.get("data", {})

        if event == "contact_form_submission":
            fan_id = data.get("fan_id", "")
            name = data.get("name", "Fan Beacons")
            email = data.get("email", "")
            message = data.get("message", "")

            return WebhookPayload(
                platform=ChannelPlatform.BEACONS,
                external_id=fan_id or email or "unknown",
                sender_id=fan_id,
                sender_name=name,
                sender_email=email,
                content=message or f"Nuevo mensaje desde formulario de contacto Beacons",
                content_type="text",
                extra_data=raw_payload,
            )

        elif event == "store_purchase":
            fan_id = data.get("fan_id", "")
            name = data.get("fan_name", "Comprador Beacons")
            email = data.get("fan_email", "")
            product_name = data.get("product_name", "")
            amount = data.get("amount", "")
            currency = data.get("currency", "USD")

            return WebhookPayload(
                platform=ChannelPlatform.BEACONS,
                external_id=fan_id or email or "unknown",
                sender_id=fan_id,
                sender_name=name,
                sender_email=email,
                content=f"Nueva compra en Beacons Store: {product_name} - ${amount} {currency}",
                content_type="order",
                extra_data=raw_payload,
            )

        elif event == "monetization_payout":
            return WebhookPayload(
                platform=ChannelPlatform.BEACONS,
                external_id=data.get("creator_id", "unknown"),
                sender_name="Beacons",
                content=f"Payout de monetización: ${data.get('amount', '')} {data.get('currency', 'USD')}",
                content_type="system",
                extra_data=raw_payload,
            )

        # Generic fallback
        return WebhookPayload(
            platform=ChannelPlatform.BEACONS,
            external_id=data.get("creator_id", "unknown"),
            sender_name="Beacons",
            content=f"Evento: {event}",
            content_type="system",
            extra_data=raw_payload,
        )

    async def verify_webhook(self, raw_body: bytes, signature: str) -> bool:
        """Verify Beacons webhook signature using webhook_secret."""
        if not self.webhook_secret:
            return True
        import hmac
        import hashlib
        expected = hmac.new(self.webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def get_links(self) -> list[dict[str, Any]]:
        """Fetch creator's links from Beacons API."""
        if not self.api_key or not self.creator_id:
            raise ValueError("Faltan credenciales de Beacons")
        import httpx
        url = f"{self.BASE_URL}/creators/{self.creator_id}/links"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get("data", [])

    async def get_store_products(self) -> list[dict[str, Any]]:
        """Fetch creator's store products from Beacons API."""
        if not self.api_key or not self.creator_id:
            raise ValueError("Faltan credenciales de Beacons")
        import httpx
        url = f"{self.BASE_URL}/creators/{self.creator_id}/store/products"
        headers = {"Authorization": f"Bearer {self.api_key}"}
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json().get("data", [])

    async def push_catalog_item(self, item: Any) -> dict[str, Any]:
        """Push a CatalogItem to Beacons Store."""
        if not self.api_key or not self.creator_id:
            raise ValueError("Faltan credenciales de Beacons")
        import httpx
        url = f"{self.BASE_URL}/creators/{self.creator_id}/store/products"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "name": item.name,
            "description": item.description or "",
            "price": str(item.price) if item.price else "0",
            "currency": item.currency or "USD",
            "image_url": item.image_url,
            "sku": item.sku or str(item.id),
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def pull_catalog_items(self) -> list[dict[str, Any]]:
        """Pull catalog items from Beacons Store."""
        return await self.get_store_products()

    async def validate_credentials(self) -> bool:
        if not self.api_key:
            return False
        try:
            import httpx
            url = f"{self.BASE_URL}/creators/{self.creator_id}"
            headers = {"Authorization": f"Bearer {self.api_key}"}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers)
                return response.status_code == 200
        except Exception:
            return False
