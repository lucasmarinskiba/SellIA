"""FOMO decay detection + smart rotation."""

from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_config.models import PublicationLink, PublicationLinkFOMO
from app.domains.seo_config.fomo_models import FOMADecayLog
from app.domains.seo_config.analytics_models import PublicationLinkMetrics

logger = get_logger(__name__)


class FOMADecayService:
    """Detect and handle FOMO copy decay."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def detect_decay(
        self,
        link_id: UUID,
        decay_threshold_pct: float = 30.0,
        lookback_days: int = 7,
    ) -> dict | None:
        """Detect if FOMO copy CTR has decayed below threshold.

        Args:
            link_id: Publication link to check
            decay_threshold_pct: % drop to trigger decay (default 30%)
            lookback_days: Days to look back for previous performance

        Returns:
            Decay info if detected, None otherwise
        """
        today = datetime.utcnow().date()
        week_ago = today - timedelta(days=lookback_days)

        # Get current metrics (last 2 days avg)
        result = await self.db.execute(
            select(func.avg(PublicationLinkMetrics.ctr).label("avg_ctr"))
            .where(
                PublicationLinkMetrics.link_id == link_id,
                PublicationLinkMetrics.metric_date >= today - timedelta(days=2),
            )
        )
        current_ctr = result.scalar() or 0.0

        # Get baseline (7 days before)
        result = await self.db.execute(
            select(func.avg(PublicationLinkMetrics.ctr).label("avg_ctr"))
            .where(
                PublicationLinkMetrics.link_id == link_id,
                PublicationLinkMetrics.metric_date >= week_ago - timedelta(days=7),
                PublicationLinkMetrics.metric_date < week_ago,
            )
        )
        baseline_ctr = result.scalar() or current_ctr

        if baseline_ctr == 0:
            return None

        decay_pct = ((baseline_ctr - current_ctr) / baseline_ctr) * 100

        if decay_pct < decay_threshold_pct:
            return None

        # Decay detected
        return {
            "link_id": str(link_id),
            "baseline_ctr": float(baseline_ctr),
            "current_ctr": float(current_ctr),
            "decay_percentage": float(decay_pct),
            "detected_at": datetime.utcnow().isoformat(),
        }

    async def log_decay_and_regenerate(
        self,
        business_id: UUID,
        link_id: UUID,
        baseline_ctr: float,
        current_ctr: float,
        decay_pct: float,
        action: str = "regenerate",
    ) -> FOMADecayLog:
        """Log decay and mark for regeneration."""
        log = FOMADecayLog(
            business_id=business_id,
            link_id=link_id,
            fomo_id=None,  # Will be set if we regenerate
            previous_ctr=baseline_ctr,
            current_ctr=current_ctr,
            decay_percentage=decay_pct,
            action=action,
        )
        self.db.add(log)
        await self.db.commit()
        await self.db.refresh(log)

        logger.info(f"Logged decay for link {link_id}: {decay_pct:.1f}% drop")
        return log

    async def get_decay_history(
        self,
        business_id: UUID,
        limit: int = 50,
    ) -> list[FOMADecayLog]:
        """Get decay history for business."""
        result = await self.db.execute(
            select(FOMADecayLog)
            .where(FOMADecayLog.business_id == business_id)
            .order_by(desc(FOMADecayLog.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_links_with_decay(
        self,
        business_id: UUID,
        decay_threshold_pct: float = 30.0,
    ) -> list[dict]:
        """Get all links for business with detected decay."""
        # Get all active links
        result = await self.db.execute(
            select(PublicationLink)
            .where(
                PublicationLink.business_id == business_id,
                PublicationLink.seo_enabled == True,
            )
        )
        links = result.scalars().all()

        decayed = []
        for link in links:
            decay_info = await self.detect_decay(
                link.id,
                decay_threshold_pct=decay_threshold_pct,
            )
            if decay_info:
                decayed.append({
                    "link": {
                        "id": str(link.id),
                        "url": link.url,
                        "title": link.title,
                        "platform": link.platform_source,
                    },
                    **decay_info,
                })

        return decayed
