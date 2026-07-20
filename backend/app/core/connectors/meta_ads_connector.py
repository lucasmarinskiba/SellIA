"""Meta/Facebook Ads connector — Crear campañas, optimizar presupuesto."""

import aiohttp, logging
from typing import Dict, List, Any
from .base_connector import BaseConnector, ConnectorType

logger = logging.getLogger(__name__)


class MetaAdsConnector(BaseConnector):
    """Facebook/Meta Ads integration."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__("meta_ads", ConnectorType.ADS, config)
        self.base_url = "https://graph.facebook.com/v18.0"
        self.access_token = config.get("access_token")
        self.ad_account_id = config.get("ad_account_id")

    async def authenticate(self) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/me"
                async with session.get(url, params={"access_token": self.access_token}) as resp:
                    if resp.status == 200:
                        self.authenticated = True
                        return True
                    return False
        except Exception as e:
            logger.error(f"Meta auth failed: {str(e)}")
            return False

    async def create_campaign(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Crea campaña Ads."""
        try:
            payload = {
                "name": campaign.get("name"),
                "objective": "CONVERSIONS",
                "status": "PAUSED",  # Start paused for review
                "special_ad_categories": ["none"],
            }
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.ad_account_id}/campaigns"
                async with session.post(url, data={**payload, "access_token": self.access_token}) as resp:
                    if resp.status == 201:
                        data = await resp.json()
                        logger.info(f"Campaign created: {data.get('id')}")
                        return {"status": "created", "campaign_id": data.get("id")}
                    return {"status": "error"}
        except Exception as e:
            logger.error(f"Error creating campaign: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def list_products(self) -> List[Dict[str, Any]]:
        return []  # Not applicable

    async def get_orders(self) -> List[Dict[str, Any]]:
        return []  # Not applicable

    async def send_message(self, recipient: str, message: str) -> Dict[str, Any]:
        return {"status": "not_implemented"}

    async def get_metrics(self) -> Dict[str, Any]:
        """Obtiene métricas de campaña."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/{self.ad_account_id}/insights"
                async with session.get(url, params={"access_token": self.access_token}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get("data", [{}])[0]
                        return {
                            "impressions": results.get("impressions", 0),
                            "clicks": results.get("clicks", 0),
                            "conversions": results.get("conversions", 0),
                            "spend": float(results.get("spend", 0)),
                        }
                    return {}
        except Exception as e:
            logger.error(f"Error fetching metrics: {str(e)}")
            return {}
