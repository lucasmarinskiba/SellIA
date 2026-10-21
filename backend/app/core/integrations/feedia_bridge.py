"""
SellIA ↔ FeedIA Bridge — Integración bidireccional completa.

SellIA (vendedor) ↔ FeedIA (contenido Instagram/TikTok)

Flujo:
1. SellIA identifica oportunidad de venta
2. Solicita contenido a FeedIA (carousel, reel, copy)
3. FeedIA genera contenido optimizado
4. SellIA publica via Computer Use
5. FeedIA monitorea performance
6. Loop feedback → mejora algoritmo
"""

import logging
from typing import Any

import httpx

from app.core.clock import utc_now

logger = logging.getLogger(__name__)


class FeedIABridge:
    """Bridge entre SellIA y FeedIA."""

    def __init__(self, feedia_api_url: str, feedia_api_key: str):
        self.api_url = feedia_api_url  # "https://feedia.vercel.app/api"
        self.api_key = feedia_api_key
        self.client = httpx.AsyncClient(timeout=30)

    # ========== CONTENT GENERATION ==========

    async def request_carousel_for_product(
        self,
        product: dict[str, Any],
        market_context: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Solicita carrusel a FeedIA para vender producto específico.

        product: {name, description, price, category, images}
        market_context: {competitor_price, demand, audience}
        """

        logger.info(f"Requesting carousel from FeedIA for {product.get('name')}")

        payload = {
            "type": "carousel",
            "product": product,
            "market_context": market_context,
            "optimization": {
                "goal": "sales_conversion",
                "platform": "instagram",
                "format": "4:5",
                "slides": 7,
            },
        }

        try:
            response = await self.client.post(
                f"{self.api_url}/content/generate",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"FeedIA error: {response.status_code}")
                return {"status": "error", "code": response.status_code}

        except Exception as e:
            logger.exception("FeedIA request failed")
            return {"status": "error", "error": str(e)}

    async def request_reel_for_product(
        self,
        product: dict[str, Any],
        trend_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Solicita reel a FeedIA para promoción de producto.
        """

        payload = {
            "type": "reel",
            "product": product,
            "trend_data": trend_data,
            "optimization": {
                "goal": "sales_conversion",
                "platform": "instagram",
                "format": "9:16",
                "duration": "15-30s",
                "hooks": ["first_3_sec", "call_to_action"],
            },
        }

        try:
            response = await self.client.post(
                f"{self.api_url}/content/generate",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            return response.json() if response.status_code == 200 else {"status": "error"}

        except Exception as e:
            logger.exception("FeedIA reel request failed")
            return {"status": "error", "error": str(e)}

    async def request_tiktok_video_for_product(
        self,
        product: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Solicita video TikTok a FeedIA para vender.
        """

        payload = {
            "type": "tiktok_video",
            "product": product,
            "optimization": {
                "goal": "sales_conversion",
                "platform": "tiktok",
                "format": "9:16",
                "duration": "15-60s",
                "hooks": ["first_1_sec", "pattern_interrupt", "urgency"],
            },
        }

        try:
            response = await self.client.post(
                f"{self.api_url}/content/generate",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            return response.json() if response.status_code == 200 else {"status": "error"}

        except Exception:
            logger.exception("FeedIA TikTok request failed")
            return {"status": "error"}

    # ========== PUBLISHING COORDINATION ==========

    async def publish_to_instagram(
        self,
        content: dict[str, Any],
        account_id: str,
    ) -> dict[str, Any]:
        """
        Publica contenido FeedIA a Instagram via SellIA Computer Use.
        """

        payload = {
            "account_id": account_id,
            "content": content,
            "platform": "instagram",
            "published_by": "sellias_computer_use",
            "timestamp": utc_now().isoformat(),
        }

        try:
            response = await self.client.post(
                f"{self.api_url}/publish/instagram",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            return response.json() if response.status_code == 200 else {"status": "error"}

        except Exception:
            logger.exception("Instagram publish failed")
            return {"status": "error"}

    async def publish_to_tiktok(
        self,
        content: dict[str, Any],
        account_id: str,
    ) -> dict[str, Any]:
        """
        Publica contenido FeedIA a TikTok via SellIA Computer Use.
        """

        payload = {
            "account_id": account_id,
            "content": content,
            "platform": "tiktok",
            "published_by": "sellias_computer_use",
            "timestamp": utc_now().isoformat(),
        }

        try:
            response = await self.client.post(
                f"{self.api_url}/publish/tiktok",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            return response.json() if response.status_code == 200 else {"status": "error"}

        except Exception:
            logger.exception("TikTok publish failed")
            return {"status": "error"}

    # ========== PERFORMANCE FEEDBACK LOOP ==========

    async def report_post_performance(
        self,
        post_id: str,
        platform: str,
        metrics: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Reporta performance de post a FeedIA para optimización.

        metrics: {views, likes, comments, shares, saves, conversion, revenue}
        """

        payload = {
            "post_id": post_id,
            "platform": platform,
            "metrics": metrics,
            "reported_by": "sellias_system",
            "timestamp": utc_now().isoformat(),
        }

        try:
            response = await self.client.post(
                f"{self.api_url}/analytics/post-performance",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            return response.json() if response.status_code == 200 else {"status": "error"}

        except Exception:
            logger.exception("Performance report failed")
            return {"status": "error"}

    # ========== AUDIENCE INSIGHTS ==========

    async def get_audience_insights(self, account_id: str) -> dict[str, Any]:
        """
        Obtiene insights de audiencia desde FeedIA para personalizar ventas.
        """

        try:
            response = await self.client.get(
                f"{self.api_url}/analytics/audience/{account_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            return response.json() if response.status_code == 200 else {"status": "error"}

        except Exception:
            logger.exception("Audience insights request failed")
            return {"status": "error"}

    # ========== HASHTAG & STRATEGY ==========

    async def get_hashtag_strategy(self, product_category: str) -> dict[str, Any]:
        """
        Obtiene estrategia de hashtags desde FeedIA.
        """

        try:
            response = await self.client.get(
                f"{self.api_url}/strategy/hashtags/{product_category}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            return response.json() if response.status_code == 200 else {"status": "error"}

        except Exception:
            logger.exception("Hashtag strategy request failed")
            return {"status": "error"}

    async def get_posting_schedule(self, account_id: str) -> dict[str, Any]:
        """
        Obtiene calendario de publicación optimizado desde FeedIA.
        """

        try:
            response = await self.client.get(
                f"{self.api_url}/schedule/optimal/{account_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            return response.json() if response.status_code == 200 else {"status": "error"}

        except Exception:
            logger.exception("Schedule request failed")
            return {"status": "error"}

    # ========== TREND MONITORING ==========

    async def get_trending_hooks(self, platform: str) -> list[str]:
        """
        Obtiene hooks trending actuales desde FeedIA.
        """

        try:
            response = await self.client.get(
                f"{self.api_url}/trends/hooks/{platform}",
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("hooks", [])
            return []

        except Exception:
            logger.exception("Trending hooks request failed")
            return []

    async def get_competitor_content_analysis(
        self,
        competitor_handle: str,
        platform: str,
    ) -> dict[str, Any]:
        """
        Analiza contenido de competidores via FeedIA.
        """

        try:
            response = await self.client.get(
                f"{self.api_url}/competitors/analyze",
                params={"handle": competitor_handle, "platform": platform},
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            return response.json() if response.status_code == 200 else {"status": "error"}

        except Exception:
            logger.exception("Competitor analysis failed")
            return {"status": "error"}

    async def close(self):
        """Cierra conexión HTTP."""
        await self.client.aclose()
