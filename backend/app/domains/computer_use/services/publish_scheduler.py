"""Publish Scheduler — Schedule posts en horarios óptimos.

Decide cuándo + dónde + qué publicar basado en analytics.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from enum import Enum

logger = logging.getLogger(__name__)


class PublishingStrategy(str, Enum):
    """Estrategias de publicación."""
    DAILY = "daily"  # 1 post/día
    TWICE_DAILY = "twice_daily"  # 2 posts/día
    AGGRESSIVE = "aggressive"  # 3-4 posts/día
    WEEKDAY_ONLY = "weekday_only"  # Lun-Vie
    WEEKEND_PEAK = "weekend_peak"  # Fines de semana


class ScheduledPost:
    """Post programado para publicar."""

    def __init__(
        self,
        post_id: str,
        platform: str,
        caption: str,
        image_url: str,
        scheduled_time: datetime,
        strategy: PublishingStrategy,
        priority: int = 0,  # 0=normal, 1=high, 2=urgent
    ):
        self.post_id = post_id
        self.platform = platform
        self.caption = caption
        self.image_url = image_url
        self.scheduled_time = scheduled_time
        self.strategy = strategy
        self.priority = priority
        self.status = "scheduled"  # scheduled, publishing, published, failed
        self.created_at = datetime.utcnow()
        self.published_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "post_id": self.post_id,
            "platform": self.platform,
            "caption": self.caption,
            "image_url": self.image_url,
            "scheduled_time": self.scheduled_time.isoformat(),
            "strategy": self.strategy.value,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }


class PublishScheduler:
    """Scheduler para publicaciones."""

    def __init__(self):
        self.logger = logger
        self.scheduled_posts: Dict[str, ScheduledPost] = {}

    async def schedule_post(
        self,
        platform: str,
        caption: str,
        image_url: str,
        strategy: PublishingStrategy,
        custom_time: Optional[datetime] = None,
    ) -> ScheduledPost:
        """Programa post para publicar."""
        try:
            # Calcular mejor hora si no se especifica
            if not custom_time:
                scheduled_time = await self._calculate_best_time(platform, strategy)
            else:
                scheduled_time = custom_time

            # Crear post
            post_id = f"post_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

            post = ScheduledPost(
                post_id=post_id,
                platform=platform,
                caption=caption,
                image_url=image_url,
                scheduled_time=scheduled_time,
                strategy=strategy,
            )

            self.scheduled_posts[post_id] = post

            self.logger.info(f"Post scheduled: {post_id} at {scheduled_time.isoformat()}")

            return post

        except Exception as e:
            self.logger.error(f"Error scheduling post: {e}")
            raise

    async def get_next_publishing_time(
        self,
        platform: str,
        strategy: PublishingStrategy,
    ) -> datetime:
        """Obtiene próxima hora de publicación."""
        now = datetime.utcnow()

        # Peak times por platform
        if platform == "tiktok":
            peak_hours = [11, 19, 21]  # 11 AM, 7 PM, 9 PM UTC
        elif platform == "instagram":
            peak_hours = [6, 9, 18, 20]  # 6 AM, 9 AM, 6 PM, 8 PM UTC
        else:
            peak_hours = [10, 14, 18]  # Defaults

        # Seleccionar siguiente peak hour
        if strategy == PublishingStrategy.DAILY:
            # 1 post en mejor hora
            next_hour = peak_hours[0]

        elif strategy == PublishingStrategy.TWICE_DAILY:
            # 2 posts en 2 peak hours
            next_hour = peak_hours[0] if now.hour < peak_hours[1] else peak_hours[1]

        elif strategy == PublishingStrategy.AGGRESSIVE:
            # 3-4 posts spread across peak hours
            next_hour = peak_hours[now.hour % len(peak_hours)]

        else:
            next_hour = peak_hours[0]

        # Calcular siguiente día si es de noche
        next_time = now.replace(hour=next_hour, minute=0, second=0, microsecond=0)

        if next_time <= now:
            next_time += timedelta(days=1)

        return next_time

    async def _calculate_best_time(
        self,
        platform: str,
        strategy: PublishingStrategy,
    ) -> datetime:
        """Calcula mejor hora para publicar."""
        return await self.get_next_publishing_time(platform, strategy)

    async def get_publishing_queue(self, limit: int = 10) -> List[ScheduledPost]:
        """Obtiene posts próximos a publicar."""
        now = datetime.utcnow()

        # Filtrar posts scheduled y ordenar por tiempo
        pending = [
            post for post in self.scheduled_posts.values()
            if post.status == "scheduled" and post.scheduled_time <= now + timedelta(hours=1)
        ]

        pending.sort(key=lambda p: p.scheduled_time)

        return pending[:limit]

    async def update_post_status(
        self,
        post_id: str,
        status: str,  # publishing, published, failed
    ) -> bool:
        """Actualiza status de post."""
        post = self.scheduled_posts.get(post_id)

        if not post:
            self.logger.warning(f"Post not found: {post_id}")
            return False

        post.status = status

        if status == "published":
            post.published_at = datetime.utcnow()
            self.logger.info(f"Post published: {post_id}")

        return True

    def get_posting_frequency_recommendation(self, platform: str) -> Dict[str, Any]:
        """Recomienda frecuencia óptima de posting."""
        recommendations = {
            "tiktok": {
                "recommended_frequency": "3-4 posts per day",
                "best_days": "All days",
                "peak_hours_utc": [11, 19, 21],
                "avg_engagement_peak": "7-10 PM local",
                "reason": "TikTok algorithm favors consistency + frequency",
            },
            "instagram": {
                "recommended_frequency": "1-2 posts per day",
                "best_days": "Weekdays (Tue-Thu best)",
                "peak_hours_utc": [6, 9, 18, 20],
                "avg_engagement_peak": "6-9 PM local",
                "reason": "Instagram favors quality + strategic timing",
            },
        }

        return recommendations.get(platform, recommendations["instagram"])


def get_publish_scheduler() -> PublishScheduler:
    return PublishScheduler()
