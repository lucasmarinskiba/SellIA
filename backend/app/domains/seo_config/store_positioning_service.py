"""Store-level (storefront / brand presence) positioning score.

Where PositioningScoreService scores one listing at a time, this scores the
seller's whole storefront on a platform that has one (today: an Amazon Brand
Store). Scope is business + platform, never a link.

Credential note: the Amazon store connector authenticates with the Amazon ADS
API, not SP-API. The `connection_id` passed to compute_store_score() must be
the IntegrationConnection that holds Ads API credentials — connecting SP-API
for per-listing scoring does not grant Brand Store access, and this service
cannot tell the two apart (IntegrationConnection has no platform column and
nothing cross-checks connection vs platform; same pre-existing gap as the
link-level service).
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_config.agent_guard import SEOAgentGuard
from app.domains.seo_config.platform_store_ranking_amazon import AmazonStoreRankingConnector
from app.domains.seo_config.platform_store_ranking_base import StorePositioningConnector
from app.domains.seo_config.positioning_models import PositioningRecommendation, StorePositioningScore
from app.domains.seo_config.positioning_scoring_utils import composite_from_sub_scores, measured_pct

logger = get_logger(__name__)

# Mercado Libre "Tienda Oficial" is intentionally absent — no public analytics API
# was confirmed. See platform_store_ranking_base.py.
STORE_RANKING_CONNECTORS = {
    "amazon": AmazonStoreRankingConnector,
}


class StorePositioningScoreService:
    """Compute and persist store-level positioning scores."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_store_connector(
        self, platform_name: str, connection_id: UUID
    ) -> StorePositioningConnector | None:
        if platform_name not in STORE_RANKING_CONNECTORS:
            logger.warning(f"No store ranking connector for platform: {platform_name}")
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

            credentials = dict(connection.auth_metadata or {})
            if connection.auth_token:
                credentials["access_token"] = connection.auth_token

            connector = STORE_RANKING_CONNECTORS[platform_name](credentials)
            if not await connector.validate_credentials():
                logger.error(f"Store ranking credentials invalid for {platform_name}")
                return None
            return connector

        except Exception as e:
            logger.error(f"Error getting store ranking connector: {str(e)[:200]}")
            return None

    async def compute_store_score(
        self,
        business_id: UUID,
        platform_name: str,
        connection_id: UUID,
        external_id: str | None = None,
    ) -> StorePositioningScore | None:
        guard = SEOAgentGuard(self.db)
        if not await guard.can_run_seo_agent(business_id, "store_positioning", platform_id=connection_id):
            return None

        connector = await self.get_store_connector(platform_name, connection_id)
        if not connector:
            return None

        try:
            signals = await connector.get_store_signals(external_id)
        except Exception as e:
            logger.error(f"Failed to fetch store signals for {business_id}/{platform_name}: {str(e)[:200]}")
            return None

        signal_map = {s.key: s for s in signals}
        sub_scores = connector.score_signals(signal_map)
        composite = composite_from_sub_scores(sub_scores)
        measured = measured_pct(signals)

        score = StorePositioningScore(
            business_id=business_id,
            platform_name=platform_name,
            composite_score=composite,
            raw_signals={"signals": [s.as_dict() for s in signals]},
            measured_signal_pct=measured,
            **sub_scores,
        )
        self.db.add(score)
        await self.db.commit()
        await self.db.refresh(score)

        await self._generate_store_recommendations(
            business_id, platform_name, score, connector.recommendation_rules(signal_map)
        )

        logger.info(
            f"Store positioning score computed for {business_id}/{platform_name}: "
            f"composite={composite:.1f}, measured={measured:.0f}%"
        )
        return score

    def _open_store_recommendations_query(self, business_id: UUID, platform_name: str):
        return (
            select(PositioningRecommendation)
            .join(StorePositioningScore, PositioningRecommendation.store_score_id == StorePositioningScore.id)
            .where(
                StorePositioningScore.business_id == business_id,
                StorePositioningScore.platform_name == platform_name,
                PositioningRecommendation.status == "open",
            )
        )

    async def _generate_store_recommendations(
        self,
        business_id: UUID,
        platform_name: str,
        score: StorePositioningScore,
        rules: list[dict],
    ) -> None:
        result = await self.db.execute(self._open_store_recommendations_query(business_id, platform_name))
        open_recs = {r.signal_key: r for r in result.scalars().all()}

        triggered_keys = {r["signal_key"] for r in rules}
        now = datetime.now(timezone.utc)

        for signal_key, rec in open_recs.items():
            if signal_key not in triggered_keys:
                rec.status = "resolved"
                rec.resolved_at = now

        for rule in rules:
            if rule["signal_key"] in open_recs:
                continue
            self.db.add(PositioningRecommendation(
                business_id=business_id,
                link_id=None,
                store_score_id=score.id,
                signal_key=rule["signal_key"],
                severity=rule["severity"],
                message=rule["message"],
                current_value=rule.get("current_value"),
                target_value=rule.get("target_value"),
            ))

        await self.db.commit()

    async def get_latest_store_score(
        self, business_id: UUID, platform_name: str
    ) -> StorePositioningScore | None:
        result = await self.db.execute(
            select(StorePositioningScore)
            .where(
                StorePositioningScore.business_id == business_id,
                StorePositioningScore.platform_name == platform_name,
            )
            .order_by(StorePositioningScore.computed_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_store_score_history(
        self, business_id: UUID, platform_name: str, days: int = 30
    ) -> list[StorePositioningScore]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        result = await self.db.execute(
            select(StorePositioningScore)
            .where(
                StorePositioningScore.business_id == business_id,
                StorePositioningScore.platform_name == platform_name,
                StorePositioningScore.computed_at >= cutoff,
            )
            .order_by(StorePositioningScore.computed_at.asc())
        )
        return list(result.scalars().all())

    async def get_open_store_recommendations(
        self, business_id: UUID, platform_name: str
    ) -> list[PositioningRecommendation]:
        result = await self.db.execute(self._open_store_recommendations_query(business_id, platform_name))
        return list(result.scalars().all())

    async def has_declared_storefront(self, business_id: UUID) -> dict:
        """Read-only overlay from web_presence: does the business have a link
        marked is_primary (its site, or its main store when it has no site)?
        No table merge — same principle as generic_web in the link-level summary."""
        out = {"has_declared_storefront": False, "primary_link_url": None, "primary_link_platform": None}
        try:
            from app.domains.businesses.models import Business
            from app.domains.web_presence.models import BusinessLink

            business = await self.db.get(Business, business_id)
            if not business:
                return out
            result = await self.db.execute(
                select(BusinessLink)
                .where(BusinessLink.user_id == business.user_id, BusinessLink.is_primary.is_(True))
                .limit(1)
            )
            link = result.scalar_one_or_none()
            if link:
                out.update(
                    has_declared_storefront=True,
                    primary_link_url=link.url,
                    primary_link_platform=link.platform,
                )
        except Exception as e:
            logger.warning(f"Could not read web_presence primary link: {str(e)[:150]}")
        return out
