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
    BacklinkOpportunityIn,
    BacklinkOpportunityOut,
    ReviewCampaignIn,
    ReviewCampaignOut,
    ReviewAggregateOut,
)
from app.domains.seo_agents.service import (
    ContentGenerationService,
    CompetitorKeywordService,
    BacklinkStrategyService,
    ReviewOrchestrationService,
)
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


# Backlink Strategy
@router.post("/backlinks/opportunities", response_model=BacklinkOpportunityOut)
async def add_backlink_opportunity(
    business_id: UUID,
    body: BacklinkOpportunityIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Identify + score a backlink outreach opportunity."""
    svc = BacklinkStrategyService(db)
    opp = await svc.add_opportunity(
        business_id,
        body.domain,
        body.opportunity_type,
        body.domain_authority,
        body.niche_keywords,
        body.domain_topic_keywords,
        body.target_url,
        body.contact_email,
        body.contact_name,
    )
    return BacklinkOpportunityOut(
        id=opp.id,
        domain=opp.domain,
        opportunity_type=opp.opportunity_type,
        domain_authority=opp.domain_authority,
        relevance_score=opp.relevance_score,
        priority_score=opp.priority_score,
        status=opp.status,
        contact_email=opp.contact_email,
    )


@router.get("/backlinks/opportunities", response_model=list[BacklinkOpportunityOut])
@cached(ttl_seconds=3600, key_prefix="backlink_opps")
async def list_backlink_opportunities(
    business_id: UUID,
    status: str | None = Query(None),
    min_priority: float = Query(0.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List backlink opportunities ranked by priority (cached 1h)."""
    svc = BacklinkStrategyService(db)
    opps = await svc.list_opportunities(business_id, status, min_priority)
    return [
        BacklinkOpportunityOut(
            id=o.id,
            domain=o.domain,
            opportunity_type=o.opportunity_type,
            domain_authority=o.domain_authority,
            relevance_score=o.relevance_score,
            priority_score=o.priority_score,
            status=o.status,
            contact_email=o.contact_email,
        )
        for o in opps
    ]


@router.patch("/backlinks/opportunities/{opportunity_id}", response_model=BacklinkOpportunityOut)
async def update_backlink_status(
    business_id: UUID,
    opportunity_id: UUID,
    status: str = Query(..., pattern="^(identified|contacted|negotiating|acquired|rejected)$"),
    acquired_url: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update backlink outreach status."""
    svc = BacklinkStrategyService(db)
    opp = await svc.update_status(opportunity_id, status, acquired_url)
    return BacklinkOpportunityOut(
        id=opp.id,
        domain=opp.domain,
        opportunity_type=opp.opportunity_type,
        domain_authority=opp.domain_authority,
        relevance_score=opp.relevance_score,
        priority_score=opp.priority_score,
        status=opp.status,
        contact_email=opp.contact_email,
    )


# Review Orchestration
@router.post("/reviews/campaigns", response_model=ReviewCampaignOut)
async def create_review_campaign(
    business_id: UUID,
    body: ReviewCampaignIn,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a review solicitation campaign."""
    svc = ReviewOrchestrationService(db)
    campaign = await svc.create_campaign(
        business_id,
        body.customer_name,
        body.customer_email,
        body.service_type,
        body.review_platform,
        body.review_url,
    )
    return ReviewCampaignOut(
        id=campaign.id,
        customer_name=campaign.customer_name,
        service_type=campaign.service_type,
        review_platform=campaign.review_platform,
        status=campaign.status,
        rating=campaign.rating,
    )


@router.patch("/reviews/campaigns/{campaign_id}/record", response_model=ReviewCampaignOut)
async def record_review_result(
    business_id: UUID,
    campaign_id: UUID,
    rating: int = Query(..., ge=1, le=5),
    review_text: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record a completed review + refresh the business rating aggregate."""
    svc = ReviewOrchestrationService(db)
    campaign = await svc.record_review(campaign_id, rating, review_text)
    return ReviewCampaignOut(
        id=campaign.id,
        customer_name=campaign.customer_name,
        service_type=campaign.service_type,
        review_platform=campaign.review_platform,
        status=campaign.status,
        rating=campaign.rating,
    )


@router.get("/reviews/campaigns", response_model=list[ReviewCampaignOut])
async def list_review_campaigns(
    business_id: UUID,
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List review campaigns."""
    svc = ReviewOrchestrationService(db)
    campaigns = await svc.list_campaigns(business_id, status)
    return [
        ReviewCampaignOut(
            id=c.id,
            customer_name=c.customer_name,
            service_type=c.service_type,
            review_platform=c.review_platform,
            status=c.status,
            rating=c.rating,
        )
        for c in campaigns
    ]


@router.get("/reviews/aggregate", response_model=ReviewAggregateOut)
@cached(ttl_seconds=3600, key_prefix="review_aggregate")
async def get_review_aggregate(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get AggregateRating rollup (cached 1h) — feeds schema.org markup."""
    svc = ReviewOrchestrationService(db)
    aggregate = await svc.get_aggregate(business_id)
    if not aggregate:
        return ReviewAggregateOut(
            total_reviews=0,
            average_rating=0.0,
            five_star=0,
            four_star=0,
            three_star=0,
            two_star=0,
            one_star=0,
        )
    return ReviewAggregateOut(
        total_reviews=aggregate.total_reviews,
        average_rating=aggregate.average_rating,
        five_star=aggregate.five_star,
        four_star=aggregate.four_star,
        three_star=aggregate.three_star,
        two_star=aggregate.two_star,
        one_star=aggregate.one_star,
    )
