"""Cross-platform FOMO pattern synthesis."""

from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from collections import defaultdict

from app.core.logger import get_logger
from app.domains.seo_config.models import PublicationLink, PublicationLinkFOMO
from app.domains.seo_config.analytics_models import PublicationLinkMetrics

logger = get_logger(__name__)


class FOMAPatternSynthesizer:
    """Analyze cross-platform FOMO patterns and suggest optimizations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_trigger_performance_by_platform(
        self,
        business_id: UUID,
        days: int = 30,
    ) -> dict:
        """Get avg CTR by urgency trigger per platform.

        Returns: {
            "mercado-libre": {"limited_stock": 34.5, "ending_soon": 28.2, ...},
            "amazon": {...},
            ...
        }
        """
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        result = await self.db.execute(
            select(
                PublicationLinkMetrics.platform_name,
                PublicationLinkFOMO.urgency_trigger,
                func.avg(PublicationLinkMetrics.ctr).label("avg_ctr"),
            )
            .join(
                PublicationLinkFOMO,
                PublicationLinkFOMO.link_id == PublicationLinkMetrics.link_id,
            )
            .where(
                PublicationLinkFOMO.business_id == business_id,
                PublicationLinkMetrics.metric_date >= start_date,
                PublicationLinkMetrics.metric_date <= end_date,
            )
            .group_by(
                PublicationLinkMetrics.platform_name,
                PublicationLinkFOMO.urgency_trigger,
            )
        )

        patterns = defaultdict(dict)
        for row in result.all():
            platform = row[0]
            trigger = row[1] or "none"
            ctr = float(row[2]) if row[2] else 0.0
            patterns[platform][trigger] = ctr

        return dict(patterns)

    async def find_best_trigger_per_platform(
        self,
        business_id: UUID,
        days: int = 30,
    ) -> dict:
        """Find best-performing urgency trigger per platform.

        Returns: {"mercado-libre": "limited_stock", "amazon": "ending_soon", ...}
        """
        patterns = await self.get_trigger_performance_by_platform(business_id, days)

        best_triggers = {}
        for platform, triggers in patterns.items():
            if not triggers:
                continue
            best_trigger = max(triggers, key=triggers.get)
            best_triggers[platform] = {
                "trigger": best_trigger,
                "avg_ctr": float(triggers[best_trigger]),
            }

        return best_triggers

    async def get_cross_platform_recommendations(
        self,
        business_id: UUID,
        days: int = 30,
    ) -> list[dict]:
        """Get recommendations to apply winning patterns across platforms.

        Example:
        - "limited_stock" wins on Mercado Libre (34% CTR)
        - But you're using "ending_soon" on Amazon
        - Recommendation: Try "limited_stock" on Amazon (potentially +8% CTR)
        """
        best_triggers = await self.find_best_trigger_per_platform(business_id, days)

        if not best_triggers:
            return []

        patterns = await self.get_trigger_performance_by_platform(business_id, days)

        recommendations = []
        all_platforms = set()
        for platform in best_triggers.keys():
            all_platforms.add(platform)
        for platform in patterns.keys():
            all_platforms.add(platform)

        for platform in all_platforms:
            current_best = best_triggers.get(platform)
            if not current_best:
                continue

            current_trigger = current_best["trigger"]
            current_ctr = current_best["avg_ctr"]

            # Check other platforms' best triggers
            for other_platform, other_info in best_triggers.items():
                if other_platform == platform:
                    continue

                other_trigger = other_info["trigger"]
                other_ctr = other_info["avg_ctr"]

                # If other platform's trigger performs better, recommend
                if other_trigger != current_trigger:
                    improvement = other_ctr - current_ctr
                    if improvement > 5.0:  # Only recommend if >5% improvement
                        recommendations.append({
                            "platform": platform,
                            "current_trigger": current_trigger,
                            "current_ctr": float(current_ctr),
                            "recommended_trigger": other_trigger,
                            "recommended_platform": other_platform,
                            "expected_ctr": float(other_ctr),
                            "potential_improvement": float(improvement),
                            "confidence": 0.75,
                            "reasoning": f"{other_trigger} performs {improvement:.1f}% better on {other_platform}",
                        })

        # Sort by potential improvement
        recommendations.sort(key=lambda x: x["potential_improvement"], reverse=True)
        return recommendations

    async def get_trigger_winning_streak(
        self,
        business_id: UUID,
        trigger: str,
        min_samples: int = 5,
    ) -> dict:
        """Get stats on how well a trigger performs across all platforms.

        Used to identify "universal winners" vs platform-specific.
        """
        result = await self.db.execute(
            select(
                PublicationLinkMetrics.platform_name,
                func.count(PublicationLinkMetrics.id).label("count"),
                func.avg(PublicationLinkMetrics.ctr).label("avg_ctr"),
            )
            .join(
                PublicationLinkFOMO,
                PublicationLinkFOMO.link_id == PublicationLinkMetrics.link_id,
            )
            .where(
                PublicationLinkFOMO.business_id == business_id,
                PublicationLinkFOMO.urgency_trigger == trigger,
            )
            .group_by(PublicationLinkMetrics.platform_name)
            .having(func.count(PublicationLinkMetrics.id) >= min_samples)
        )

        platforms = []
        total_ctr = 0.0
        for row in result.all():
            platform = row[0]
            count = row[1]
            ctr = float(row[2]) if row[2] else 0.0
            platforms.append({
                "platform": platform,
                "samples": count,
                "avg_ctr": ctr,
            })
            total_ctr += ctr

        avg_across_platforms = total_ctr / len(platforms) if platforms else 0.0
        is_universal_winner = avg_across_platforms > 25.0 and len(platforms) >= 2

        return {
            "trigger": trigger,
            "is_universal_winner": is_universal_winner,
            "avg_ctr_across_platforms": float(avg_across_platforms),
            "platforms": platforms,
            "winning_streak": len([p for p in platforms if p["avg_ctr"] > 20.0]),
        }
