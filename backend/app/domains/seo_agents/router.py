"""SEO Agents API — Phase 1: Content Generation + Keyword Gaps."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.cache import cached
from app.domains.seo_agents.schemas import (
    GenerateContentRequest,
    GeneratedContentOut,
    CompetitorKeywordGapIn,
    CompetitorKeywordGapOut,
    KeywordOpportunityOut,
)
from app.domains.seo_agents.service import ContentGenerationService, CompetitorKeywordService
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/seo-agents", tags=["SEO Agents"])


# Content Generation
@router.post("/content/generate", response_model=GeneratedContentOut)
async def generate_seo_content(
    business_id: UUID,
    body: GenerateContentRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate AI-optimized SEO content for product/service."""
    svc = ContentGenerationService(db)
    content = await svc.generate_content(
        business_id,
        body.content_type,
        body.target_keyword,
        body.product_name,
        body.product_description,
        tone=body.tone,
    )
    return GeneratedContentOut(
        id=content.id,
        product_name=content.product_name,
        target_keyword=content.target_keyword,
        title=content.title,
        meta_description=content.meta_description,
        h1=content.h1,
        seo_score=content.seo_score,
        keyword_density=content.keyword_density,
        content_length=content.content_length,
        status=content.status,
    )


@router.get("/content", response_model=list[GeneratedContentOut])
@cached(ttl_seconds=3600, key_prefix="seo_content")
async def list_generated_content(
    business_id: UUID,
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List generated content."""
    svc = ContentGenerationService(db)
    contents = await svc.list_content(business_id, status)
    return [
        GeneratedContentOut(
            id=c.id,
            product_name=c.product_name,
            target_keyword=c.target_keyword,
            title=c.title,
            meta_description=c.meta_description,
            h1=c.h1,
            seo_score=c.seo_score,
            keyword_density=c.keyword_density,
            content_length=c.content_length,
            status=c.status,
        )
        for c in contents
    ]


@router.get("/content/{content_id}")
async def get_generated_content(
    business_id: UUID,
    content_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get full generated content (including body + structure)."""
    from sqlalchemy import select

    result = await db.execute(
        select(__import__("app.domains.seo_agents.models", fromlist=["GeneratedContent"]).GeneratedContent).where(
            __import__("app.domains.seo_agents.models", fromlist=["GeneratedContent"]).GeneratedContent.id == content_id
        )
    )
    content = result.scalar_one_or_none()
    if not content:
        return {"error": "Content not found"}
    return {
        "id": content.id,
        "title": content.title,
        "meta": content.meta_description,
        "h1": content.h1,
        "body": content.body,
        "h2_sections": content.h2_sections,
        "internal_links": content.internal_links,
        "seo_score": content.seo_score,
        "keyword_density": content.keyword_density,
        "readability_score": content.readability_score,
    }


# Keyword Gap Analysis
@router.post("/keywords/analyze-gap", response_model=CompetitorKeywordGapOut)
async def analyze_keyword_gap(
    business_id: UUID,
    body: CompetitorKeywordGapIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze keyword gap vs competitors."""
    svc = CompetitorKeywordService(db)
    competitor_ranks = {
        1: body.competitor_1_rank,
        2: body.competitor_2_rank,
        3: body.competitor_3_rank,
    }
    gap = await svc.analyze_gap(
        business_id,
        body.keyword,
        body.search_volume,
        body.difficulty,
        body.business_rank,
        competitor_ranks,
    )
    return CompetitorKeywordGapOut(
        id=gap.id,
        keyword=gap.keyword,
        search_volume=gap.search_volume,
        difficulty=gap.difficulty,
        business_rank=gap.business_rank,
        competitor_1_rank=gap.competitor_1_rank,
        opportunity_score=gap.opportunity_score,
        action_taken=gap.action_taken,
    )


@router.get("/keywords/gaps", response_model=list[CompetitorKeywordGapOut])
@cached(ttl_seconds=900, key_prefix="keyword_gaps")
async def list_keyword_gaps(
    business_id: UUID,
    min_opportunity: float = Query(50.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List keyword gaps ranked by opportunity."""
    svc = CompetitorKeywordService(db)
    gaps = await svc.list_gaps(business_id, min_opportunity)
    return [
        CompetitorKeywordGapOut(
            id=g.id,
            keyword=g.keyword,
            search_volume=g.search_volume,
            difficulty=g.difficulty,
            business_rank=g.business_rank,
            competitor_1_rank=g.competitor_1_rank,
            opportunity_score=g.opportunity_score,
            action_taken=g.action_taken,
        )
        for g in gaps
    ]


@router.post("/keywords/identify-opportunities", response_model=list[KeywordOpportunityOut])
async def identify_keyword_opportunities(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Identify high-opportunity keywords from gaps."""
    gap_svc = CompetitorKeywordService(db)
    gaps = await gap_svc.list_gaps(business_id, min_opportunity=60.0)
    opportunities = await gap_svc.identify_opportunities(business_id, gaps)
    return [
        KeywordOpportunityOut(
            id=o.id,
            keyword=o.keyword,
            search_volume=o.search_volume,
            difficulty=o.difficulty,
            opportunity_score=o.opportunity_score,
            estimated_traffic=o.estimated_traffic,
            status=o.status,
        )
        for o in opportunities
    ]


@router.get("/dashboard")
@cached(ttl_seconds=3600, key_prefix="seo_agents_dashboard")
async def seo_agents_dashboard(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """SEO Agents dashboard — content stats + keyword opportunities."""
    from sqlalchemy import select, func

    GeneratedContent = __import__("app.domains.seo_agents.models", fromlist=["GeneratedContent"]).GeneratedContent
    KeywordOpportunity = __import__("app.domains.seo_agents.models", fromlist=["KeywordOpportunity"]).KeywordOpportunity

    # Content stats
    content_count = (
        await db.execute(
            select(func.count(GeneratedContent.id)).where(GeneratedContent.business_id == business_id)
        )
    ).scalar()
    avg_seo_score = (
        await db.execute(
            select(func.avg(GeneratedContent.seo_score)).where(GeneratedContent.business_id == business_id)
        )
    ).scalar() or 0

    # Opportunity stats
    total_opportunities = (
        await db.execute(
            select(func.count(KeywordOpportunity.id)).where(KeywordOpportunity.business_id == business_id)
        )
    ).scalar()
    total_traffic_potential = (
        await db.execute(
            select(func.sum(KeywordOpportunity.estimated_traffic)).where(KeywordOpportunity.business_id == business_id)
        )
    ).scalar() or 0

    return {
        "content_generated": content_count,
        "avg_seo_score": round(avg_seo_score, 1),
        "keyword_opportunities": total_opportunities,
        "estimated_monthly_traffic": total_traffic_potential,
    }
