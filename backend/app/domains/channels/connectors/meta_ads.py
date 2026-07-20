"""Meta Ads (Facebook/Instagram Ads) Connector.

Manages campaigns, adsets, ads, and lead retrieval beyond basic lead webhooks.
Docs: https://developers.facebook.com/docs/marketing-api
"""

import httpx
from typing import Any, Optional

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform


class MetaAdsConnector(BaseChannelConnector):
    """Conector completo para Meta Ads (Facebook + Instagram Ads)."""
    platform = "meta_ads"
    BASE_URL = "https://graph.facebook.com/v18.0"

    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.access_token = credentials.get("access_token")
        self.page_id = credentials.get("page_id")
        self.ad_account_id = credentials.get("ad_account_id")
        self.app_id = credentials.get("app_id")
        self.app_secret = credentials.get("app_secret")
        self.pixel_id = credentials.get("pixel_id")

    async def _api_get(self, endpoint: str, params: Optional[dict] = None) -> dict[str, Any]:
        """Helper for Meta Graph API GET requests."""
        if not self.access_token:
            raise ValueError("Falta access_token de Meta")
        
        url = f"{self.BASE_URL}/{endpoint}"
        query = params or {}
        query["access_token"] = self.access_token
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=query)
            response.raise_for_status()
            return response.json()

    async def _api_post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        """Helper for Meta Graph API POST requests."""
        if not self.access_token:
            raise ValueError("Falta access_token de Meta")
        
        url = f"{self.BASE_URL}/{endpoint}"
        payload = {**data, "access_token": self.access_token}
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, data=payload)
            response.raise_for_status()
            return response.json()

    async def get_campaigns(self) -> list[dict[str, Any]]:
        """Fetch active campaigns for the ad account."""
        account = self.ad_account_id or "me"
        result = await self._api_get(
            f"{account}/campaigns",
            {"fields": "id,name,status,objective,daily_budget,budget_remaining", "effective_status": "['ACTIVE']"}
        )
        return result.get("data", [])

    async def get_adsets(self, campaign_id: str) -> list[dict[str, Any]]:
        """Fetch adsets for a campaign."""
        result = await self._api_get(
            f"{campaign_id}/adsets",
            {"fields": "id,name,status,targeting,daily_budget,billing_event"}
        )
        return result.get("data", [])

    async def get_ads(self, adset_id: str) -> list[dict[str, Any]]:
        """Fetch ads for an adset."""
        result = await self._api_get(
            f"{adset_id}/ads",
            {"fields": "id,name,status,creative,insights{spend,impressions,clicks,ctr,cpc,conversions}"}
        )
        return result.get("data", [])

    async def get_insights(self, object_id: str, level: str = "campaign") -> dict[str, Any]:
        """Fetch insights/metrics for a campaign, adset, or ad."""
        result = await self._api_get(
            f"{object_id}/insights",
            {
                "fields": "spend,impressions,clicks,ctr,cpc,conversions,conversion_values,actions",
                "level": level,
                "date_preset": "last_30d",
            }
        )
        data = result.get("data", [])
        return data[0] if data else {}

    async def create_campaign(self, name: str, objective: str = "OUTCOME_LEADS", daily_budget: Optional[int] = None) -> dict[str, Any]:
        """Create a new Meta Ads campaign."""
        account = self.ad_account_id or "act_me"
        data = {
            "name": name,
            "objective": objective,
            "status": "PAUSED",
            "special_ad_categories": "[]",
        }
        if daily_budget:
            data["daily_budget"] = str(daily_budget)
        
        return await self._api_post(f"{account}/campaigns", data)

    async def create_adset(self, campaign_id: str, name: str, targeting: dict[str, Any], daily_budget: int = 1000) -> dict[str, Any]:
        """Create a new adset within a campaign."""
        import json
        account = self.ad_account_id or "act_me"
        data = {
            "name": name,
            "campaign_id": campaign_id,
            "daily_budget": str(daily_budget),
            "billing_event": "IMPRESSIONS",
            "optimization_goal": "LEAD_GENERATION",
            "status": "PAUSED",
            "targeting": json.dumps(targeting),
        }
        return await self._api_post(f"{account}/adsets", data)

    async def send_message(self, recipient_id: str, content: str, content_type: str = "text") -> dict[str, Any]:
        """Send follow-up via Messenger if the user has opted in."""
        if not self.access_token or not self.page_id:
            raise ValueError("Faltan credenciales de Meta")

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
        """Parse Meta Ads webhook (same as FacebookAdsConnector for leads)."""
        entry = raw_payload.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

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

        full_name = lead_fields.get("full_name", lead_fields.get("name", "Lead Meta"))
        email = lead_fields.get("email", "")
        phone = lead_fields.get("phone_number", lead_fields.get("phone", ""))

        content_parts = ["Nuevo lead desde Meta Ads"]
        if full_name:
            content_parts.append(f"Nombre: {full_name}")
        if email:
            content_parts.append(f"Email: {email}")
        if phone:
            content_parts.append(f"Teléfono: {phone}")

        return WebhookPayload(
            platform=ChannelPlatform.META_ADS,
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

    async def push_catalog_item(self, item: Any) -> dict[str, Any]:
        """Push a CatalogItem to Meta Commerce / Dynamic Ads catalog."""
        if not self.access_token or not self.ad_account_id:
            raise ValueError("Faltan credenciales de Meta Ads")
        catalog_id = self.credentials.get("catalog_id")
        if not catalog_id:
            raise ValueError("Se requiere catalog_id en credenciales")
        data = {
            "name": item.name,
            "description": item.description or "",
            "price": f"{item.price} {item.currency or 'USD'}",
            "currency": item.currency or "USD",
            "image_url": item.image_url,
            "url": item.extra_data.get("url", ""),
            "availability": item.extra_data.get("availability", "in stock"),
        }
        return await self._api_post(f"{catalog_id}/products", data)

    async def pull_catalog_items(self) -> list[dict[str, Any]]:
        """Pull products from Meta Commerce catalog."""
        if not self.access_token:
            raise ValueError("Falta access_token de Meta")
        catalog_id = self.credentials.get("catalog_id")
        if not catalog_id:
            raise ValueError("Se requiere catalog_id en credenciales")
        result = await self._api_get(
            f"{catalog_id}/products",
            {"fields": "id,name,description,price,currency,image_url,url,availability"}
        )
        return result.get("data", [])

    async def validate_credentials(self) -> bool:
        if not self.access_token:
            return False
        try:
            result = await self._api_get("me", {"fields": "id,name"})
            return "id" in result
        except Exception:
            return False
