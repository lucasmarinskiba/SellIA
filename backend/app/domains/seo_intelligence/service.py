"""SEO Intelligence services."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_intelligence.models import (
    Keyword,
    Ranking,
    PageOptimization,
    CompetitorAnalysis,
    SEORecommendation,
)

logger = get_logger(__name__)


class KeywordService:
    """Manage keyword research and tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_keyword(
        self,
        business_id: uuid.UUID,
        keyword: str,
        search_volume: int = 0,
        difficulty: int = 0,
        cpc: Decimal = Decimal("0"),
        competition: str = "medium",
        intent: str = "commercial",
        trend: str = "stable",
        platform: str = "google",
    ) -> Keyword:
        """Add keyword to track."""
        kw = Keyword(
            business_id=business_id,
            keyword=keyword,
            search_volume=search_volume,
            difficulty=difficulty,
            cpc=cpc,
            competition=competition,
            intent=intent,
            trend=trend,
            platform=platform,
        )
        self.db.add(kw)
        await self.db.commit()
        return kw

    async def update_rank(self, keyword_id: uuid.UUID, rank: int) -> Keyword:
        """Update keyword ranking."""
        kw = (
            await self.db.execute(select(Keyword).where(Keyword.id == keyword_id))
        ).scalar_one_or_none()
        if not kw:
            raise ValueError(f"Keyword {keyword_id} not found")
        kw.current_rank = rank
        kw.tracked_at = datetime.now(timezone.utc)
        await self.db.commit()
        return kw

    async def list_keywords(
        self,
        business_id: uuid.UUID,
        platform: Optional[str] = None,
        limit: int = 100,
    ) -> list[Keyword]:
        """List tracked keywords."""
        query = select(Keyword).where(Keyword.business_id == business_id)
        if platform:
            query = query.where(Keyword.platform == platform)
        query = query.order_by(desc(Keyword.search_volume)).limit(limit)
        return (await self.db.execute(query)).scalars().all()

    async def get_trending_keywords(self, business_id: uuid.UUID) -> list[Keyword]:
        """Get rising trend keywords."""
        keywords = (
            await self.db.execute(
                select(Keyword).where(
                    and_(
                        Keyword.business_id == business_id,
                        Keyword.trend == "rising",
                    )
                )
            )
        ).scalars().all()
        return keywords


class PageOptimizationService:
    """Manage page SEO optimization."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_page(
        self,
        business_id: uuid.UUID,
        page_url: str,
        page_title: str,
        page_type: str,
        meta_description: Optional[str] = None,
        keywords_targeted: Optional[list] = None,
    ) -> PageOptimization:
        """Create page optimization record."""
        page = PageOptimization(
            business_id=business_id,
            page_url=page_url,
            page_title=page_title,
            page_type=page_type,
            meta_description=meta_description,
            keywords_targeted=keywords_targeted or [],
        )
        self.db.add(page)
        await self.db.commit()
        return page

    async def update_page(
        self,
        page_id: uuid.UUID,
        page_speed_ms: Optional[int] = None,
        mobile_score: Optional[int] = None,
        optimization_score: Optional[int] = None,
        organic_traffic_30d: Optional[int] = None,
        organic_revenue_30d: Optional[Decimal] = None,
    ) -> PageOptimization:
        """Update page metrics."""
        page = (
            await self.db.execute(
                select(PageOptimization).where(PageOptimization.id == page_id)
            )
        ).scalar_one_or_none()
        if not page:
            raise ValueError(f"Page {page_id} not found")

        if page_speed_ms is not None:
            page.page_speed_ms = page_speed_ms
        if mobile_score is not None:
            page.mobile_score = mobile_score
        if optimization_score is not None:
            page.optimization_score = optimization_score
        if organic_traffic_30d is not None:
            page.organic_traffic_30d = organic_traffic_30d
        if organic_revenue_30d is not None:
            page.organic_revenue_30d = organic_revenue_30d

        page.last_updated = datetime.now(timezone.utc)
        await self.db.commit()
        return page

    async def seo_health(self, business_id: uuid.UUID) -> dict:
        """Get overall SEO health."""
        pages = (
            await self.db.execute(
                select(PageOptimization).where(PageOptimization.business_id == business_id)
            )
        ).scalars().all()

        total_pages = len(pages)
        indexed_pages = sum(1 for p in pages if p.indexed)
        avg_speed = sum(p.page_speed_ms for p in pages) // total_pages if pages else 0
        avg_mobile = sum(p.mobile_score for p in pages) // total_pages if pages else 0
        total_traffic = sum(p.organic_traffic_30d for p in pages)
        total_revenue = sum(p.organic_revenue_30d for p in pages)

        # Critical issues: pages with low optimization score
        critical = sum(1 for p in pages if p.optimization_score < 30)
        high = sum(1 for p in pages if 30 <= p.optimization_score < 60)

        return {
            "overall_score": sum(p.optimization_score for p in pages) // total_pages if pages else 0,
            "indexed_pages": indexed_pages,
            "total_pages": total_pages,
            "avg_page_speed_ms": avg_speed,
            "avg_mobile_score": avg_mobile,
            "organic_traffic_30d": total_traffic,
            "organic_revenue_30d": float(total_revenue),
            "critical_issues": critical,
            "high_priority_issues": high,
        }


class CompetitorAnalysisService:
    """Analyze competitor SEO."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_competitor(
        self,
        business_id: uuid.UUID,
        competitor_name: str,
        competitor_url: str,
    ) -> CompetitorAnalysis:
        """Create competitor analysis."""
        analysis = CompetitorAnalysis(
            business_id=business_id,
            competitor_name=competitor_name,
            competitor_url=competitor_url,
        )
        self.db.add(analysis)
        await self.db.commit()
        logger.info(f"Competitor analysis created: {competitor_name}")
        return analysis

    async def update_analysis(
        self,
        analysis_id: uuid.UUID,
        domain_authority: int,
        backlinks: int,
        referring_domains: int,
        organic_keywords: int,
        top_keywords: Optional[list] = None,
        monthly_traffic: int = 0,
        monthly_revenue: Decimal = Decimal("0"),
    ) -> CompetitorAnalysis:
        """Update competitor metrics."""
        analysis = (
            await self.db.execute(
                select(CompetitorAnalysis).where(CompetitorAnalysis.id == analysis_id)
            )
        ).scalar_one_or_none()
        if not analysis:
            raise ValueError(f"Analysis {analysis_id} not found")

        analysis.domain_authority = domain_authority
        analysis.backlinks_count = backlinks
        analysis.referring_domains = referring_domains
        analysis.organic_keywords = organic_keywords
        analysis.top_keywords = top_keywords or []
        analysis.estimated_monthly_traffic = monthly_traffic
        analysis.estimated_monthly_revenue = monthly_revenue
        analysis.analyzed_at = datetime.now(timezone.utc)
        await self.db.commit()
        return analysis

    async def list_competitors(self, business_id: uuid.UUID) -> list[CompetitorAnalysis]:
        """List analyzed competitors."""
        competitors = (
            await self.db.execute(
                select(CompetitorAnalysis).where(CompetitorAnalysis.business_id == business_id)
                .order_by(desc(CompetitorAnalysis.domain_authority))
            )
        ).scalars().all()
        return competitors


class SEORecommendationService:
    """Generate and track SEO recommendations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_recommendation(
        self,
        business_id: uuid.UUID,
        page_optimization_id: uuid.UUID,
        recommendation_type: str,
        priority: str,
        description: str,
        current_value: Optional[str] = None,
        recommended_value: Optional[str] = None,
        potential_impact: str = "medium",
    ) -> SEORecommendation:
        """Create SEO recommendation."""
        rec = SEORecommendation(
            business_id=business_id,
            page_optimization_id=page_optimization_id,
            recommendation_type=recommendation_type,
            priority=priority,
            description=description,
            current_value=current_value,
            recommended_value=recommended_value,
            potential_impact=potential_impact,
        )
        self.db.add(rec)
        await self.db.commit()
        return rec

    async def list_recommendations(
        self,
        business_id: uuid.UUID,
        status: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> list[SEORecommendation]:
        """List recommendations."""
        query = select(SEORecommendation).where(SEORecommendation.business_id == business_id)
        if status:
            query = query.where(SEORecommendation.status == status)
        if priority:
            query = query.where(SEORecommendation.priority == priority)
        query = query.order_by(SEORecommendation.priority).order_by(
            desc(SEORecommendation.created_at)
        )
        return (await self.db.execute(query)).scalars().all()

    async def update_status(
        self,
        recommendation_id: uuid.UUID,
        status: str,
    ) -> SEORecommendation:
        """Update recommendation status."""
        rec = (
            await self.db.execute(
                select(SEORecommendation).where(SEORecommendation.id == recommendation_id)
            )
        ).scalar_one_or_none()
        if not rec:
            raise ValueError(f"Recommendation {recommendation_id} not found")
        rec.status = status
        await self.db.commit()
        return rec
