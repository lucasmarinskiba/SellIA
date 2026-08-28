"""SEO Intelligence API — /api/v1/businesses/{business_id}/seo/*"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.cache import cached
from app.domains.seo_intelligence.schemas import (
    KeywordCreate,
    KeywordOut,
    PageOptimizationCreate,
    PageOptimizationUpdate,
    PageOptimizationOut,
    CompetitorAnalysisCreate,
    CompetitorAnalysisOut,
    SEORecommendationOut,
    SEOHealthResponse,
)
from app.domains.seo_intelligence.service import (
    KeywordService,
    PageOptimizationService,
    CompetitorAnalysisService,
    SEORecommendationService,
)
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/seo", tags=["SEO Intelligence"])


# Keywords
@router.post("/keywords", response_model=KeywordOut)
async def add_keyword(
    business_id: UUID,
    body: KeywordCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add keyword to track."""
    svc = KeywordService(db)
    return await svc.add_keyword(
        business_id,
        body.keyword,
        body.search_volume,
        body.difficulty,
        body.cpc,
        body.competition,
        body.intent,
        body.trend,
        body.platform,
    )


@router.get("/keywords", response_model=list[KeywordOut])
@cached(ttl_seconds=3600, key_prefix="keywords")
async def list_keywords(
    business_id: UUID,
    platform: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List tracked keywords (cached 1h)."""
    svc = KeywordService(db)
    return await svc.list_keywords(business_id, platform, limit)


@router.get("/keywords/trending")
@cached(ttl_seconds=900, key_prefix="trending")
async def get_trending_keywords(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get rising trend keywords (cached 15min)."""
    svc = KeywordService(db)
    keywords = await svc.get_trending_keywords(business_id)
    return {"trending_keywords": [{"keyword": k.keyword, "trend": k.trend} for k in keywords]}


# Page Optimization
@router.post("/pages", response_model=PageOptimizationOut)
async def create_page(
    business_id: UUID,
    body: PageOptimizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create page optimization record."""
    svc = PageOptimizationService(db)
    return await svc.create_page(
        business_id,
        body.page_url,
        body.page_title,
        body.page_type,
        body.meta_description,
        body.keywords_targeted,
    )


@router.patch("/pages/{page_id}", response_model=PageOptimizationOut)
async def update_page(
    business_id: UUID,
    page_id: UUID,
    body: PageOptimizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update page metrics."""
    svc = PageOptimizationService(db)
    return await svc.update_page(
        page_id,
        body.page_speed_ms,
        body.mobile_score,
        body.optimization_score,
        body.organic_traffic_30d,
        body.organic_revenue_30d,
    )


@router.get("/health", response_model=SEOHealthResponse)
@cached(ttl_seconds=3600, key_prefix="seo_health")
async def get_seo_health(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get overall SEO health (cached 1h)."""
    svc = PageOptimizationService(db)
    health = await svc.seo_health(business_id)
    return SEOHealthResponse(**health)


# Competitor Analysis
@router.post("/competitors", response_model=CompetitorAnalysisOut)
async def analyze_competitor(
    business_id: UUID,
    body: CompetitorAnalysisCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze competitor."""
    svc = CompetitorAnalysisService(db)
    return await svc.analyze_competitor(business_id, body.competitor_name, body.competitor_url)


@router.get("/competitors", response_model=list[CompetitorAnalysisOut])
@cached(ttl_seconds=3600, key_prefix="competitors")
async def list_competitors(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List analyzed competitors (cached 1h)."""
    svc = CompetitorAnalysisService(db)
    return await svc.list_competitors(business_id)


# Recommendations
@router.get("/recommendations", response_model=list[SEORecommendationOut])
async def list_recommendations(
    business_id: UUID,
    status: str | None = Query(None),
    priority: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List SEO recommendations."""
    svc = SEORecommendationService(db)
    return await svc.list_recommendations(business_id, status, priority)


@router.patch("/recommendations/{rec_id}")
async def update_recommendation_status(
    business_id: UUID,
    rec_id: UUID,
    status: str = Query(..., pattern="^(open|in_progress|completed|rejected)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update recommendation status."""
    svc = SEORecommendationService(db)
    rec = await svc.update_status(rec_id, status)
    return {"recommendation_id": rec.id, "status": rec.status}
