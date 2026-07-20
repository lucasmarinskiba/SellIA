"""Trending Analyzer — Detect trending hashtags + topics for growth.

Analiza qué está trending en Instagram/TikTok → genera posts automático.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import httpx

logger = logging.getLogger(__name__)


class TrendingTopic:
    """Tema trending."""

    def __init__(
        self,
        topic: str,
        platform: str,  # instagram, tiktok
        hashtag: str,
        trend_score: float,  # 0-1
        volume: int,  # posts/videos con este hashtag hoy
        growth_rate: float,  # % crecimiento en últimas 24h
        best_time_utc: str,  # cuándo publicar
    ):
        self.topic = topic
        self.platform = platform
        self.hashtag = hashtag
        self.trend_score = trend_score
        self.volume = volume
        self.growth_rate = growth_rate
        self.best_time_utc = best_time_utc
        self.detected_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "platform": self.platform,
            "hashtag": self.hashtag,
            "trend_score": self.trend_score,
            "volume": self.volume,
            "growth_rate": self.growth_rate,
            "best_time_utc": self.best_time_utc,
            "detected_at": self.detected_at.isoformat(),
        }


class TrendingAnalyzer:
    """Detecta tendencias en redes sociales."""

    # Trending topics por defecto (mock data para MVP)
    INSTAGRAM_TRENDING = {
        "hustle_culture": {
            "hashtags": ["#sidehustle", "#entrepreneurlife", "#makemoney"],
            "trend_score": 0.92,
            "volume": 15000,
            "growth_rate": 23.5,
        },
        "personal_finance": {
            "hashtags": ["#financialfreedome", "#wealth", "#invest"],
            "trend_score": 0.88,
            "volume": 12000,
            "growth_rate": 18.2,
        },
        "ai_tools": {
            "hashtags": ["#aitools", "#automation", "#productivity"],
            "trend_score": 0.85,
            "volume": 10000,
            "growth_rate": 35.7,
        },
    }

    TIKTOK_TRENDING = {
        "short_tips": {
            "hashtags": ["#shorttips", "#quickmoney", "#boostbusiness"],
            "trend_score": 0.95,
            "volume": 50000,
            "growth_rate": 42.1,
        },
        "transformation": {
            "hashtags": ["#beforeafter", "#success", "#transformation"],
            "trend_score": 0.90,
            "volume": 45000,
            "growth_rate": 28.5,
        },
        "trend_challenges": {
            "hashtags": ["#challenge", "#viral", "#trending"],
            "trend_score": 0.93,
            "volume": 60000,
            "growth_rate": 51.3,
        },
    }

    def __init__(self):
        self.logger = logger

    async def get_trending_topics(
        self,
        platform: str,  # instagram, tiktok
        niche: Optional[str] = None,  # ej: "sales", "fitness", "ai"
        top_n: int = 5,
    ) -> List[TrendingTopic]:
        """Obtiene trending topics para plataforma."""
        try:
            if platform == "instagram":
                trending_dict = self.INSTAGRAM_TRENDING
                best_time = "18:00"  # 6 PM UTC óptimo para Instagram
            elif platform == "tiktok":
                trending_dict = self.TIKTOK_TRENDING
                best_time = "19:00"  # 7 PM UTC óptimo para TikTok
            else:
                return []

            # Filtrar por niche si se proporciona
            if niche:
                trending_dict = {k: v for k, v in trending_dict.items() if niche.lower() in k.lower()}

            # Convertir a TrendingTopic objects ordenados por trend_score
            topics = []
            for topic_name, topic_data in trending_dict.items():
                hashtag = topic_data["hashtags"][0]  # usar primer hashtag
                topic = TrendingTopic(
                    topic=topic_name,
                    platform=platform,
                    hashtag=hashtag,
                    trend_score=topic_data["trend_score"],
                    volume=topic_data["volume"],
                    growth_rate=topic_data["growth_rate"],
                    best_time_utc=best_time,
                )
                topics.append(topic)

            # Sort por trend_score descendente
            topics.sort(key=lambda t: t.trend_score, reverse=True)

            self.logger.info(f"Found {len(topics)} trending topics for {platform}")

            return topics[:top_n]

        except Exception as e:
            self.logger.error(f"Error getting trending topics: {e}")
            return []

    async def get_best_posting_time(
        self,
        platform: str,
        audience_timezone: Optional[str] = None,
    ) -> str:
        """Obtiene mejor hora para publicar."""
        # Basado en analytics: Instagram peak 6-9 PM, TikTok peak 7-11 PM
        if platform == "tiktok":
            return "19:00"  # 7 PM UTC
        else:  # instagram
            return "18:00"  # 6 PM UTC

    async def analyze_niche_performance(
        self,
        platform: str,
        niche: str,
    ) -> Dict[str, Any]:
        """Analiza performance de niche específico."""
        return {
            "niche": niche,
            "platform": platform,
            "market_saturation": 0.62,  # 0-1
            "growth_potential": 0.78,  # 0-1
            "avg_engagement_rate": 0.045,  # 4.5%
            "recommended_posting_frequency": "2-3 per day",
            "recommended_hashtag_count": 15,
            "competitor_count": 234,
            "recommendations": [
                "Focus on short-form video (15-30s)",
                "Use trending sounds",
                "Post during peak hours (7-10 PM UTC)",
                "Engage with community in first hour",
            ],
        }


def get_trending_analyzer() -> TrendingAnalyzer:
    return TrendingAnalyzer()
