"""SEO Agents models — content generation + competitor keyword monitoring."""

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text, ForeignKey, func, Boolean, Float, Integer, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GeneratedContent(Base):
    """AI-generated product/service content optimized for SEO."""
    __tablename__ = "seo_generated_content"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))

    # Target
    content_type: Mapped[str] = mapped_column(String(50))  # product_description, landing_page, blog_post, service_page
    target_keyword: Mapped[str] = mapped_column(String(255))
    target_keywords: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # related keywords

    # Input
    product_name: Mapped[str] = mapped_column(String(255))
    product_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    user_input: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Generated
    title: Mapped[str] = mapped_column(String(255))  # 50-60 chars optimal
    meta_description: Mapped[str] = mapped_column(String(160))  # 150-160 chars optimal
    h1: Mapped[str] = mapped_column(String(255))
    body: Mapped[str] = mapped_column(Text)  # 2000+ words
    h2_sections: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # ["How to Use", "Benefits", "FAQ"]
    internal_links: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # [{"anchor": "text", "url": "/path"}]

    # Scoring
    seo_score: Mapped[int] = mapped_column(default=0)  # 0-100
    keyword_density: Mapped[float] = mapped_column(default=0.0)
    readability_score: Mapped[float] = mapped_column(default=0.0)  # 0-100 (Flesch-Kincaid)
    content_length: Mapped[int] = mapped_column(default=0)  # word count

    # Status
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, approved, published
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Performance
    organic_traffic: Mapped[int] = mapped_column(default=0)  # post-publish
    avg_position: Mapped[float] = mapped_column(default=0.0)  # SERP position
    clicks: Mapped[int] = mapped_column(default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CompetitorKeywordGap(Base):
    """Tracks competitor keyword rankings vs business."""
    __tablename__ = "seo_competitor_keyword_gaps"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))

    # Keyword
    keyword: Mapped[str] = mapped_column(String(255))
    search_volume: Mapped[int] = mapped_column(default=0)
    difficulty: Mapped[int] = mapped_column(default=50)  # 0-100

    # Business ranking
    business_rank: Mapped[int | None] = mapped_column(nullable=True)  # 1-100, NULL if not ranked
    business_rank_change: Mapped[int] = mapped_column(default=0)  # weekly change

    # Competitor rankings
    competitor_1_rank: Mapped[int | None] = mapped_column(nullable=True)
    competitor_2_rank: Mapped[int | None] = mapped_column(nullable=True)
    competitor_3_rank: Mapped[int | None] = mapped_column(nullable=True)

    # Gap opportunity score
    opportunity_score: Mapped[float] = mapped_column(default=0.0)  # 0-100: how easily business can rank
    # Formula: search_volume * (1 - difficulty/100) * rank_gap_factor
    # rank_gap_factor = 1.5x if competitor ranks but business doesn't, 1.0x otherwise

    # Status
    tracked: Mapped[bool] = mapped_column(default=True)
    action_taken: Mapped[str | None] = mapped_column(String(50), nullable=True)  # content_created, ranked, abandoned

    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class KeywordOpportunity(Base):
    """High-opportunity keywords (low competition, high volume, undefended by competitors)."""
    __tablename__ = "seo_keyword_opportunities"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))

    keyword: Mapped[str] = mapped_column(String(255))
    search_volume: Mapped[int] = mapped_column(default=0)
    difficulty: Mapped[int] = mapped_column(default=50)  # 0-100

    # Opportunity metrics
    opportunity_score: Mapped[float] = mapped_column(default=0.0)  # 0-100
    estimated_traffic: Mapped[int] = mapped_column(default=0)  # monthly clicks if rank #3
    content_gap: Mapped[bool] = mapped_column(default=True)  # business has no content for this keyword

    # Status
    status: Mapped[str] = mapped_column(String(20), default="identified")  # identified, content_created, ranked
    content_id: Mapped[UUID | None] = mapped_column(ForeignKey("seo_generated_content.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class BacklinkOpportunity(Base):
    """Identified backlink opportunity — outreach targets scored by relevance + authority."""
    __tablename__ = "seo_backlink_opportunities"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))

    # Target
    domain: Mapped[str] = mapped_column(String(255))
    target_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Type
    opportunity_type: Mapped[str] = mapped_column(String(50))  # guest_post, directory, resource_page, broken_link, competitor_backlink

    # Scoring
    domain_authority: Mapped[int] = mapped_column(default=0)  # 0-100 (Moz DA or similar)
    relevance_score: Mapped[float] = mapped_column(default=0.0)  # 0-100: topical relevance to niche
    priority_score: Mapped[float] = mapped_column(default=0.0)  # 0-100: DA * relevance weighted

    # Outreach
    status: Mapped[str] = mapped_column(String(20), default="identified")  # identified, contacted, negotiating, acquired, rejected
    outreach_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    outreach_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acquired_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acquired_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # actual backlink URL once live

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReviewCampaign(Base):
    """Review solicitation campaign — sent to past customers post-purchase."""
    __tablename__ = "seo_review_campaigns"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))

    customer_name: Mapped[str] = mapped_column(String(255))
    customer_email: Mapped[str] = mapped_column(String(255))
    service_type: Mapped[str | None] = mapped_column(String(255), nullable=True)  # product/service purchased

    # Request
    review_platform: Mapped[str] = mapped_column(String(50), default="google")  # google, trustpilot, facebook, internal
    review_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # deep link to leave review
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Result
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, sent, completed, declined
    rating: Mapped[int | None] = mapped_column(nullable=True)  # 1-5
    review_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ReviewAggregate(Base):
    """Aggregated review stats per business — feeds schema.org AggregateRating."""
    __tablename__ = "seo_review_aggregates"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"), unique=True)

    total_reviews: Mapped[int] = mapped_column(default=0)
    average_rating: Mapped[float] = mapped_column(default=0.0)  # 1.0-5.0

    five_star: Mapped[int] = mapped_column(default=0)
    four_star: Mapped[int] = mapped_column(default=0)
    three_star: Mapped[int] = mapped_column(default=0)
    two_star: Mapped[int] = mapped_column(default=0)
    one_star: Mapped[int] = mapped_column(default=0)

    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ContentCalendarEntry(Base):
    """Scheduled content pipeline entry — plans publication ahead of generation."""
    __tablename__ = "seo_content_calendar"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))

    title: Mapped[str] = mapped_column(String(255))
    content_type: Mapped[str] = mapped_column(String(50))  # blog_post, landing_page, guide, video
    target_keyword: Mapped[str] = mapped_column(String(255))
    priority: Mapped[str] = mapped_column(String(20), default="medium")  # high, medium, low

    planned_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    seasonal_context: Mapped[str | None] = mapped_column(String(255), nullable=True)  # "Black Friday", "Back to School"
    seo_target_score: Mapped[int] = mapped_column(default=85)  # target seo_score once published

    status: Mapped[str] = mapped_column(String(20), default="planned")  # planned, in_progress, published, skipped
    content_id: Mapped[UUID | None] = mapped_column(ForeignKey("seo_generated_content.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EntitySignal(Base):
    """Entity + knowledge graph signal — schema.org markup for brand/product/person recognition."""
    __tablename__ = "seo_entity_signals"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))

    entity_type: Mapped[str] = mapped_column(String(50))  # Organization, Person, Product, LocalBusiness
    entity_name: Mapped[str] = mapped_column(String(255))

    schema_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # generated JSON-LD
    external_links: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # sameAs: wikipedia, wikidata, social profiles
    co_mention_targets: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # other entities to co-mention with

    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, published
    published_url: Mapped[str | None] = mapped_column(String(500), nullable=True)  # page carrying this markup

    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LocationSEOProfile(Base):
    """Location/service-area SEO profile — LocalBusiness schema + NAP citation tracking."""
    __tablename__ = "seo_location_profiles"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))

    location_name: Mapped[str] = mapped_column(String(255))
    address: Mapped[str] = mapped_column(String(500))
    city: Mapped[str] = mapped_column(String(255))
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str] = mapped_column(String(100), default="US")
    service_area_radius_km: Mapped[float | None] = mapped_column(nullable=True)  # NULL = single-address only

    local_schema_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # LocalBusiness JSON-LD
    location_keywords: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # ["plumber in Austin", ...]

    # NAP (Name/Address/Phone) citation consistency across directories
    citation_status: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # {"google_business": true, "yelp": false, ...}
    nap_consistent: Mapped[bool] = mapped_column(default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class TopicalCluster(Base):
    """Pillar + cluster content group — drives internal linking strategy + topical authority."""
    __tablename__ = "seo_topical_clusters"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))

    pillar_topic: Mapped[str] = mapped_column(String(255))
    pillar_content_id: Mapped[UUID | None] = mapped_column(ForeignKey("seo_generated_content.id", ondelete="SET NULL"), nullable=True)

    cluster_topics: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # subtopic strings
    internal_linking_map: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # {"pillar": "seo-services", "clusters": [{"topic": "...", "anchor_text": "..."}]}

    authority_score: Mapped[float] = mapped_column(default=0.0)  # 0-100, scales with cluster size

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


SEO_AGENTS_TABLES = [
    GeneratedContent.__table__,
    CompetitorKeywordGap.__table__,
    KeywordOpportunity.__table__,
    BacklinkOpportunity.__table__,
    ReviewCampaign.__table__,
    ReviewAggregate.__table__,
    ContentCalendarEntry.__table__,
    EntitySignal.__table__,
    LocationSEOProfile.__table__,
    TopicalCluster.__table__,
]
