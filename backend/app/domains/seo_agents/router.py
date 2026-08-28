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
    GenerateCalendarRequest,
    ContentCalendarEntryOut,
    CreateEntityRequest,
    EntitySignalOut,
    CreateLocationRequest,
    LocationSEOProfileOut,
    CitationConsistencyReportOut,
    CreateClusterRequest,
    TopicalClusterOut,
)
from app.domains.seo_agents.service import (
    ContentGenerationService,
    CompetitorKeywordService,
    BacklinkStrategyService,
    ReviewOrchestrationService,
    ContentCalendarService,
    EntityOptimizationService,
    MultiLocationSEOService,
    TopicalClusterService,
)
from app.domains.seo_agents.orchestrator import SEOAuditOrchestrator
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


# Content Calendar
@router.post("/calendar/generate", response_model=list[ContentCalendarEntryOut])
async def generate_content_calendar(
    business_id: UUID,
    body: GenerateCalendarRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a content calendar spaced across a rolling window."""
    svc = ContentCalendarService(db)
    entries = await svc.generate_calendar(
        business_id,
        body.target_keywords,
        body.days,
        body.cadence_days,
        body.keyword_opportunities,
    )
    return [
        ContentCalendarEntryOut(
            id=e.id,
            title=e.title,
            content_type=e.content_type,
            target_keyword=e.target_keyword,
            priority=e.priority,
            planned_date=e.planned_date.isoformat(),
            status=e.status,
            seo_target_score=e.seo_target_score,
        )
        for e in entries
    ]


@router.get("/calendar", response_model=list[ContentCalendarEntryOut])
@cached(ttl_seconds=1800, key_prefix="content_calendar")
async def list_content_calendar(
    business_id: UUID,
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List calendar entries in publication order (cached 30min)."""
    svc = ContentCalendarService(db)
    entries = await svc.list_calendar(business_id, status)
    return [
        ContentCalendarEntryOut(
            id=e.id,
            title=e.title,
            content_type=e.content_type,
            target_keyword=e.target_keyword,
            priority=e.priority,
            planned_date=e.planned_date.isoformat(),
            status=e.status,
            seo_target_score=e.seo_target_score,
        )
        for e in entries
    ]


@router.get("/calendar/upcoming", response_model=list[ContentCalendarEntryOut])
async def upcoming_calendar_entries(
    business_id: UUID,
    within_days: int = Query(7),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Entries due within the next N days."""
    svc = ContentCalendarService(db)
    entries = await svc.upcoming_entries(business_id, within_days)
    return [
        ContentCalendarEntryOut(
            id=e.id,
            title=e.title,
            content_type=e.content_type,
            target_keyword=e.target_keyword,
            priority=e.priority,
            planned_date=e.planned_date.isoformat(),
            status=e.status,
            seo_target_score=e.seo_target_score,
        )
        for e in entries
    ]


@router.patch("/calendar/{entry_id}", response_model=ContentCalendarEntryOut)
async def update_calendar_entry(
    business_id: UUID,
    entry_id: UUID,
    status: str = Query(..., pattern="^(planned|in_progress|published|skipped)$"),
    content_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a calendar entry's status, optionally linking generated content."""
    svc = ContentCalendarService(db)
    entry = await svc.update_entry_status(entry_id, status, content_id)
    return ContentCalendarEntryOut(
        id=entry.id,
        title=entry.title,
        content_type=entry.content_type,
        target_keyword=entry.target_keyword,
        priority=entry.priority,
        planned_date=entry.planned_date.isoformat(),
        status=entry.status,
        seo_target_score=entry.seo_target_score,
    )


# Entity & Knowledge Graph
@router.post("/entities", response_model=EntitySignalOut)
async def create_entity_signal(
    business_id: UUID,
    body: CreateEntityRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create + generate schema.org markup for an entity."""
    svc = EntityOptimizationService(db)
    entity = await svc.create_entity(
        business_id,
        body.entity_type,
        body.entity_name,
        body.external_links,
        body.co_mention_targets,
    )
    return EntitySignalOut(
        id=entity.id,
        entity_type=entity.entity_type,
        entity_name=entity.entity_name,
        schema_json=entity.schema_json,
        external_links=entity.external_links,
        co_mention_targets=entity.co_mention_targets,
        status=entity.status,
    )


@router.get("/entities", response_model=list[EntitySignalOut])
@cached(ttl_seconds=3600, key_prefix="entity_signals")
async def list_entity_signals(
    business_id: UUID,
    entity_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List entity signals (cached 1h)."""
    svc = EntityOptimizationService(db)
    entities = await svc.list_entities(business_id, entity_type)
    return [
        EntitySignalOut(
            id=e.id,
            entity_type=e.entity_type,
            entity_name=e.entity_name,
            schema_json=e.schema_json,
            external_links=e.external_links,
            co_mention_targets=e.co_mention_targets,
            status=e.status,
        )
        for e in entities
    ]


@router.patch("/entities/{entity_id}", response_model=EntitySignalOut)
async def update_entity_signal(
    business_id: UUID,
    entity_id: UUID,
    external_links: list[str] | None = None,
    co_mention_targets: list[str] | None = None,
    status: str | None = Query(None, pattern="^(draft|published)$"),
    published_url: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update entity links/targets/status; regenerates schema if links change."""
    svc = EntityOptimizationService(db)
    entity = await svc.update_entity(entity_id, external_links, co_mention_targets, status, published_url)
    return EntitySignalOut(
        id=entity.id,
        entity_type=entity.entity_type,
        entity_name=entity.entity_name,
        schema_json=entity.schema_json,
        external_links=entity.external_links,
        co_mention_targets=entity.co_mention_targets,
        status=entity.status,
    )


# Multi-Location SEO
@router.post("/locations", response_model=LocationSEOProfileOut)
async def create_location_profile(
    business_id: UUID,
    body: CreateLocationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a location profile with LocalBusiness schema + location keywords."""
    svc = MultiLocationSEOService(db)
    profile = await svc.create_location_profile(
        business_id,
        body.location_name,
        body.address,
        body.city,
        body.service_type,
        body.state,
        body.zip_code,
        body.country,
        body.service_area_radius_km,
    )
    return LocationSEOProfileOut(
        id=profile.id,
        location_name=profile.location_name,
        city=profile.city,
        local_schema_json=profile.local_schema_json,
        location_keywords=profile.location_keywords,
        citation_status=profile.citation_status,
        nap_consistent=profile.nap_consistent,
    )


@router.get("/locations", response_model=list[LocationSEOProfileOut])
@cached(ttl_seconds=3600, key_prefix="seo_locations")
async def list_location_profiles(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List location profiles (cached 1h)."""
    svc = MultiLocationSEOService(db)
    profiles = await svc.list_locations(business_id)
    return [
        LocationSEOProfileOut(
            id=p.id,
            location_name=p.location_name,
            city=p.city,
            local_schema_json=p.local_schema_json,
            location_keywords=p.location_keywords,
            citation_status=p.citation_status,
            nap_consistent=p.nap_consistent,
        )
        for p in profiles
    ]


@router.patch("/locations/{profile_id}/citations", response_model=LocationSEOProfileOut)
async def update_location_citation(
    business_id: UUID,
    profile_id: UUID,
    platform: str = Query(..., pattern="^(google_business|yelp|facebook|bing_places|apple_maps)$"),
    confirmed: bool = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark a directory citation confirmed/unconfirmed; recomputes NAP consistency."""
    svc = MultiLocationSEOService(db)
    profile = await svc.update_citation_status(profile_id, platform, confirmed)
    return LocationSEOProfileOut(
        id=profile.id,
        location_name=profile.location_name,
        city=profile.city,
        local_schema_json=profile.local_schema_json,
        location_keywords=profile.location_keywords,
        citation_status=profile.citation_status,
        nap_consistent=profile.nap_consistent,
    )


@router.get("/locations/citation-report", response_model=CitationConsistencyReportOut)
@cached(ttl_seconds=3600, key_prefix="citation_report")
async def get_citation_consistency_report(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """NAP citation coverage rollup across all locations (cached 1h)."""
    svc = MultiLocationSEOService(db)
    report = await svc.citation_consistency_report(business_id)
    return CitationConsistencyReportOut(**report)


# Link Building Orchestrator (Topical Clusters)
@router.post("/clusters", response_model=TopicalClusterOut)
async def create_topical_cluster(
    business_id: UUID,
    body: CreateClusterRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a pillar + cluster topic group with a generated internal-linking map."""
    svc = TopicalClusterService(db)
    cluster = await svc.create_cluster(
        business_id,
        body.pillar_topic,
        body.cluster_topics,
        body.pillar_content_id,
    )
    return TopicalClusterOut(
        id=cluster.id,
        pillar_topic=cluster.pillar_topic,
        cluster_topics=cluster.cluster_topics,
        internal_linking_map=cluster.internal_linking_map,
        authority_score=cluster.authority_score,
    )


@router.get("/clusters", response_model=list[TopicalClusterOut])
@cached(ttl_seconds=3600, key_prefix="topical_clusters")
async def list_topical_clusters(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List topical clusters ranked by authority score (cached 1h)."""
    svc = TopicalClusterService(db)
    clusters = await svc.list_clusters(business_id)
    return [
        TopicalClusterOut(
            id=c.id,
            pillar_topic=c.pillar_topic,
            cluster_topics=c.cluster_topics,
            internal_linking_map=c.internal_linking_map,
            authority_score=c.authority_score,
        )
        for c in clusters
    ]


@router.patch("/clusters/{cluster_id}/topics", response_model=TopicalClusterOut)
async def add_cluster_topic(
    business_id: UUID,
    cluster_id: UUID,
    topic: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Add a subtopic to an existing cluster; regenerates the linking map + authority score."""
    svc = TopicalClusterService(db)
    cluster = await svc.add_cluster_topic(cluster_id, topic)
    return TopicalClusterOut(
        id=cluster.id,
        pillar_topic=cluster.pillar_topic,
        cluster_topics=cluster.cluster_topics,
        internal_linking_map=cluster.internal_linking_map,
        authority_score=cluster.authority_score,
    )


@router.get("/clusters/{cluster_id}/linking-map")
async def get_cluster_linking_map(
    business_id: UUID,
    cluster_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the internal-linking map for a cluster."""
    svc = TopicalClusterService(db)
    linking_map = await svc.get_linking_map(cluster_id)
    if linking_map is None:
        return {"error": "Cluster not found"}
    return linking_map


# Cross-Domain Audit Orchestrator
@router.get("/audit")
@cached(ttl_seconds=1800, key_prefix="seo_audit")
async def run_seo_audit(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Run a full cross-domain SEO audit (seo_intelligence + fomo_seo +
    seo_optimization + every seo_agents service) and return a prioritized
    action plan. Read-only — cached 30min since it fans out across ~10 queries."""
    orchestrator = SEOAuditOrchestrator(db)
    return await orchestrator.run_audit(business_id)
