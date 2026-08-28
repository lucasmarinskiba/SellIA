"""FOMO+SEO integrated copy generation."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.fomo_seo.models import FOMOSEOCopy, A_B_TestCopy, CopyPerformanceMetric

logger = get_logger(__name__)


class FOMOSEOCopyService:
    """Generate FOMO+SEO optimized copy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_copy(
        self,
        business_id: uuid.UUID,
        product_id: Optional[uuid.UUID],
        title: str,
        meta_description: str,
        short_description: str,
        long_description: str,
        bullet_points: Optional[list] = None,
        call_to_action: str = "Buy Now",
        urgency_trigger: Optional[str] = None,
        social_proof_element: Optional[str] = None,
        scarcity_message: Optional[str] = None,
        keywords_targeted: Optional[list] = None,
        platform: str = "shopify",
    ) -> FOMOSEOCopy:
        """Create FOMO+SEO optimized copy."""
        copy = FOMOSEOCopy(
            business_id=business_id,
            product_id=product_id,
            title=title,
            meta_description=meta_description,
            short_description=short_description,
            long_description=long_description,
            bullet_points=bullet_points or [],
            call_to_action=call_to_action,
            urgency_trigger=urgency_trigger,
            social_proof_element=social_proof_element,
            scarcity_message=scarcity_message,
            keywords_targeted=keywords_targeted or [],
            platform=platform,
        )

        # Calculate SEO score (simplified)
        copy.seo_score = self._calculate_seo_score(
            title, meta_description, keywords_targeted
        )
        # Calculate FOMO/CTR score
        copy.ctr_score = self._calculate_ctr_score(
            title, urgency_trigger, social_proof_element
        )

        self.db.add(copy)
        await self.db.commit()
        logger.info(f"FOMO+SEO copy created for product {product_id}")
        return copy

    def _calculate_seo_score(
        self,
        title: str,
        meta_description: str,
        keywords: Optional[list] = None,
    ) -> float:
        """Calculate SEO optimization score (0-100)."""
        score = 0.0

        # Title length (50-60 chars optimal)
        if 50 <= len(title) <= 60:
            score += 30
        elif 30 <= len(title) < 80:
            score += 20

        # Meta description (150-160 chars optimal)
        if 150 <= len(meta_description) <= 160:
            score += 30
        elif 120 <= len(meta_description) < 180:
            score += 20

        # Keywords included
        if keywords and len(keywords) > 0:
            score += 40
        elif keywords and len(keywords) > 5:
            score += 50

        return min(score, 100)

    def _calculate_ctr_score(
        self,
        title: str,
        urgency_trigger: Optional[str] = None,
        social_proof: Optional[str] = None,
    ) -> float:
        """Calculate CTR potential score (0-100)."""
        score = 50  # baseline

        # Power words in title
        power_words = ["guaranteed", "proven", "exclusive", "limited", "special", "save"]
        if any(word in title.lower() for word in power_words):
            score += 15

        # Urgency triggers
        if urgency_trigger:
            score += 20

        # Social proof
        if social_proof:
            score += 15

        return min(score, 100)

    async def list_copy(
        self,
        business_id: uuid.UUID,
        platform: Optional[str] = None,
        status: str = "active",
    ) -> list[FOMOSEOCopy]:
        """List copy variants."""
        query = select(FOMOSEOCopy).where(
            and_(
                FOMOSEOCopy.business_id == business_id,
                FOMOSEOCopy.status == status,
            )
        )
        if platform:
            query = query.where(FOMOSEOCopy.platform == platform)
        query = query.order_by(desc(FOMOSEOCopy.seo_score))
        return (await self.db.execute(query)).scalars().all()

    async def get_copy(self, copy_id: uuid.UUID) -> FOMOSEOCopy:
        """Fetch copy."""
        copy = (
            await self.db.execute(select(FOMOSEOCopy).where(FOMOSEOCopy.id == copy_id))
        ).scalar_one_or_none()
        if not copy:
            raise ValueError(f"Copy {copy_id} not found")
        return copy


class A_B_TestService:
    """Manage FOMO+SEO copy A/B tests."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_test(
        self,
        business_id: uuid.UUID,
        copy_id: uuid.UUID,
        variant_a_title: str,
        variant_b_title: str,
        variant_a_description: str,
        variant_b_description: str,
    ) -> A_B_TestCopy:
        """Create A/B test."""
        test = A_B_TestCopy(
            business_id=business_id,
            copy_id=copy_id,
            variant_a_title=variant_a_title,
            variant_b_title=variant_b_title,
            variant_a_description=variant_a_description,
            variant_b_description=variant_b_description,
        )
        self.db.add(test)
        await self.db.commit()
        logger.info(f"A/B test created for copy {copy_id}")
        return test

    async def update_results(
        self,
        test_id: uuid.UUID,
        variant_a_impressions: int,
        variant_a_clicks: int,
        variant_a_conversions: int,
        variant_b_impressions: int,
        variant_b_clicks: int,
        variant_b_conversions: int,
    ) -> A_B_TestCopy:
        """Update test results."""
        test = (
            await self.db.execute(
                select(A_B_TestCopy).where(A_B_TestCopy.id == test_id)
            )
        ).scalar_one_or_none()
        if not test:
            raise ValueError(f"Test {test_id} not found")

        # Calculate metrics
        test.variant_a_impressions = variant_a_impressions
        test.variant_a_clicks = variant_a_clicks
        test.variant_a_conversions = variant_a_conversions
        test.variant_a_ctr = (
            (variant_a_clicks / variant_a_impressions * 100) if variant_a_impressions > 0 else 0
        )
        test.variant_a_conversion_rate = (
            (variant_a_conversions / variant_a_clicks * 100) if variant_a_clicks > 0 else 0
        )

        test.variant_b_impressions = variant_b_impressions
        test.variant_b_clicks = variant_b_clicks
        test.variant_b_conversions = variant_b_conversions
        test.variant_b_ctr = (
            (variant_b_clicks / variant_b_impressions * 100) if variant_b_impressions > 0 else 0
        )
        test.variant_b_conversion_rate = (
            (variant_b_conversions / variant_b_clicks * 100) if variant_b_clicks > 0 else 0
        )

        # Determine winner (higher conversion rate wins)
        if test.variant_a_conversion_rate > test.variant_b_conversion_rate:
            test.winner = "A"
        elif test.variant_b_conversion_rate > test.variant_a_conversion_rate:
            test.winner = "B"

        await self.db.commit()
        logger.info(f"A/B test {test_id} results: winner={test.winner}")
        return test

    async def list_tests(self, business_id: uuid.UUID) -> list[A_B_TestCopy]:
        """List active tests."""
        tests = (
            await self.db.execute(
                select(A_B_TestCopy).where(
                    and_(
                        A_B_TestCopy.business_id == business_id,
                        A_B_TestCopy.is_active,
                    )
                )
            )
        ).scalars().all()
        return tests
