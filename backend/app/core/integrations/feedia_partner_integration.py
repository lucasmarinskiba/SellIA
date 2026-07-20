"""
FeedIA Partner Integration — SellIA ↔ FeedIA conexión real.

FeedIA: Platform especializada en creación de contenido (Instagram/TikTok/YouTube)
SellIA: Platform especializada en venta (checkout, órdenes, fulfillment)

Integración bidireccional:
1. SellIA solicita contenido de FeedIA (producto → carousel/reel)
2. FeedIA publica en redes del usuario
3. FeedIA reporta engagement + clicks
4. SellIA optimiza estrategia basado en datos
"""

import logging
import httpx
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class FeedIAPartnerIntegration:
    """Integración SellIA ↔ FeedIA."""

    FEEDIA_API = "https://api.feedia.app/v1"

    def __init__(self, feedia_api_key: str, feedia_partner_id: str):
        self.feedia_api_key = feedia_api_key
        self.feedia_partner_id = feedia_partner_id
        self.http_client = httpx.AsyncClient(timeout=30)

    # ========== CONTENT CREATION REQUESTS ==========

    async def request_carousel_for_product(
        self,
        product_id: str,
        product_name: str,
        product_description: str,
        product_price: float,
        product_images: List[str],
        style: Optional[str] = None,  # minimal, maximalist, trendy, etc
    ) -> Dict[str, Any]:
        """
        Solicita carousel Instagram para producto.

        SellIA → FeedIA: crea carousel optimizado con hooks trending.
        FeedIA genera images + captions + hashtags.
        """

        logger.info(f"Requesting carousel from FeedIA for product {product_id}")

        try:
            payload = {
                "type": "carousel",
                "platform": "instagram",
                "product": {
                    "id": product_id,
                    "name": product_name,
                    "description": product_description,
                    "price": product_price,
                    "images": product_images,
                },
                "style": style or "trending",
                "optimization": {
                    "target_audience": "e-commerce buyers",
                    "engagement_goal": "clicks_to_product",
                },
            }

            response = await self.http_client.post(
                f"{self.FEEDIA_API}/content/create",
                json=payload,
                headers={"Authorization": f"Bearer {self.feedia_api_key}"},
            )

            if response.status_code in [200, 201]:
                content = response.json()
                logger.info(f"Carousel created: {content.get('id')}")

                return {
                    "status": "success",
                    "content_id": content.get("id"),
                    "carousel": {
                        "slides": content.get("slides", []),
                        "captions": content.get("captions", []),
                        "hashtags": content.get("hashtags", []),
                        "hooks": content.get("hooks", []),
                    },
                    "ready_to_publish": True,
                }
            else:
                logger.error(f"FeedIA carousel error: {response.status_code}")
                return {"status": "error"}

        except Exception as e:
            logger.error(f"Request carousel failed: {str(e)}")
            return {"status": "error", "error": str(e)}

    async def request_reel_for_product(
        self,
        product_id: str,
        product_name: str,
        trending_hook: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Solicita Instagram Reel para producto (15-60s).

        SellIA → FeedIA: crea reel con trending audio + hook.
        FeedIA maneja: script, voiceover, editing, subtítulos.
        """

        logger.info(f"Requesting reel from FeedIA for {product_id}")

        try:
            payload = {
                "type": "reel",
                "platform": "instagram",
                "product_id": product_id,
                "product_name": product_name,
                "trending_hook": trending_hook or "must_try",
                "duration_seconds": 30,
                "style": "fast_paced",
            }

            response = await self.http_client.post(
                f"{self.FEEDIA_API}/content/create",
                json=payload,
                headers={"Authorization": f"Bearer {self.feedia_api_key}"},
            )

            if response.status_code in [200, 201]:
                content = response.json()
                logger.info(f"Reel created: {content.get('id')}")

                return {
                    "status": "success",
                    "content_id": content.get("id"),
                    "reel": {
                        "video_url": content.get("video_url"),
                        "duration": content.get("duration_seconds"),
                        "audio": content.get("audio", {}),
                        "subtitles": content.get("subtitles", []),
                    },
                    "ready_to_publish": True,
                }
            else:
                return {"status": "error"}

        except Exception as e:
            logger.error(f"Request reel failed: {str(e)}")
            return {"status": "error"}

    async def request_tiktok_video(
        self,
        product_id: str,
        product_name: str,
        product_price: float,
    ) -> Dict[str, Any]:
        """
        Solicita TikTok video para producto (15-60s).

        FeedIA especialista en TikTok trends. SellIA usa para driving traffic.
        """

        logger.info(f"Requesting TikTok video from FeedIA for {product_id}")

        try:
            payload = {
                "type": "tiktok",
                "platform": "tiktok",
                "product": {
                    "id": product_id,
                    "name": product_name,
                    "price": product_price,
                },
                "style": "viral",
                "hooks": ["relatable", "surprising", "educational"],
            }

            response = await self.http_client.post(
                f"{self.FEEDIA_API}/content/create",
                json=payload,
                headers={"Authorization": f"Bearer {self.feedia_api_key}"},
            )

            if response.status_code in [200, 201]:
                content = response.json()
                logger.info(f"TikTok video created: {content.get('id')}")

                return {
                    "status": "success",
                    "content_id": content.get("id"),
                    "tiktok_video": {
                        "video_url": content.get("video_url"),
                        "caption": content.get("caption"),
                        "hashtags": content.get("hashtags", []),
                        "trending_sounds": content.get("trending_sounds", []),
                    },
                    "ready_to_publish": True,
                }
            else:
                return {"status": "error"}

        except Exception as e:
            logger.error(f"Request TikTok failed: {str(e)}")
            return {"status": "error"}

    # ========== PUBLISHING ==========

    async def publish_carousel_to_instagram(
        self,
        content_id: str,
        user_instagram_account: str,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Publica carousel a Instagram del usuario.

        FeedIA usa Instagram Graph API para publicar.
        """

        logger.info(f"Publishing carousel {content_id} to Instagram")

        try:
            payload = {
                "content_id": content_id,
                "platform": "instagram",
                "account": user_instagram_account,
                "caption": caption,
                "schedule": "now",  # O datetime para programar
            }

            response = await self.http_client.post(
                f"{self.FEEDIA_API}/publishing/publish",
                json=payload,
                headers={"Authorization": f"Bearer {self.feedia_api_key}"},
            )

            if response.status_code in [200, 201]:
                result = response.json()
                logger.info(f"Published: {result.get('post_id')}")

                return {
                    "status": "success",
                    "post_id": result.get("post_id"),
                    "url": result.get("post_url"),
                    "published_at": datetime.utcnow().isoformat(),
                }
            else:
                return {"status": "error"}

        except Exception as e:
            logger.error(f"Publish failed: {str(e)}")
            return {"status": "error"}

    async def publish_reel_to_instagram(
        self,
        content_id: str,
        user_instagram_account: str,
    ) -> Dict[str, Any]:
        """Publica Reel a Instagram."""

        logger.info(f"Publishing reel {content_id}")

        try:
            payload = {
                "content_id": content_id,
                "type": "reel",
                "account": user_instagram_account,
            }

            response = await self.http_client.post(
                f"{self.FEEDIA_API}/publishing/publish",
                json=payload,
                headers={"Authorization": f"Bearer {self.feedia_api_key}"},
            )

            if response.status_code in [200, 201]:
                result = response.json()
                return {"status": "success", "post_id": result.get("post_id")}
            else:
                return {"status": "error"}

        except Exception as e:
            return {"status": "error"}

    async def publish_tiktok_video(
        self,
        content_id: str,
        user_tiktok_account: str,
    ) -> Dict[str, Any]:
        """Publica video a TikTok."""

        logger.info(f"Publishing TikTok {content_id}")

        try:
            payload = {
                "content_id": content_id,
                "type": "tiktok",
                "account": user_tiktok_account,
            }

            response = await self.http_client.post(
                f"{self.FEEDIA_API}/publishing/publish",
                json=payload,
                headers={"Authorization": f"Bearer {self.feedia_api_key}"},
            )

            if response.status_code in [200, 201]:
                result = response.json()
                return {"status": "success", "video_id": result.get("video_id")}
            else:
                return {"status": "error"}

        except Exception as e:
            return {"status": "error"}

    # ========== ANALYTICS & FEEDBACK LOOP ==========

    async def get_content_performance(self, content_id: str) -> Dict[str, Any]:
        """
        Obtiene engagement + analytics de contenido.

        SellIA recibe datos para optimizar futuro contenido.
        """

        logger.info(f"Getting performance for content {content_id}")

        try:
            response = await self.http_client.get(
                f"{self.FEEDIA_API}/analytics/content/{content_id}",
                headers={"Authorization": f"Bearer {self.feedia_api_key}"},
            )

            if response.status_code == 200:
                analytics = response.json()

                return {
                    "status": "success",
                    "content_id": content_id,
                    "metrics": {
                        "impressions": analytics.get("impressions", 0),
                        "clicks": analytics.get("clicks", 0),
                        "ctr": analytics.get("ctr", 0),
                        "comments": analytics.get("comments", 0),
                        "shares": analytics.get("shares", 0),
                        "saves": analytics.get("saves", 0),
                        "sales_attributed": analytics.get("sales_attributed", 0),
                    },
                }
            else:
                return {"status": "error"}

        except Exception as e:
            return {"status": "error"}

    async def report_sale_attribution(
        self,
        content_id: str,
        sale_amount: float,
        product_id: str,
    ) -> Dict[str, Any]:
        """
        Reporta a FeedIA que una venta vino de su contenido.

        Feedback loop: FeedIA optimiza basado en ROI real.
        """

        logger.info(f"Reporting sale attribution for content {content_id}: ${sale_amount}")

        try:
            payload = {
                "content_id": content_id,
                "sale_amount": sale_amount,
                "product_id": product_id,
                "timestamp": datetime.utcnow().isoformat(),
            }

            response = await self.http_client.post(
                f"{self.FEEDIA_API}/analytics/sale-attribution",
                json=payload,
                headers={"Authorization": f"Bearer {self.feedia_api_key}"},
            )

            if response.status_code in [200, 201]:
                return {"status": "success", "recorded": True}
            else:
                return {"status": "error"}

        except Exception as e:
            return {"status": "error"}

    # ========== FEEDIA CAPABILITIES ACCESS ==========

    async def list_feedia_services(self) -> Dict[str, Any]:
        """
        Lista todas herramientas/funciones disponibles en FeedIA.

        SellIA puede acceder a:
        - Content creation (carousels, reels, TikToks, blogs)
        - Audience insights (edad, género, intereses)
        - Trend analysis (hashtags trending, sounds)
        - Scheduling + publishing
        - Analytics + attribution
        - Influencer discovery
        - Y muchas más...
        """

        logger.info("Fetching FeedIA services list")

        try:
            response = await self.http_client.get(
                f"{self.FEEDIA_API}/services",
                headers={"Authorization": f"Bearer {self.feedia_api_key}"},
            )

            if response.status_code == 200:
                services = response.json()
                logger.info(f"FeedIA services available: {len(services.get('services', []))}")

                return {
                    "status": "success",
                    "services": services.get("services", []),
                }
            else:
                return {"status": "error"}

        except Exception as e:
            return {"status": "error"}

    async def close(self):
        """Cierra conexión."""
        await self.http_client.aclose()
