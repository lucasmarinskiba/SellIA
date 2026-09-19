"""Composite platform-algorithm-aware positioning score.

Turns raw RankingSignal values (fetched by a PlatformRankingConnector) into:
  - a composite 0-100 score per PublicationLink, broken into sub-scores that
    mirror the community "5 pillar" marketplace ranking model (reputation,
    conversion, price competitiveness, listing quality, logistics) plus an
    engagement pillar for social platforms;
  - concrete, platform-specific PositioningRecommendation rows — never
    generic advice, always tied to the actual signal value and a threshold.

A pillar with no honestly-fetchable signal (price_competitiveness_score,
today, since no competitor-price source exists in this codebase) is left
NULL and excluded from the composite average rather than fabricated — same
principle as the clicks/conversions estimation-flag fix in
platform_analytics_mercadolibre.py.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_config.models import PublicationLink
from app.domains.seo_config.positioning_models import (
    PublicationLinkPositioningScore,
    PositioningRecommendation,
)
from app.domains.seo_config.platform_ranking_base import PlatformRankingConnector, RankingSignal
from app.domains.seo_config.platform_ranking_mercadolibre import MercadoLibreRankingConnector
from app.domains.seo_config.platform_ranking_instagram import InstagramRankingConnector
from app.domains.seo_config.platform_ranking_amazon import AmazonRankingConnector
from app.domains.seo_config.platform_ranking_hotmart import HotmartRankingConnector
from app.domains.seo_config.positioning_scoring_utils import composite_from_sub_scores, measured_pct
from app.domains.seo_config.agent_guard import SEOAgentGuard

logger = get_logger(__name__)

RANKING_CONNECTORS = {
    "mercado-libre": MercadoLibreRankingConnector,
    "instagram": InstagramRankingConnector,
    "amazon": AmazonRankingConnector,
    "hotmart": HotmartRankingConnector,
}


class PositioningScoreService:
    """Compute and persist platform-algorithm-aware positioning scores."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_ranking_connector(
        self, platform_name: str, connection_id: UUID
    ) -> PlatformRankingConnector | None:
        """Resolve a ranking connector for a platform, same credential
        resolution pattern as PlatformAnalyticsService.get_analytics_connector."""
        if platform_name not in RANKING_CONNECTORS:
            logger.warning(f"No ranking connector for platform: {platform_name}")
            return None

        try:
            from app.domains.integrations.integration_models import IntegrationConnection

            result = await self.db.execute(
                select(IntegrationConnection).where(IntegrationConnection.id == connection_id)
            )
            connection = result.scalar_one_or_none()
            if not connection:
                logger.error(f"Connection {connection_id} not found")
                return None

            credentials = connection.auth_metadata or {}
            if connection.auth_token:
                credentials["access_token"] = connection.auth_token

            connector_class = RANKING_CONNECTORS[platform_name]
            connector = connector_class(credentials)

            if not await connector.validate_credentials():
                logger.error(f"Ranking credentials invalid for {platform_name}")
                return None

            return connector

        except Exception as e:
            logger.error(f"Error getting ranking connector: {str(e)[:200]}")
            return None

    async def compute_score_for_link(
        self,
        business_id: UUID,
        link: PublicationLink,
        connection_id: UUID | None = None,
    ) -> PublicationLinkPositioningScore | None:
        """Fetch signals for one link, compute composite + sub-scores, persist
        the score snapshot and any triggered recommendations."""

        guard = SEOAgentGuard(self.db)
        if not await guard.can_run_seo_agent(business_id, "positioning", platform_id=connection_id):
            return None

        if not connection_id or link.platform_source not in RANKING_CONNECTORS:
            logger.info(
                f"No ranking connector available for link {link.id} (platform={link.platform_source})"
            )
            return None

        connector = await self.get_ranking_connector(link.platform_source, connection_id)
        if not connector:
            return None

        try:
            external_id = link.url  # connectors resolve their own id shape internally where needed
            signals = await connector.get_ranking_signals(external_id)
        except Exception as e:
            logger.error(f"Failed to fetch ranking signals for link {link.id}: {str(e)[:200]}")
            return None

        if link.platform_source == "instagram":
            signals.extend(await self._compute_posting_cadence(business_id, link))

        signal_map = {s.key: s for s in signals}

        sub_scores = connector.score_signals(signal_map)
        composite = composite_from_sub_scores(sub_scores)
        measured = measured_pct(signals)

        score = PublicationLinkPositioningScore(
            business_id=business_id,
            link_id=link.id,
            platform_name=link.platform_source,
            composite_score=composite,
            raw_signals={"signals": [s.as_dict() for s in signals]},
            measured_signal_pct=measured,
            **sub_scores,
        )
        self.db.add(score)
        await self.db.commit()
        await self.db.refresh(score)

        await self._generate_recommendations(
            business_id, link, score, connector.recommendation_rules(signal_map)
        )

        logger.info(
            f"Positioning score computed for link {link.id}: composite={composite:.1f}, "
            f"measured={measured:.0f}%"
        )
        return score

    async def _compute_posting_cadence(
        self, business_id: UUID, link: PublicationLink
    ) -> list[RankingSignal]:
        result = await self.db.execute(
            select(PublicationLink)
            .where(
                PublicationLink.business_id == business_id,
                PublicationLink.platform_source == "instagram",
            )
            .order_by(PublicationLink.created_at.desc())
            .limit(10)
        )
        links = result.scalars().all()
        if len(links) < 2:
            return [RankingSignal(
                "posting_cadence_days", None, measured=False,
                detail="not enough publication history yet",
            )]

        deltas = [
            (links[i].created_at - links[i + 1].created_at).total_seconds() / 86400
            for i in range(len(links) - 1)
        ]
        avg_days = round(sum(deltas) / len(deltas), 1)
        return [RankingSignal(
            "posting_cadence_days", avg_days, measured=True, unit="days",
            detail="average gap between recent Instagram publication links",
        )]

    async def _generate_recommendations(
        self,
        business_id: UUID,
        link: PublicationLink,
        score: PublicationLinkPositioningScore,
        rules: list[dict],
    ) -> None:
        # Resolve prior open recommendations for this link.
        result = await self.db.execute(
            select(PositioningRecommendation).where(
                PositioningRecommendation.link_id == link.id,
                PositioningRecommendation.status == "open",
            )
        )
        open_recs = {r.signal_key: r for r in result.scalars().all()}

        triggered_keys = {r["signal_key"] for r in rules}
        now = datetime.now(timezone.utc)

        for signal_key, rec in open_recs.items():
            if signal_key not in triggered_keys:
                rec.status = "resolved"
                rec.resolved_at = now

        for rule in rules:
            if rule["signal_key"] in open_recs:
                continue  # already open, don't duplicate
            self.db.add(PositioningRecommendation(
                business_id=business_id,
                link_id=link.id,
                score_id=score.id,
                signal_key=rule["signal_key"],
                severity=rule["severity"],
                message=rule["message"],
                current_value=rule.get("current_value"),
                target_value=rule.get("target_value"),
            ))

        await self.db.commit()

    async def get_latest_score(self, link_id: UUID) -> PublicationLinkPositioningScore | None:
        result = await self.db.execute(
            select(PublicationLinkPositioningScore)
            .where(PublicationLinkPositioningScore.link_id == link_id)
            .order_by(PublicationLinkPositioningScore.computed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_score_history(
        self, link_id: UUID, days: int = 30
    ) -> list[PublicationLinkPositioningScore]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(PublicationLinkPositioningScore)
            .where(
                PublicationLinkPositioningScore.link_id == link_id,
                PublicationLinkPositioningScore.computed_at >= cutoff,
            )
            .order_by(PublicationLinkPositioningScore.computed_at.asc())
        )
        return list(result.scalars().all())

    async def get_open_recommendations(self, link_id: UUID) -> list[PositioningRecommendation]:
        result = await self.db.execute(
            select(PositioningRecommendation).where(
                PositioningRecommendation.link_id == link_id,
                PositioningRecommendation.status == "open",
            )
        )
        return list(result.scalars().all())

    async def get_business_summary(self, business_id: UUID) -> dict:
        """Per-platform latest scores for the business, plus a generic_web
        overlay from web_presence (read-only, no table merge)."""
        result = await self.db.execute(
            select(PublicationLink).where(PublicationLink.business_id == business_id)
        )
        links = result.scalars().all()

        per_link = []
        for link in links:
            score = await self.get_latest_score(link.id)
            if score:
                per_link.append({
                    "link_id": str(link.id),
                    "title": link.title,
                    "platform_name": score.platform_name,
                    "composite_score": score.composite_score,
                    "measured_signal_pct": score.measured_signal_pct,
                    "computed_at": score.computed_at.isoformat(),
                })

        summary = {
            "business_id": str(business_id),
            "platforms": per_link,
            "generic_web": None,
        }

        try:
            from app.domains.businesses.models import Business
            from app.domains.web_presence.service import seo_report as web_presence_seo_report

            business = await self.db.get(Business, business_id)
            if business and getattr(business, "user_id", None):
                web_data = await web_presence_seo_report(self.db, business.user_id)
                if web_data:
                    summary["generic_web"] = {
                        "average_score": web_data.get("average_score"),
                        "pages_analyzed": web_data.get("pages_analyzed"),
                    }
        except Exception as e:
            logger.warning(f"Could not merge web_presence data into positioning summary: {str(e)[:150]}")

        return summary

    async def dismiss_recommendation(self, recommendation_id: UUID) -> bool:
        rec = await self.db.get(PositioningRecommendation, recommendation_id)
        if not rec:
            return False
        rec.status = "dismissed"
        await self.db.commit()
        return True
