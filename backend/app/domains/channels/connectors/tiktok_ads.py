"""TikTok Ads / TikTok For Business Connector.

Captures leads from TikTok Lead Ads and manages TikTok Shop orders.
Docs: https://ads.tiktok.com/marketing_api/docs
"""

import hmac
import hashlib
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class TikTokAdsConnector(BaseChannelConnector):
    """Conector para TikTok Lead Ads y TikTok Shop."""
    platform = "tiktok_ads"
    BASE_URL = "https://business-api.tiktok.com/open_api/v1.3"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.access_token = credentials.get("access_token")
        self.app_id = credentials.get("app_id")
        self.secret = credentials.get("secret")
        self.advertiser_id = credentials.get("advertiser_id")
        self.webhook_secret = credentials.get("webhook_secret")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        """TikTok no tiene mensajería directa B2C vía API; log para tracking."""
        return {"status": "logged", "note": "TikTok Ads no soporta mensajería directa"}

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        """Parse TikTok Lead Ads webhook payload.
        
        TikTok sends lead data via webhook:
        {
            "lead_id": "...",
            "advertiser_id": "...",
            "ad_id": "...",
            "campaign_id": "...",
            "form_id": "...",
            "lead_data": {
                "name": "John Doe",
                "email": "john@example.com",
                "phone": "+1234567890",
                "country": "US",
                "state": "CA",
                "city": "San Francisco",
                "zip_code": "94102",
                "street_address": "...",
                "company": "Acme Inc",
            },
            "page_id": "...",
            "lead_type": 1,
            "create_time": 1234567890,
        }
        """
        lead_data = raw_payload.get("lead_data", {})
        lead_id = raw_payload.get("lead_id", "")
        advertiser_id = raw_payload.get("advertiser_id", "")
        ad_id = raw_payload.get("ad_id", "")
        campaign_id = raw_payload.get("campaign_id", "")
        form_id = raw_payload.get("form_id", "")
        create_time = raw_payload.get("create_time", "")

        full_name = lead_data.get("name", "Lead TikTok")
        email = lead_data.get("email", "")
        phone = lead_data.get("phone", "")
        city = lead_data.get("city", "")
        state = lead_data.get("state", "")
        country = lead_data.get("country", "")
        zip_code = lead_data.get("zip_code", "")
        street_address = lead_data.get("street_address", "")
        company = lead_data.get("company", "")

        content_parts = ["Nuevo lead desde TikTok Ads"]
        if campaign_id:
            content_parts.append(f"Campaña: {campaign_id}")
        if ad_id:
            content_parts.append(f"Ad: {ad_id}")
        if full_name:
            content_parts.append(f"Nombre: {full_name}")
        if email:
            content_parts.append(f"Email: {email}")
        if phone:
            content_parts.append(f"Teléfono: {phone}")
        if company:
            content_parts.append(f"Empresa: {company}")
        if city:
            location = ", ".join(filter(None, [city, state, country]))
            content_parts.append(f"Ubicación: {location}")

        return WebhookPayload(
            platform=ChannelPlatform.TIKTOK_ADS,
            external_id=lead_id or f"{advertiser_id}_{campaign_id}",
            sender_id=lead_id,
            sender_name=full_name,
            sender_email=email,
            sender_phone=phone,
            content="\n".join(content_parts),
            content_type="lead",
            extra_data={
                **raw_payload,
                "lead_data": lead_data,
                "advertiser_id": advertiser_id,
                "campaign_id": campaign_id,
                "ad_id": ad_id,
                "form_id": form_id,
                "create_time": create_time,
            },
        )

    def verify_webhook(self, raw_body: bytes, signature_header: str) -> bool:
        """Verify TikTok webhook signature."""
        if not self.webhook_secret:
            return True
        try:
            digest = hmac.new(
                self.webhook_secret.encode(),
                raw_body,
                hashlib.sha256,
            ).hexdigest()
            return hmac.compare_digest(digest, signature_header)
        except Exception:
            return False

    async def validate_credentials(self) -> bool:
        if not self.access_token:
            return False
        try:
            import httpx
            url = f"{self.BASE_URL}/advertiser/info/"
            headers = {"Access-Token": self.access_token}
            params = {"advertiser_ids": f"[{self.advertiser_id}]"} if self.advertiser_id else {}
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params=params)
                return response.status_code == 200
        except Exception:
            return False
