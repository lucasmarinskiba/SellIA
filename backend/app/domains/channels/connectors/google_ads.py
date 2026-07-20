"""Google Ads Connector.

Captures leads from Google Ads Lead Form Extensions and manages campaign data.
Docs: https://developers.google.com/google-ads/api/docs/start
"""

import hmac
import hashlib
import base64
from typing import Any

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class GoogleAdsConnector(BaseChannelConnector):
    """Conector para Google Ads Lead Forms y gestión de campañas."""
    platform = "google_ads"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.developer_token = credentials.get("developer_token")
        self.customer_id = credentials.get("customer_id")
        self.login_customer_id = credentials.get("login_customer_id")
        self.client_id = credentials.get("client_id")
        self.client_secret = credentials.get("client_secret")
        self.refresh_token = credentials.get("refresh_token")
        self.access_token = credentials.get("access_token")
        self.webhook_secret = credentials.get("webhook_secret")

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        """Google Ads no tiene mensajería directa; log para tracking."""
        return {"status": "logged", "note": "Google Ads no soporta mensajería directa"}

    async def parse_webhook(self, raw_payload: dict[str, Any]) -> WebhookPayload:
        """Parse Google Ads Lead Form webhook payload.
        
        Google sends webhook data via Google Ads API or webhook integrations:
        {
            "lead_id": "...",
            "campaign_id": "...",
            "gcl_id": "...",
            "user_column_data": [
                {"column_name": "FULL_NAME", "column_value": "John Doe"},
                {"column_name": "EMAIL", "column_value": "john@example.com"},
                {"column_name": "PHONE_NUMBER", "column_value": "+1234567890"},
            ],
            "api_version": "1.0",
            "form_id": "...",
            "google_key": "...",
        }
        """
        user_data = raw_payload.get("user_column_data", [])
        lead_fields = {}
        for field in user_data:
            name = field.get("column_name", "").lower()
            value = field.get("column_value", "")
            lead_fields[name] = value

        lead_id = raw_payload.get("lead_id", "")
        campaign_id = raw_payload.get("campaign_id", "")
        form_id = raw_payload.get("form_id", "")
        gcl_id = raw_payload.get("gcl_id", "")

        full_name = lead_fields.get("full_name", lead_fields.get("name", "Lead Google Ads"))
        email = lead_fields.get("email", "")
        phone = lead_fields.get("phone_number", lead_fields.get("phone", ""))
        city = lead_fields.get("city", "")
        country = lead_fields.get("country", "")
        zip_code = lead_fields.get("zip_code", "")
        street_address = lead_fields.get("street_address", "")
        company_name = lead_fields.get("company_name", "")
        work_email = lead_fields.get("work_email", "")
        job_title = lead_fields.get("job_title", "")

        content_parts = ["Nuevo lead desde Google Ads"]
        if campaign_id:
            content_parts.append(f"Campaña: {campaign_id}")
        if full_name:
            content_parts.append(f"Nombre: {full_name}")
        if email:
            content_parts.append(f"Email: {email}")
        if phone:
            content_parts.append(f"Teléfono: {phone}")
        if company_name:
            content_parts.append(f"Empresa: {company_name}")
        if job_title:
            content_parts.append(f"Cargo: {job_title}")

        return WebhookPayload(
            platform=ChannelPlatform.GOOGLE_ADS,
            external_id=lead_id or gcl_id or f"{campaign_id}_{form_id}",
            sender_id=lead_id,
            sender_name=full_name,
            sender_email=email or work_email,
            sender_phone=phone,
            content="\n".join(content_parts),
            content_type="lead",
            extra_data={
                **raw_payload,
                "lead_fields": lead_fields,
                "campaign_id": campaign_id,
                "form_id": form_id,
                "gcl_id": gcl_id,
                "city": city,
                "country": country,
                "zip_code": zip_code,
                "street_address": street_address,
            },
        )

    def verify_webhook(self, raw_body: bytes, signature_header: str) -> bool:
        """Verify Google Ads webhook signature (if configured)."""
        if not self.webhook_secret:
            return True
        try:
            expected = base64.b64encode(
                hmac.new(self.webhook_secret.encode(), raw_body, hashlib.sha1).digest()
            ).decode()
            return hmac.compare_digest(expected, signature_header)
        except Exception:
            return False

    async def validate_credentials(self) -> bool:
        if not self.access_token or not self.developer_token:
            return False
        try:
            import httpx
            url = "https://googleads.googleapis.com/v14/customers/{}/campaigns".format(self.customer_id)
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "developer-token": self.developer_token,
            }
            if self.login_customer_id:
                headers["login-customer-id"] = self.login_customer_id
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=headers, params={"pageSize": "1"})
                return response.status_code == 200
        except Exception:
            return False
