"""Facebook Ads / Meta Marketing API Connector.

Captures leads from Facebook Lead Ads and Instagram Lead Ads.
Docs: https://developers.facebook.com/docs/marketing-api/guides/lead-ads/
"""

import httpx
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class FacebookAdsConnector(BaseChannelConnector):
    """Conector para capturar leads de anuncios de Facebook e Instagram."""
    platform = "facebook_ads"
    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.access_token = credentials.get("access_token")
        self.page_id = credentials.get("page_id")
        self.ad_account_id = credentials.get("ad_account_id")
        self.app_secret = credentials.get("app_secret")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        """Send follow-up message via Messenger if the lead has opted in."""
        if not self.access_token:
            raise ValueError("Falta access_token de Facebook")

        url = f"{self.BASE_URL}/me/messages"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "recipient": {"id": recipient_id},
            "message": {"text": content},
            "messaging_type": "UPDATE",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return response.json()

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        """Parse Facebook Lead Ads webhook payload.
        
        Meta sends leadgen webhooks with structure:
        {
            "entry": [{
                "id": "<page_id>",
                "time": 1234567890,
                "changes": [{
                    "field": "leadgen",
                    "value": {
                        "leadgen_id": "<lead_id>",
                        "page_id": "<page_id>",
                        "form_id": "<form_id>",
                        "created_time": 1234567890,
                        "field_data": [
                            {"name": "full_name", "values": ["John Doe"]},
                            {"name": "email", "values": ["john@example.com"]},
                            {"name": "phone_number", "values": ["+1234567890"]},
                            ...
                        ]
                    }
                }]
            }]
        }
        """
        entry = raw_payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        # Extract lead data
        field_data = value.get("field_data", [])
        lead_fields = {}
        for field in field_data:
            name = field.get("name", "").lower()
            values = field.get("values", [])
            if values:
                lead_fields[name] = values[0]

        leadgen_id = value.get("leadgen_id", "")
        page_id = value.get("page_id", "")
        form_id = value.get("form_id", "")

        full_name = lead_fields.get("full_name", lead_fields.get("name", "Lead Facebook"))
        email = lead_fields.get("email", "")
        phone = lead_fields.get("phone_number", lead_fields.get("phone", ""))
        
        # Build content from available fields
        content_parts = [f"Nuevo lead desde Facebook Ads"]
        if full_name:
            content_parts.append(f"Nombre: {full_name}")
        if email:
            content_parts.append(f"Email: {email}")
        if phone:
            content_parts.append(f"Teléfono: {phone}")
        
        # Add any other fields as extra context
        for key, val in lead_fields.items():
            if key not in ("full_name", "name", "email", "phone_number", "phone"):
                content_parts.append(f"{key}: {val}")

        return WebhookPayload(
            platform=ChannelPlatform.FACEBOOK_ADS,
            external_id=leadgen_id or f"{page_id}_{form_id}",
            sender_id=leadgen_id,
            sender_name=full_name,
            sender_email=email,
            sender_phone=phone,
            content="\n".join(content_parts),
            content_type="lead",
            extra_data={
                **raw_payload,
                "lead_fields": lead_fields,
                "page_id": page_id,
                "form_id": form_id,
                "leadgen_id": leadgen_id,
            },
        )

    async def validate_credentials(self) -> bool:
        if not self.access_token:
            return False
        try:
            url = f"{self.BASE_URL}/me"
            params = {"access_token": self.access_token}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, params=params)
                return response.status_code == 200
        except Exception:
            return False
