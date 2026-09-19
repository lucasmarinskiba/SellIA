"""Mercado Libre analytics connector."""

from typing import Any
from datetime import date, datetime, timedelta
import httpx

from app.core.logger import get_logger
from app.domains.seo_config.platform_analytics_base import PlatformAnalyticsConnector

logger = get_logger(__name__)


class MercadoLibreAnalytics(PlatformAnalyticsConnector):
    """Fetch performance metrics from Mercado Libre API."""

    platform_name = "mercado-libre"
    API_BASE = "https://api.mercadolibre.com"

    def __init__(self, credentials: dict[str, Any]):
        super().__init__(credentials)
        self.access_token = credentials.get("access_token")
        self.seller_id = credentials.get("seller_id")

    async def validate_credentials(self) -> bool:
        """Check if access token is valid."""
        if not self.access_token or not self.seller_id:
            logger.error("MercadoLibre analytics: missing access_token or seller_id")
            return False

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.API_BASE}/users/{self.seller_id}",
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"MercadoLibre analytics credentials validation failed: {str(e)[:100]}")
            return False

    async def get_listing_metrics(
        self, external_id: str, start_date: date, end_date: date
    ) -> dict[str, Any]:
        """Fetch metrics for a Mercado Libre listing.

        impressions: real, from /items/{id}/visits.
        conversions/revenue: real, from /orders/search filtered by item + date range.
        clicks: Mercado Libre does NOT expose a clicks/CTR metric to sellers on any
        documented endpoint. We fall back to a labeled estimate (15% of impressions)
        rather than silently guessing — callers must check clicks_estimated before
        trusting the value or computing CTR from it.
        """
        if not self.access_token:
            return {
                "impressions": 0,
                "clicks": 0,
                "conversions": 0,
                "revenue": 0,
                "clicks_estimated": True,
                "conversions_estimated": True,
                "revenue_estimated": True,
                "error": "Missing access_token",
            }

        impressions = 0
        clicks = 0
        conversions = 0
        revenue = 0.0
        conversions_estimated = True
        revenue_estimated = True

        try:
            async with httpx.AsyncClient() as client:
                # Real impressions from the visits endpoint.
                visits_url = f"{self.API_BASE}/items/{external_id}/visits"
                visits_resp = await client.get(
                    visits_url,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=10,
                    params={"include": "sales,traffic_source"},
                )

                if visits_resp.status_code == 200:
                    data = visits_resp.json()
                    impressions = data.get("total_visits", 0)

                # ML has no seller-facing clicks/CTR endpoint. This is a documented
                # platform limitation, not a shortcut: label it, never present as fact.
                clicks = int(impressions * 0.15)  # labeled estimate: 15% CTR baseline

                # Real conversions/revenue from actual orders containing this item,
                # filtered to the requested date range.
                orders_url = f"{self.API_BASE}/orders/search"
                orders_resp = await client.get(
                    orders_url,
                    headers={"Authorization": f"Bearer {self.access_token}"},
                    timeout=10,
                    params={
                        "seller": self.seller_id,
                        "order.date_created.from": f"{start_date.isoformat()}T00:00:00.000-00:00",
                        "order.date_created.to": f"{end_date.isoformat()}T23:59:59.999-00:00",
                    },
                )

                if orders_resp.status_code == 200:
                    orders_data = orders_resp.json()
                    matched_orders = 0
                    matched_revenue = 0.0
                    for order in orders_data.get("results", []):
                        for item in order.get("order_items", []):
                            if item.get("item", {}).get("id") == external_id:
                                matched_orders += 1
                                matched_revenue += float(
                                    item.get("full_unit_price", 0) or 0
                                ) * float(item.get("quantity", 0) or 0)
                    conversions = matched_orders
                    revenue = matched_revenue
                    conversions_estimated = False
                    revenue_estimated = False
                elif orders_resp.status_code in (401, 403):
                    # Missing orders_read scope on the connected app — fall back to
                    # the old labeled estimate instead of crashing the whole fetch.
                    logger.warning(
                        f"MercadoLibre orders API returned {orders_resp.status_code} "
                        f"for seller {self.seller_id} — falling back to estimated conversions "
                        "(likely missing orders_read scope)"
                    )
                    conversions = max(0, int(clicks * 0.05))
                    revenue = 0.0

                logger.info(
                    f"MercadoLibre analytics for {external_id}: "
                    f"impressions={impressions}, clicks={clicks} (estimated), "
                    f"conversions={conversions} (estimated={conversions_estimated}), "
                    f"revenue={revenue} (estimated={revenue_estimated})"
                )

                return {
                    "impressions": impressions,
                    "clicks": clicks,
                    "conversions": conversions,
                    "revenue": revenue,
                    "clicks_estimated": True,
                    "conversions_estimated": conversions_estimated,
                    "revenue_estimated": revenue_estimated,
                }

        except Exception as e:
            error_msg = str(e)[:200]
            logger.error(f"MercadoLibre analytics fetch failed: {error_msg}")
            return {
                "impressions": impressions,
                "clicks": clicks,
                "conversions": conversions,
                "revenue": revenue,
                "clicks_estimated": True,
                "conversions_estimated": True,
                "revenue_estimated": True,
                "error": error_msg,
            }
