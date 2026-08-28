"""SEO Agents models — content generation + competitor keyword monitoring."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text, ForeignKey, func, Boolean, Float, Integer, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class GeneratedContent(Base):
    """AI-generated product/service content optimized for SEO."""
    __tablename__ = "seo_generated_content"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
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

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
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

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
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


SEO_AGENTS_TABLES = [
    GeneratedContent.__table__,
    CompetitorKeywordGap.__table__,
    KeywordOpportunity.__table__,
]
