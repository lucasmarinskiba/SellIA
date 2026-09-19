"""A/B testing service for FOMO copy variants."""

from uuid import UUID
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_config.models import PublicationLink, PublicationLinkFOMO
from app.domains.seo_config.fomo_models import FOMABTest, ConversionEvent

logger = get_logger(__name__)


class FOMABTestService:
    """Manage FOMO A/B tests and winner detection."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ab_test(
        self,
        business_id: UUID,
        link_id: UUID,
        variant_a_id: UUID,
        variant_b_id: UUID,
        variant_c_id: UUID | None = None,
        min_conversions: int = 100,
    ) -> FOMABTest:
        """Create new A/B test for FOMO variants."""
        # Validate variants exist
        variants = await self.db.execute(
            select(PublicationLinkFOMO).where(
                PublicationLinkFOMO.id.in_([variant_a_id, variant_b_id] + ([variant_c_id] if variant_c_id else []))
            )
        )
        if len(variants.scalars().all()) < 2:
            raise ValueError("Invalid variant IDs")

        test = FOMABTest(
            business_id=business_id,
            link_id=link_id,
            variant_a_id=variant_a_id,
            variant_b_id=variant_b_id,
            variant_c_id=variant_c_id,
            variant_a_split=0.20,
            variant_b_split=0.20,
            variant_c_split=0.60 if variant_c_id else 0.00,
            status="running",
            min_conversions_for_winner=min_conversions,
        )
        self.db.add(test)
        await self.db.commit()
        await self.db.refresh(test)

        logger.info(f"Created A/B test {test.id} for link {link_id}")
        return test

    async def get_test(self, test_id: UUID) -> FOMABTest | None:
        """Get test by ID."""
        result = await self.db.execute(
            select(FOMABTest).where(FOMABTest.id == test_id)
        )
        return result.scalar_one_or_none()

    async def list_running_tests(self, business_id: UUID) -> list[FOMABTest]:
        """Get all running A/B tests for business."""
        result = await self.db.execute(
            select(FOMABTest).where(
                FOMABTest.business_id == business_id,
                FOMABTest.status == "running",
            )
        )
        return result.scalars().all()

    async def check_and_announce_winner(self, test_id: UUID) -> FOMABTest | None:
        """Check if test has enough conversions to declare winner."""
        test = await self.get_test(test_id)
        if not test or test.status != "running":
            return None

        # Count conversions per variant
        variants = [test.variant_a_id, test.variant_b_id]
        if test.variant_c_id:
            variants.append(test.variant_c_id)

        results = await self.db.execute(
            select(
                ConversionEvent.fomo_variant_id,
                func.count(ConversionEvent.id).label("count"),
            )
            .where(ConversionEvent.fomo_variant_id.in_(variants))
            .group_by(ConversionEvent.fomo_variant_id)
        )

        variant_counts = {row[0]: row[1] for row in results.all()}
        test.total_conversions = sum(variant_counts.values())

        # Check if minimum reached
        if test.total_conversions < test.min_conversions_for_winner:
            await self.db.commit()
            return test

        # Find winner (highest conversion count)
        winner_id = max(variant_counts, key=variant_counts.get) if variant_counts else test.variant_a_id

        test.winner_variant_id = winner_id
        test.status = "completed"
        test.winner_announced_at = datetime.utcnow()
        test.ended_at = datetime.utcnow()

        self.db.add(test)
        await self.db.commit()
        await self.db.refresh(test)

        logger.info(
            f"A/B test {test_id} completed. Winner: {winner_id} with {variant_counts.get(winner_id, 0)} conversions"
        )
        return test

    async def apply_winner_to_link(self, test_id: UUID) -> PublicationLink | None:
        """Apply winning FOMO variant to the publication link."""
        test = await self.get_test(test_id)
        if not test or not test.winner_variant_id:
            logger.warning(f"Cannot apply winner for test {test_id}: no winner")
            return None

        # Get link and winner FOMO
        link_result = await self.db.execute(
            select(PublicationLink).where(PublicationLink.id == test.link_id)
        )
        link = link_result.scalar_one_or_none()

        winner_fomo = await self.db.execute(
            select(PublicationLinkFOMO).where(
                PublicationLinkFOMO.id == test.winner_variant_id
            )
        )
        winner = winner_fomo.scalar_one_or_none()

        if not link or not winner:
            return None

        # In production: would sync winner copy to actual platform here
        # For now: just log + return link
        logger.info(
            f"Applied winner FOMO {test.winner_variant_id} to link {link.id}"
        )

        return link

    async def get_test_metrics(self, test_id: UUID) -> dict:
        """Get detailed metrics for A/B test."""
        test = await self.get_test(test_id)
        if not test:
            return {}

        variants = [test.variant_a_id, test.variant_b_id]
        if test.variant_c_id:
            variants.append(test.variant_c_id)

        results = await self.db.execute(
            select(
                ConversionEvent.fomo_variant_id,
                func.count(ConversionEvent.id).label("conversions"),
                func.sum(ConversionEvent.conversion_value).label("revenue"),
            )
            .where(ConversionEvent.fomo_variant_id.in_(variants))
            .group_by(ConversionEvent.fomo_variant_id)
        )

        variant_data = {row[0]: {"conversions": row[1], "revenue": float(row[2] or 0)} for row in results.all()}

        return {
            "test_id": str(test.id),
            "status": test.status,
            "min_conversions": test.min_conversions_for_winner,
            "total_conversions": test.total_conversions,
            "variant_a": {
                "id": str(test.variant_a_id),
                "split": test.variant_a_split,
                **variant_data.get(test.variant_a_id, {"conversions": 0, "revenue": 0.0}),
            },
            "variant_b": {
                "id": str(test.variant_b_id),
                "split": test.variant_b_split,
                **variant_data.get(test.variant_b_id, {"conversions": 0, "revenue": 0.0}),
            },
            "variant_c": (
                {
                    "id": str(test.variant_c_id),
                    "split": test.variant_c_split,
                    **variant_data.get(test.variant_c_id, {"conversions": 0, "revenue": 0.0}),
                } if test.variant_c_id else None
            ),
            "winner_id": str(test.winner_variant_id) if test.winner_variant_id else None,
            "winner_announced_at": test.winner_announced_at.isoformat() if test.winner_announced_at else None,
        }
