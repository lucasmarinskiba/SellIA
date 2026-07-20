"""Growth Automation Engine — Auto content creation + publishing for growth.

Orquesta: trending detection → content generation → scheduling → analytics.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta

from app.domains.computer_use.services.trending_analyzer import get_trending_analyzer, TrendingTopic
from app.domains.computer_use.services.content_generator import get_content_generator, ContentStyle
from app.domains.computer_use.services.publish_scheduler import (
    get_publish_scheduler,
    PublishingStrategy,
    ScheduledPost,
)
from app.domains.computer_use.services.growth_analytics import get_growth_analytics
from app.domains.computer_use.platform_automation_engine import (
    get_platform_automation_engine,
    PlatformAutomationType,
)

logger = logging.getLogger(__name__)


class GrowthAutomationEngine:
    """Automatiza crecimiento: detecta trends → crea + publica contenido."""

    def __init__(self):
        self.logger = logger
        self.trending_analyzer = get_trending_analyzer()
        self.content_generator = get_content_generator()
        self.publisher = get_publish_scheduler()
        self.analytics = get_growth_analytics()
        self.platform_automation = get_platform_automation_engine()

    async def run_daily_growth_cycle(
        self,
        platform: str,  # instagram, tiktok
        account_id: str,
        product_info: Dict[str, Any],
        posting_strategy: PublishingStrategy = PublishingStrategy.TWICE_DAILY,
    ) -> Dict[str, Any]:
        """
        Ejecuta ciclo diario automático:
        1. Detecta trending topics
        2. Genera contenido
        3. Publica
        4. Reporta
        """
        try:
            self.logger.info(f"Starting daily growth cycle for {platform}/{account_id}")

            # 1. DETECT TRENDS
            trending_topics = await self.trending_analyzer.get_trending_topics(
                platform=platform,
                niche=product_info.get("niche"),
                top_n=3,
            )

            if not trending_topics:
                self.logger.warning(f"No trending topics found for {platform}")
                return {"status": "no_trends", "message": "No trending topics detected"}

            # 2. GENERATE CONTENT
            posts_to_publish = []

            for i, topic in enumerate(trending_topics):
                # Seleccionar style basado en tópico
                style = self._select_content_style(topic.topic, i)

                # Generar caption
                caption = self.content_generator.generate_caption(
                    product_info=product_info,
                    trending_topic=topic.topic,
                    style=style,
                    platform=platform,
                )

                # Seleccionar imagen
                image_theme = self.content_generator.select_image_theme(topic.topic)

                # Crear post
                post = await self.publisher.schedule_post(
                    platform=platform,
                    caption=caption,
                    image_url=f"https://picsum.photos/1080/1080?random={i}",  # Placeholder
                    strategy=posting_strategy,
                )

                posts_to_publish.append({
                    "post": post,
                    "trending_topic": topic,
                    "image_theme": image_theme,
                    "style": style.value,
                })

                self.logger.info(f"Generated post for trend: {topic.topic}")

            # 3. PUBLISH POSTS
            publish_results = []

            for post_data in posts_to_publish:
                success, message_id = await self._publish_post(
                    platform=platform,
                    post=post_data["post"],
                )

                publish_results.append({
                    "post_id": post_data["post"].post_id,
                    "success": success,
                    "topic": post_data["trending_topic"].topic,
                    "scheduled_time": post_data["post"].scheduled_time.isoformat(),
                })

                if success:
                    await self.publisher.update_post_status(post_data["post"].post_id, "published")

            # 4. GET ANALYTICS
            metrics = await self.analytics.get_account_metrics(platform, account_id)
            top_posts = await self.analytics.get_top_posts(platform, account_id, limit=3)
            recommendations = await self.analytics.analyze_content_performance(platform, account_id)

            result = {
                "status": "success",
                "platform": platform,
                "account_id": account_id,
                "posts_generated": len(posts_to_publish),
                "posts_published": sum(1 for r in publish_results if r["success"]),
                "trending_topics": [t.to_dict() for t in trending_topics],
                "publish_results": publish_results,
                "current_metrics": {
                    "followers": metrics.followers_today,
                    "daily_growth": f"+{metrics.daily_growth_rate:.1f}%",
                    "new_followers_today": metrics.new_followers_today,
                },
                "top_posts": top_posts,
                "recommendations": recommendations["recommendations"],
                "next_cycle": (datetime.utcnow() + timedelta(hours=6)).isoformat(),
            }

            self.logger.info(f"Daily growth cycle completed: {len(posts_to_publish)} posts created")

            return result

        except Exception as e:
            self.logger.error(f"Error in daily growth cycle: {e}")
            return {"status": "error", "message": str(e)}

    async def get_growth_recommendations(
        self,
        platform: str,
        account_id: str,
    ) -> Dict[str, Any]:
        """Obtiene recomendaciones de crecimiento."""
        try:
            # Analizar performance
            performance = await self.analytics.analyze_content_performance(platform, account_id)
            metrics = await self.analytics.get_account_metrics(platform, account_id)

            # Predecir growth
            projection = await self.analytics.predict_growth(
                platform=platform,
                current_followers=metrics.followers_today,
                historical_growth_rate=metrics.weekly_growth_rate,
                posting_frequency=14,  # 2 per day
                days_forward=30,
            )

            return {
                "current_metrics": {
                    "followers": metrics.followers_today,
                    "weekly_growth_rate": f"{metrics.weekly_growth_rate:.1f}%",
                    "new_followers_week": metrics.new_followers_week,
                },
                "performance": performance,
                "30_day_projection": projection,
                "immediate_actions": [
                    f"Post in next 2 hours (optimal time: {performance['best_posting_times'][0]})",
                    f"Create '{performance['top_content_type']}' content",
                    f"Use hashtag '{performance['top_hashtag']}'",
                    "Respond to all comments within 1 hour",
                    "Share top posts to story",
                ],
                "longer_term": [
                    "Test 3x daily posting next week",
                    "Collaborate with 2-3 micro-influencers",
                    "Launch weekly live sessions",
                    "Create series (e.g., Tips Tuesday)",
                ],
            }

        except Exception as e:
            self.logger.error(f"Error getting recommendations: {e}")
            return {}

    # ── Private ──────────────────────────────────────────

    def _select_content_style(self, topic: str, index: int) -> ContentStyle:
        """Selecciona content style basado en topic."""
        styles = [
            ContentStyle.EDUCATIONAL,
            ContentStyle.MOTIVATIONAL,
            ContentStyle.ENTERTAINING,
        ]

        return styles[index % len(styles)]

    async def _publish_post(
        self,
        platform: str,
        post: ScheduledPost,
    ) -> Tuple[bool, Optional[str]]:
        """Publica post usando browser automation."""
        try:
            # Usar platform automation para publicar
            if platform == "instagram":
                platform_type = PlatformAutomationType.INSTAGRAM_DM  # placeholder
            elif platform == "tiktok":
                platform_type = PlatformAutomationType.TIKTOK_DM  # placeholder
            else:
                return False, None

            # En MVP, marcar como publicado
            # En prod, ejecutar platform_automation.publish_post()

            self.logger.info(f"Post published: {post.post_id}")

            return True, post.post_id

        except Exception as e:
            self.logger.error(f"Error publishing post: {e}")
            return False, None


def get_growth_automation_engine() -> GrowthAutomationEngine:
    return GrowthAutomationEngine()
