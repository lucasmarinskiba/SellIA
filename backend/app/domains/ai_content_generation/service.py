"""Phase 51: Content Generation Service."""
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, select
from app.domains.ai_content_generation.models import (
    ContentTemplate,
    GeneratedContent,
    ContentPerformance,
    BulkContentGeneration,
    ContentVariant,
)


class ContentGenerationService:
    @staticmethod
    async def create_template(
        db: AsyncSession,
        business_id: UUID,
        template_name: str,
        template_type: str,
        template_prompt: str,
        platform: Optional[str] = None,
    ) -> ContentTemplate:
        template = ContentTemplate(
            business_id=business_id,
            template_name=template_name,
            template_type=template_type,
            template_prompt=template_prompt,
            platform=platform,
        )
        db.add(template)
        await db.commit()
        await db.refresh(template)
        return template

    @staticmethod
    async def save_generated_content(
        db: AsyncSession,
        business_id: UUID,
        content_type: str,
        generated_content: str,
        product_id: Optional[UUID] = None,
        platform: Optional[str] = None,
        original_content: Optional[str] = None,
        seo_score: float = 0,
        engagement_score: float = 0,
    ) -> GeneratedContent:
        content = GeneratedContent(
            business_id=business_id,
            product_id=product_id,
            content_type=content_type,
            platform=platform,
            original_content=original_content,
            generated_content=generated_content,
            content_length=len(generated_content),
            seo_score=seo_score,
            engagement_score=engagement_score,
        )
        db.add(content)
        await db.commit()
        await db.refresh(content)
        return content

    @staticmethod
    async def create_content_variants(
        db: AsyncSession,
        business_id: UUID,
        generated_content_id: UUID,
        variants: List[dict],  # [{"text": "...", "style": "formal"}, ...]
    ) -> List[ContentVariant]:
        created = []
        for idx, variant in enumerate(variants, 1):
            cv = ContentVariant(
                business_id=business_id,
                generated_content_id=generated_content_id,
                variant_number=idx,
                variant_text=variant["text"],
                variant_style=variant.get("style", "neutral"),
                seo_score=variant.get("seo_score", 0),
                engagement_score=variant.get("engagement_score", 0),
            )
            db.add(cv)
            created.append(cv)
        await db.commit()
        return created

    @staticmethod
    async def publish_content(db: AsyncSession, content_id: UUID) -> GeneratedContent:
        result = await db.execute(
            select(GeneratedContent).where(GeneratedContent.id == content_id)
        )
        content = result.scalar()
        if content:
            content.is_approved = True
            content.is_published = True
            content.published_at = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(content)
        return content

    @staticmethod
    async def create_bulk_generation_job(
        db: AsyncSession,
        business_id: UUID,
        batch_name: str,
        content_type: str,
        product_ids: List[UUID],
        platform: Optional[str] = None,
    ) -> BulkContentGeneration:
        job = BulkContentGeneration(
            business_id=business_id,
            batch_name=batch_name,
            content_type=content_type,
            platform=platform,
            product_ids=product_ids,
            total_items=len(product_ids),
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def update_bulk_job_status(
        db: AsyncSession,
        job_id: UUID,
        status: str,
        generated_count: int = 0,
        approved_count: int = 0,
        published_count: int = 0,
        error_message: Optional[str] = None,
    ) -> BulkContentGeneration:
        result = await db.execute(
            select(BulkContentGeneration).where(BulkContentGeneration.id == job_id)
        )
        job = result.scalar()
        if job:
            job.status = status
            job.generated_count = generated_count
            job.approved_count = approved_count
            job.published_count = published_count
            if error_message:
                job.error_message = error_message
            if status == "completed":
                job.completed_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(job)
        return job

    @staticmethod
    async def track_content_performance(
        db: AsyncSession,
        business_id: UUID,
        generated_content_id: UUID,
        product_id: Optional[UUID],
        platform: str,
        views: int = 0,
        clicks: int = 0,
        conversions: int = 0,
        revenue: float = 0,
    ) -> ContentPerformance:
        perf = ContentPerformance(
            business_id=business_id,
            generated_content_id=generated_content_id,
            product_id=product_id,
            platform=platform,
            views=views,
            clicks=clicks,
            conversions=conversions,
            revenue=revenue,
        )
        if views > 0:
            perf.ctr = (clicks / views * 100) if clicks > 0 else 0
            perf.conversion_rate = (conversions / views * 100) if conversions > 0 else 0
            perf.engagement_rate = ((clicks + conversions) / views * 100) if (clicks + conversions) > 0 else 0

        db.add(perf)
        await db.commit()
        await db.refresh(perf)
        return perf

    @staticmethod
    async def get_content_by_type(
        db: AsyncSession,
        business_id: UUID,
        content_type: str,
        platform: Optional[str] = None,
        is_published: bool = True,
    ) -> List[GeneratedContent]:
        where_clause = and_(
            GeneratedContent.business_id == business_id,
            GeneratedContent.content_type == content_type,
            GeneratedContent.is_published == is_published,
        )
        if platform:
            where_clause = and_(where_clause, GeneratedContent.platform == platform)

        result = await db.execute(select(GeneratedContent).where(where_clause))
        return result.scalars().all()
