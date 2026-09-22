"""FOMO testing, preview, and conversion tracking service."""

from uuid import UUID
from datetime import datetime, timedelta
from sqlalchemy import select, func, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_config.models import PublicationLink, PublicationLinkFOMO
from app.domains.seo_config.fomo_models import ConversionEvent, FOMABTest, FOMADecayLog
from app.domains.seo_config.analytics_models import PublicationLinkMetrics

logger = get_logger(__name__)


class FOMAConversionService:
    """Handle conversion tracking and FOMO metrics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_conversion(
        self,
        business_id: UUID,
        link_id: UUID,
        platform_name: str,
        conversion_type: str = "purchase",
        conversion_value: float = 0.0,
        external_listing_id: str | None = None,
        external_event_id: str | None = None,
        fomo_variant_id: UUID | None = None,
        raw_event_data: dict | None = None,
    ) -> ConversionEvent | None:
        """Log a conversion event.

        When `external_event_id` is given (a stable per-event id from the
        source, e.g. Mercado Libre's order id), duplicates are rejected by a
        partial unique index on (business_id, platform_name,
        external_listing_id, external_event_id) rather than a check-then-insert
        race — a caller-side "does this exist?" SELECT can't see a concurrent
        insert that hasn't committed yet, which used to let two notifications
        for the same order both record a sale. Returns None (and rolls back)
        when the DB rejects it as a duplicate; the caller decides whether that's
        worth logging.

        The rollback expires every ORM object this session has loaded, not
        just this one — a caller sharing `db` across a request (the normal
        FastAPI pattern) must re-fetch, or snapshot plain values before this
        call, before touching any other object it already loaded.
        """
        event = ConversionEvent(
            business_id=business_id,
            link_id=link_id,
            platform_name=platform_name,
            conversion_type=conversion_type,
            conversion_value=conversion_value,
            external_listing_id=external_listing_id,
            external_event_id=external_event_id,
            fomo_variant_id=fomo_variant_id,
            raw_event_data=raw_event_data or {},
        )
        self.db.add(event)
        try:
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            logger.info(f"Duplicate conversion ignored: {link_id} on {platform_name} ({external_event_id})")
            return None
        await self.db.refresh(event)

        logger.info(f"Logged conversion: {link_id} on {platform_name}")
        return event

    async def get_recent_conversions(
        self,
        business_id: UUID,
        limit: int = 10,
        hours_back: int = 24,
    ) -> list[ConversionEvent]:
        """Get recent conversions for ticker."""
        cutoff = datetime.utcnow() - timedelta(hours=hours_back)

        result = await self.db.execute(
            select(ConversionEvent)
            .where(
                ConversionEvent.business_id == business_id,
                ConversionEvent.created_at >= cutoff,
            )
            .order_by(desc(ConversionEvent.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_urgency_metrics(
        self,
        business_id: UUID,
    ) -> dict:
        """Get CTR breakdown by urgency trigger type."""
        # Get all FOMO entries with urgency triggers for this business
        result = await self.db.execute(
            select(
                PublicationLinkFOMO.urgency_trigger,
                func.count(ConversionEvent.id).label("conversions"),
                func.avg(PublicationLinkMetrics.ctr).label("avg_ctr"),
            )
            .join(
                ConversionEvent,
                ConversionEvent.fomo_variant_id == PublicationLinkFOMO.id,
            )
            .join(
                PublicationLinkMetrics,
                PublicationLinkMetrics.link_id == PublicationLinkFOMO.link_id,
            )
            .where(PublicationLinkFOMO.business_id == business_id)
            .group_by(PublicationLinkFOMO.urgency_trigger)
            .order_by(desc("avg_ctr"))
        )

        metrics = result.all()
        return {
            "triggers": [
                {
                    "trigger": m[0] or "none",
                    "conversions": m[1],
                    "avg_ctr": float(m[2]) if m[2] else 0.0,
                }
                for m in metrics
            ],
        }

    async def get_fomo_preview(
        self,
        link_id: UUID,
    ) -> dict | None:
        """Get FOMO preview: original vs FOMO copy."""
        link = await self.db.execute(
            select(PublicationLink).where(PublicationLink.id == link_id)
        )
        link_obj = link.scalar_one_or_none()

        if not link_obj:
            return None

        # Get latest FOMO
        fomo_result = await self.db.execute(
            select(PublicationLinkFOMO)
            .where(PublicationLinkFOMO.link_id == link_id)
            .order_by(desc(PublicationLinkFOMO.created_at))
            .limit(1)
        )
        fomo_obj = fomo_result.scalar_one_or_none()

        return {
            "link": {
                "id": str(link_obj.id),
                "title": link_obj.title,
                "url": link_obj.url,
                "platform": link_obj.platform_source,
            },
            "original": {
                "title": link_obj.title,
                "description": "Sin FOMO (original listing description)",
            },
            "with_fomo": {
                "title": link_obj.title,
                "urgency_trigger": fomo_obj.urgency_trigger if fomo_obj else None,
                "scarcity_message": fomo_obj.scarcity_message if fomo_obj else None,
                "call_to_action": fomo_obj.call_to_action if fomo_obj else None,
                "full_copy": fomo_obj.generated_copy if fomo_obj else None,
                "fomo_score": float(fomo_obj.fomo_score) if fomo_obj else 0.0,
            },
        }
