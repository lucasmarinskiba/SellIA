"""SEO Intelligence domain models."""

import uuid
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Integer, Numeric, String, Text, ForeignKey, func, Float
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Keyword(Base):
    """Keyword research and tracking."""
    __tablename__ = "seo_keywords"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    keyword: Mapped[str] = mapped_column(String(255))
    search_volume: Mapped[int] = mapped_column(default=0)
    difficulty: Mapped[int] = mapped_column(default=0)  # 0-100
    cpc: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    competition: Mapped[str] = mapped_column(String(20), default="medium")  # low, medium, high
    intent: Mapped[str] = mapped_column(String(50), default="commercial")  # commercial, informational, navigational
    trend: Mapped[str] = mapped_column(String(20), default="stable")  # rising, stable, declining
    current_rank: Mapped[int | None] = mapped_column(nullable=True)
    platform: Mapped[str] = mapped_column(String(50))  # google, amazon, ebay, etc.
    tracked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Ranking(Base):
    """Keyword ranking tracking over time."""
    __tablename__ = "seo_rankings"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    keyword_id: Mapped[UUID] = mapped_column(ForeignKey("seo_keywords.id", ondelete="CASCADE"))
    rank_position: Mapped[int] = mapped_column()
    impressions: Mapped[int] = mapped_column(default=0)
    clicks: Mapped[int] = mapped_column(default=0)
    ctr: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)  # Click-through rate %
    tracked_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PageOptimization(Base):
    """Page-level SEO optimization tracking."""
    __tablename__ = "seo_page_optimization"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    page_url: Mapped[str] = mapped_column(String(500))
    page_title: Mapped[str] = mapped_column(String(255))
    page_type: Mapped[str] = mapped_column(String(50))  # product, category, blog, homepage
    meta_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    h1_tags: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    keywords_targeted: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    backlinks_count: Mapped[int] = mapped_column(default=0)
    internal_links_count: Mapped[int] = mapped_column(default=0)
    page_speed_ms: Mapped[int] = mapped_column(default=0)
    mobile_score: Mapped[int] = mapped_column(default=0)
    core_web_vitals: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    optimization_score: Mapped[int] = mapped_column(default=0)  # 0-100
    organic_traffic_30d: Mapped[int] = mapped_column(default=0)
    organic_revenue_30d: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    indexed: Mapped[bool] = mapped_column(default=False)
    canonical_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CompetitorAnalysis(Base):
    """Competitor SEO analysis."""
    __tablename__ = "seo_competitor_analysis"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    competitor_name: Mapped[str] = mapped_column(String(255))
    competitor_url: Mapped[str] = mapped_column(String(500))
    domain_authority: Mapped[int] = mapped_column(default=0)  # 0-100
    backlinks_count: Mapped[int] = mapped_column(default=0)
    referring_domains: Mapped[int] = mapped_column(default=0)
    organic_keywords: Mapped[int] = mapped_column(default=0)
    top_keywords: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    estimated_monthly_traffic: Mapped[int] = mapped_column(default=0)
    estimated_monthly_revenue: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class SEORecommendation(Base):
    """SEO optimization recommendations."""
    __tablename__ = "seo_recommendations"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    page_optimization_id: Mapped[UUID] = mapped_column(ForeignKey("seo_page_optimization.id", ondelete="CASCADE"))
    recommendation_type: Mapped[str] = mapped_column(String(50))  # title, meta, keywords, content, technical, backlinks
    priority: Mapped[str] = mapped_column(String(20))  # critical, high, medium, low
    description: Mapped[str] = mapped_column(Text)
    current_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommended_value: Mapped[str | None] = mapped_column(Text, nullable=True)
    potential_impact: Mapped[str] = mapped_column(String(20))  # high, medium, low
    status: Mapped[str] = mapped_column(String(20), default="open")  # open, in_progress, completed, rejected
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


SEO_TABLES = [
    Keyword.__table__,
    Ranking.__table__,
    PageOptimization.__table__,
    CompetitorAnalysis.__table__,
    SEORecommendation.__table__,
]
