"""Growth Analytics — Track followers, engagement, ROI.

Monitora crecimiento + propone optimizaciones.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class EngagementMetrics:
    """Métricas de engagement."""
    likes: int
    comments: int
    shares: int
    saves: int
    reach: int
    impressions: int
    engagement_rate: float  # (engagement / reach) * 100
    sentiment: str  # positive, neutral, negative


@dataclass
class GrowthMetrics:
    """Métricas de crecimiento."""
    followers_today: int
    followers_yesterday: int
    followers_7d_ago: int
    followers_30d_ago: int

    daily_growth_rate: float  # %
    weekly_growth_rate: float  # %
    monthly_growth_rate: float  # %

    new_followers_today: int
    new_followers_week: int
    new_followers_month: int

    churn_rate: float  # % unfollows


class GrowthAnalytics:
    """Analiza crecimiento y engagement."""

    def __init__(self):
        self.logger = logger

    async def get_account_metrics(
        self,
        platform: str,
        account_id: str,
    ) -> GrowthMetrics:
        """Obtiene métricas de cuenta."""
        # Mock data para MVP
        followers_today = 5420
        followers_yesterday = 5380
        followers_7d_ago = 5100
        followers_30d_ago = 4200

        daily_growth = ((followers_today - followers_yesterday) / followers_yesterday) * 100
        weekly_growth = ((followers_today - followers_7d_ago) / followers_7d_ago) * 100
        monthly_growth = ((followers_today - followers_30d_ago) / followers_30d_ago) * 100

        metrics = GrowthMetrics(
            followers_today=followers_today,
            followers_yesterday=followers_yesterday,
            followers_7d_ago=followers_7d_ago,
            followers_30d_ago=followers_30d_ago,
            daily_growth_rate=daily_growth,
            weekly_growth_rate=weekly_growth,
            monthly_growth_rate=monthly_growth,
            new_followers_today=40,
            new_followers_week=320,
            new_followers_month=1220,
            churn_rate=0.8,
        )

        self.logger.info(f"Account metrics: {followers_today} followers | daily growth: {daily_growth:.2f}%")

        return metrics

    async def get_top_posts(
        self,
        platform: str,
        account_id: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Obtiene posts con mejor engagement."""
        return [
            {
                "post_id": "post_001",
                "caption": "Cómo ganar $10k/mes...",
                "likes": 1250,
                "comments": 89,
                "shares": 34,
                "engagement_rate": 8.5,
                "reach": 15000,
                "published_at": (datetime.utcnow() - timedelta(days=2)).isoformat(),
            },
            {
                "post_id": "post_002",
                "caption": "La verdad sobre los negocios online...",
                "likes": 980,
                "comments": 67,
                "shares": 28,
                "engagement_rate": 7.2,
                "reach": 13500,
                "published_at": (datetime.utcnow() - timedelta(days=4)).isoformat(),
            },
        ]

    async def get_engagement_by_time(
        self,
        platform: str,
        account_id: str,
        days: int = 7,
    ) -> Dict[str, EngagementMetrics]:
        """Obtiene engagement por día."""
        return {
            "2026-07-04": EngagementMetrics(
                likes=520, comments=45, shares=12, saves=18, reach=8500, impressions=12000,
                engagement_rate=5.8, sentiment="positive",
            ),
            "2026-07-03": EngagementMetrics(
                likes=480, comments=42, shares=10, saves=15, reach=8000, impressions=11500,
                engagement_rate=5.5, sentiment="positive",
            ),
        }

    async def analyze_content_performance(
        self,
        platform: str,
        account_id: str,
    ) -> Dict[str, Any]:
        """Analiza qué tipo de contenido funciona mejor."""
        return {
            "top_content_type": "educational_tips",
            "avg_engagement": 6.8,
            "top_hashtag": "#sidehustle",
            "optimal_posting_frequency": "2-3 per day",
            "best_posting_times": ["7-8 PM UTC", "11 AM UTC"],
            "worst_content_type": "promotional",
            "avg_engagement_worst": 2.1,
            "recommendations": [
                "Focus on educational + motivational content",
                "Use trending hashtags (currently #hustle_culture trending +35%)",
                "Post during 7-9 PM UTC for max reach",
                "Engage with comments in first 30 minutes",
                "Use story features to boost visibility",
            ],
        }

    async def predict_growth(
        self,
        platform: str,
        current_followers: int,
        historical_growth_rate: float,
        posting_frequency: int,  # posts per week
        days_forward: int = 30,
    ) -> Dict[str, Any]:
        """Predice crecimiento futuro."""
        # Simple linear prediction
        daily_rate = (historical_growth_rate / 100.0) * (posting_frequency / 7.0)

        projected_followers = current_followers
        for _ in range(days_forward):
            projected_followers += (current_followers * daily_rate)
            current_followers = projected_followers

        total_growth = projected_followers - current_followers
        projected_rate = (total_growth / current_followers) * 100

        return {
            "current_followers": current_followers,
            "projected_followers": int(projected_followers),
            "projected_new_followers": int(total_growth),
            "projected_growth_rate": projected_rate,
            "projection_days": days_forward,
            "assumptions": [
                f"Current growth rate: {historical_growth_rate:.1f}%",
                f"Posting frequency: {posting_frequency} per week",
                "No changes to content strategy",
            ],
        }

    async def calculate_roi(
        self,
        followers: int,
        conversions: int,
        revenue: float,
        marketing_spend: float,
    ) -> Dict[str, Any]:
        """Calcula ROI de campaña."""
        conversion_rate = (conversions / followers) * 100 if followers > 0 else 0
        roi = ((revenue - marketing_spend) / marketing_spend) * 100 if marketing_spend > 0 else 0
        cost_per_conversion = marketing_spend / conversions if conversions > 0 else 0

        return {
            "revenue": revenue,
            "spend": marketing_spend,
            "roi_percentage": roi,
            "roi_ratio": f"1:{revenue / marketing_spend:.2f}" if marketing_spend > 0 else "N/A",
            "conversions": conversions,
            "conversion_rate": conversion_rate,
            "cost_per_conversion": cost_per_conversion,
            "net_profit": revenue - marketing_spend,
            "status": "profitable" if roi > 50 else "needs_optimization",
        }

    async def generate_growth_report(
        self,
        platform: str,
        account_id: str,
    ) -> Dict[str, Any]:
        """Genera reporte completo de crecimiento."""
        metrics = await self.get_account_metrics(platform, account_id)
        performance = await self.analyze_content_performance(platform, account_id)
        top_posts = await self.get_top_posts(platform, account_id)

        return {
            "platform": platform,
            "account_id": account_id,
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "followers": metrics.followers_today,
                "daily_growth": f"+{metrics.daily_growth_rate:.1f}%",
                "weekly_growth": f"+{metrics.weekly_growth_rate:.1f}%",
                "monthly_growth": f"+{metrics.monthly_growth_rate:.1f}%",
            },
            "top_posts": top_posts,
            "performance": performance,
            "next_actions": [
                f"Create {performance['optimal_posting_frequency']} posts tomorrow",
                f"Focus on '{performance['top_content_type']}'",
                f"Post at {performance['best_posting_times'][0]}",
                "Engage with top 10 comments in first hour",
            ],
        }


def get_growth_analytics() -> GrowthAnalytics:
    return GrowthAnalytics()
