"""
FOMO Engine Service - Star Player Logic
"""

from typing import Optional, List
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, func, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.fomo.models import (
    FOMOCampaign,
    FOMOEvent,
    FOMOABTest,
    FOMOMetric,
    SocialProofEvent,
)


class FOMOService:
    @staticmethod
    async def create_campaign(
        db: AsyncSession,
        user_id: UUID,
        name: str,
        campaign_type: str,
        headline: str,
        config: dict,
        trigger_type: Optional[str] = None,
        **kwargs,
    ) -> FOMOCampaign:
        campaign = FOMOCampaign(
            user_id=user_id,
            name=name,
            campaign_type=campaign_type,
            headline=headline,
            config=config,
            trigger_type=trigger_type,
            status='draft',
            **kwargs,
        )
        db.add(campaign)
        await db.flush()
        return campaign

    @staticmethod
    async def activate_campaign(db: AsyncSession, campaign_id: UUID) -> FOMOCampaign:
        stmt = select(FOMOCampaign).where(FOMOCampaign.id == campaign_id)
        campaign = await db.scalar(stmt)
        if not campaign:
            raise ValueError(f"Campaign {campaign_id} not found")
        campaign.status = 'active'
        campaign.is_active = True
        campaign.updated_at = datetime.now(timezone.utc)
        await db.flush()
        return campaign

    @staticmethod
    async def get_campaigns(db: AsyncSession, user_id: UUID) -> List[FOMOCampaign]:
        stmt = select(FOMOCampaign).where(FOMOCampaign.user_id == user_id).order_by(FOMOCampaign.created_at.desc())
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_campaign(db: AsyncSession, campaign_id: UUID) -> Optional[FOMOCampaign]:
        stmt = select(FOMOCampaign).where(FOMOCampaign.id == campaign_id)
        return await db.scalar(stmt)

    # ========== EVENT LOGGING ==========
    @staticmethod
    async def log_event(
        db: AsyncSession,
        campaign_id: UUID,
        event_type: str,
        customer_id: Optional[UUID] = None,
        product_id: Optional[UUID] = None,
        metadata: Optional[dict] = None,
    ) -> FOMOEvent:
        event = FOMOEvent(
            campaign_id=campaign_id,
            event_type=event_type,
            customer_id=customer_id,
            product_id=product_id,
            event_metadata=metadata or {},
        )
        db.add(event)
        await db.flush()
        return event

    @staticmethod
    async def get_recent_events(db: AsyncSession, campaign_id: UUID, limit: int = 10) -> List[FOMOEvent]:
        stmt = (
            select(FOMOEvent)
            .where(FOMOEvent.campaign_id == campaign_id)
            .order_by(FOMOEvent.created_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return result.scalars().all()

    @staticmethod
    async def get_event_count(
        db: AsyncSession,
        campaign_id: UUID,
        event_type: Optional[str] = None,
        hours: int = 24,
    ) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        where_clause = [FOMOEvent.campaign_id == campaign_id, FOMOEvent.created_at > cutoff]
        if event_type:
            where_clause.append(FOMOEvent.event_type == event_type)

        stmt = select(func.count(FOMOEvent.id)).where(and_(*where_clause))
        result = await db.scalar(stmt)
        return result or 0

    # ========== A/B TESTING ==========
    @staticmethod
    async def create_ab_test(
        db: AsyncSession,
        campaign_id: UUID,
        variant_a: dict,
        variant_b: dict,
    ) -> FOMOABTest:
        test = FOMOABTest(
            campaign_id=campaign_id,
            variant_a=variant_a,
            variant_b=variant_b,
            status='running',
        )
        db.add(test)
        await db.flush()
        return test

    @staticmethod
    async def record_ab_test_view(db: AsyncSession, test_id: UUID, variant: str) -> None:
        stmt = select(FOMOABTest).where(FOMOABTest.id == test_id)
        test = await db.scalar(stmt)
        if not test:
            raise ValueError(f"Test {test_id} not found")

        if variant == 'A':
            test.variant_a_views += 1
        elif variant == 'B':
            test.variant_b_views += 1
        await db.flush()

    @staticmethod
    async def record_ab_test_conversion(db: AsyncSession, test_id: UUID, variant: str) -> None:
        stmt = select(FOMOABTest).where(FOMOABTest.id == test_id)
        test = await db.scalar(stmt)
        if not test:
            raise ValueError(f"Test {test_id} not found")

        if variant == 'A':
            test.variant_a_conversions += 1
        elif variant == 'B':
            test.variant_b_conversions += 1
        await db.flush()

    @staticmethod
    async def get_ab_test_stats(db: AsyncSession, test_id: UUID) -> dict:
        stmt = select(FOMOABTest).where(FOMOABTest.id == test_id)
        test = await db.scalar(stmt)
        if not test:
            raise ValueError(f"Test {test_id} not found")

        rate_a = test.variant_a_conversions / test.variant_a_views if test.variant_a_views > 0 else 0
        rate_b = test.variant_b_conversions / test.variant_b_views if test.variant_b_views > 0 else 0

        winner = None
        if rate_a > rate_b * 1.1:
            winner = 'A'
        elif rate_b > rate_a * 1.1:
            winner = 'B'

        return {
            'variant_a': {
                'views': test.variant_a_views,
                'conversions': test.variant_a_conversions,
                'rate': float(rate_a),
            },
            'variant_b': {
                'views': test.variant_b_views,
                'conversions': test.variant_b_conversions,
                'rate': float(rate_b),
            },
            'winner': winner,
        }

    # ========== METRICS & ANALYTICS ==========
    @staticmethod
    async def record_metric(
        db: AsyncSession,
        campaign_id: UUID,
        event_type: str,  # 'impression' | 'conversion'
        revenue: Optional[Decimal] = None,
    ) -> None:
        today = datetime.now(timezone.utc).date()

        stmt = select(FOMOMetric).where(
            and_(
                FOMOMetric.campaign_id == campaign_id,
                FOMOMetric.date == today,
            )
        )
        metric = await db.scalar(stmt)

        if not metric:
            metric = FOMOMetric(campaign_id=campaign_id, date=today)
            db.add(metric)
            await db.flush()

        if event_type == 'impression':
            metric.impressions += 1
        elif event_type == 'conversion':
            metric.conversions += 1
            if revenue:
                metric.revenue += revenue

        await db.flush()

    @staticmethod
    async def get_metrics(db: AsyncSession, campaign_id: UUID, days: int = 30) -> List[dict]:
        cutoff = datetime.now(timezone.utc).date() - timedelta(days=days)

        stmt = (
            select(FOMOMetric)
            .where(
                and_(
                    FOMOMetric.campaign_id == campaign_id,
                    FOMOMetric.date >= cutoff,
                )
            )
            .order_by(FOMOMetric.date.desc())
        )
        result = await db.execute(stmt)
        metrics = result.scalars().all()

        return [
            {
                'date': m.date.isoformat(),
                'impressions': m.impressions,
                'conversions': m.conversions,
                'revenue': float(m.revenue),
                'conversion_rate': (m.conversions / m.impressions * 100) if m.impressions > 0 else 0,
                'aov': float(m.revenue / m.conversions) if m.conversions > 0 else 0,
            }
            for m in metrics
        ]

    @staticmethod
    async def get_summary_metrics(db: AsyncSession, campaign_id: UUID) -> dict:
        stmt = select(
            func.sum(FOMOMetric.conversions).label('total_conversions'),
            func.sum(FOMOMetric.revenue).label('total_revenue'),
            func.avg(
                FOMOMetric.conversions / func.nullif(FOMOMetric.impressions, 0)
            ).label('avg_conversion_rate'),
        ).where(FOMOMetric.campaign_id == campaign_id)

        result = await db.execute(stmt)
        row = result.first()

        total_conversions = row[0] or 0
        total_revenue = float(row[1] or 0)
        avg_cr = float((row[2] or 0) * 100)

        return {
            'total_conversions': total_conversions,
            'total_revenue': total_revenue,
            'avg_conversion_rate': avg_cr,
            'avg_aov': total_revenue / total_conversions if total_conversions > 0 else 0,
        }

    @staticmethod
    async def get_active_campaigns(db: AsyncSession, page_path: Optional[str] = None, plan_id: Optional[str] = None) -> List[FOMOCampaign]:
        """Get campaigns active for a given page."""
        now = datetime.now(timezone.utc)
        query = select(FOMOCampaign).where(
            and_(
                FOMOCampaign.is_active == True,
                FOMOCampaign.status == 'active',
            )
        )
        if page_path:
            query = query.where(FOMOCampaign.show_on_pages.contains([page_path]))
        result = await db.execute(query.order_by(desc(FOMOCampaign.created_at)))
        campaigns = result.scalars().all()

        active = []
        for c in campaigns:
            if c.ends_at and c.ends_at < now:
                continue
            if c.total_spots and c.spots_taken >= c.total_spots:
                continue
            active.append(c)
        return active

    @staticmethod
    async def get_recent_social_proof(db: AsyncSession, limit: int = 10) -> List[SocialProofEvent]:
        result = await db.execute(
            select(SocialProofEvent)
            .order_by(desc(SocialProofEvent.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def create_social_proof_event(db: AsyncSession, data: dict) -> SocialProofEvent:
        event = SocialProofEvent(**data)
        db.add(event)
        await db.commit()
        await db.refresh(event)
        return event


fomo_service = FOMOService()
