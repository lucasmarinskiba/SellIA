"""Meta Ads API Connector — Real Facebook/Instagram Ads integration.

Usa Meta Graph API para crear + monitorear campaigns.
Soporta: Facebook, Instagram, Audience Network, Messenger.
"""

import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime
import httpx

logger = logging.getLogger(__name__)


class MetaAdsConnector:
    """Conector real de Meta Ads API."""

    API_VERSION = "v18.0"
    BASE_URL = "https://graph.facebook.com"

    def __init__(self, access_token: str, ad_account_id: str):
        """
        Inicializa connector.

        access_token: Meta access token (con ads_management scope)
        ad_account_id: act_XXXXXXXXXX format
        """
        self.access_token = access_token
        self.ad_account_id = ad_account_id  # sin 'act_' prefix
        if self.ad_account_id.startswith("act_"):
            self.ad_account_id = self.ad_account_id[4:]

        self.client = httpx.AsyncClient(
            timeout=30.0,
        )

    async def create_campaign(
        self,
        name: str,
        objective: str,  # REACH, LINK_CLICKS, CONVERSIONS, VIDEO_VIEWS, etc
        special_ad_categories: Optional[List[str]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Crea campaign.

        objective: REACH, LINK_CLICKS, CONVERSIONS, VIDEO_VIEWS, TRAFFIC, etc
        special_ad_categories: para industrias reguladas (CREDIT, EMPLOYMENT, HOUSING, etc)

        Retorna: (success, campaign_id)
        """
        try:
            url = f"{self.BASE_URL}/{self.API_VERSION}/act_{self.ad_account_id}/campaigns"

            params = {
                "access_token": self.access_token,
            }

            data = {
                "name": name,
                "objective": objective,
                "status": "PAUSED",  # Crear en pausa, activar después de configurar
            }

            if special_ad_categories:
                data["special_ad_categories"] = special_ad_categories

            response = await self.client.post(url, params=params, json=data)
            response.raise_for_status()

            result = response.json()
            campaign_id = result.get("id")

            logger.info(f"Campaign created: {campaign_id} | {name}")

            return True, campaign_id

        except httpx.HTTPError as e:
            logger.error(f"Meta Ads API error: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error creating campaign: {e}")
            return False, None

    async def create_adset(
        self,
        campaign_id: str,
        name: str,
        daily_budget: float,
        targeting: Dict[str, Any],
        billing_event: str = "IMPRESSIONS",
    ) -> Tuple[bool, Optional[str]]:
        """
        Crea adset (targeting + budget).

        targeting: {
            "geo_locations": [{"regions": [{"key": "US"}]}],
            "age_min": 18,
            "age_max": 65,
            "interests": [{"name": "marketing"}],
            "languages": [6]  # English
        }

        billing_event: IMPRESSIONS, LINK_CLICKS, PURCHASES, etc

        Retorna: (success, adset_id)
        """
        try:
            url = f"{self.BASE_URL}/{self.API_VERSION}/{campaign_id}/adsets"

            params = {
                "access_token": self.access_token,
            }

            data = {
                "name": name,
                "daily_budget": int(daily_budget * 100),  # Meta usa centavos
                "billing_event": billing_event,
                "optimization_goal": "LINK_CLICKS",
                "targeting": targeting,
                "status": "PAUSED",
            }

            response = await self.client.post(url, params=params, json=data)
            response.raise_for_status()

            result = response.json()
            adset_id = result.get("id")

            logger.info(f"Adset created: {adset_id} | {name}")

            return True, adset_id

        except httpx.HTTPError as e:
            logger.error(f"Meta Ads API error: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error creating adset: {e}")
            return False, None

    async def create_ad(
        self,
        adset_id: str,
        name: str,
        creative_id: str,  # ID de creative (imagen/video)
        status: str = "PAUSED",
    ) -> Tuple[bool, Optional[str]]:
        """
        Crea ad (vincula creative a adset).

        creative_id: ID del creative asset

        Retorna: (success, ad_id)
        """
        try:
            url = f"{self.BASE_URL}/{self.API_VERSION}/{adset_id}/ads"

            params = {
                "access_token": self.access_token,
            }

            data = {
                "name": name,
                "adset_id": adset_id,
                "creative": {"creative_id": creative_id},
                "status": status,
            }

            response = await self.client.post(url, params=params, json=data)
            response.raise_for_status()

            result = response.json()
            ad_id = result.get("id")

            logger.info(f"Ad created: {ad_id} | {name}")

            return True, ad_id

        except httpx.HTTPError as e:
            logger.error(f"Meta Ads API error: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error creating ad: {e}")
            return False, None

    async def upload_creative(
        self,
        image_url: str,
        body: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Sube imagen + copy como creative.

        Retorna: (success, creative_id)
        """
        try:
            url = f"{self.BASE_URL}/{self.API_VERSION}/act_{self.ad_account_id}/creatives"

            params = {
                "access_token": self.access_token,
            }

            data = {
                "name": f"creative_{datetime.utcnow().timestamp()}",
                "object_story_spec": {
                    "link_data": {
                        "image_hash": image_url,  # URL pública
                        "message": body,
                        "link": "https://yoursite.com",  # TODO: make configurable
                    }
                },
            }

            response = await self.client.post(url, params=params, json=data)
            response.raise_for_status()

            result = response.json()
            creative_id = result.get("id")

            logger.info(f"Creative uploaded: {creative_id}")

            return True, creative_id

        except httpx.HTTPError as e:
            logger.error(f"Meta Ads API error: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error uploading creative: {e}")
            return False, None

    async def get_insights(
        self,
        campaign_id: str,
        fields: Optional[List[str]] = None,
        time_range: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Obtiene metrics del campaign.

        fields: impressions, clicks, spend, actions, action_values, etc
        time_range: {"since": "2024-01-01", "until": "2024-01-31"}

        Retorna: insights
        """
        try:
            fields = fields or [
                "impressions",
                "clicks",
                "spend",
                "actions",
                "action_values",
                "cpc",
                "cpm",
                "ctr",
            ]

            url = f"{self.BASE_URL}/{self.API_VERSION}/{campaign_id}/insights"

            params = {
                "access_token": self.access_token,
                "fields": ",".join(fields),
            }

            if time_range:
                params.update(time_range)

            response = await self.client.get(url, params=params)
            response.raise_for_status()

            result = response.json()

            return result.get("data", [{}])[0] if result.get("data") else {}

        except Exception as e:
            logger.error(f"Error getting insights: {e}")
            return {}

    async def update_campaign_status(
        self,
        campaign_id: str,
        status: str,  # ACTIVE, PAUSED, DELETED, ARCHIVED
    ) -> bool:
        """Actualiza status del campaign."""
        try:
            url = f"{self.BASE_URL}/{self.API_VERSION}/{campaign_id}"

            params = {
                "access_token": self.access_token,
            }

            data = {"status": status}

            response = await self.client.post(url, params=params, json=data)
            response.raise_for_status()

            logger.info(f"Campaign {campaign_id} status updated to {status}")

            return True

        except Exception as e:
            logger.error(f"Error updating campaign status: {e}")
            return False

    async def update_adset_budget(
        self,
        adset_id: str,
        daily_budget: float,
    ) -> bool:
        """Actualiza presupuesto diario."""
        try:
            url = f"{self.BASE_URL}/{self.API_VERSION}/{adset_id}"

            params = {
                "access_token": self.access_token,
            }

            data = {"daily_budget": int(daily_budget * 100)}  # centavos

            response = await self.client.post(url, params=params, json=data)
            response.raise_for_status()

            logger.info(f"Adset {adset_id} budget updated to ${daily_budget}/day")

            return True

        except Exception as e:
            logger.error(f"Error updating budget: {e}")
            return False

    async def close(self):
        """Cierra conexión HTTP."""
        await self.client.aclose()


def get_meta_ads_connector(
    access_token: str,
    ad_account_id: str,
) -> MetaAdsConnector:
    """Factory para obtener connector."""
    return MetaAdsConnector(access_token, ad_account_id)
