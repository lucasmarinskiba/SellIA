"""SEO Intelligence schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class KeywordCreate(BaseModel):
    """Create keyword for tracking."""
    keyword: str = Field(..., min_length=1, max_length=255)
    search_volume: int = Field(default=0, ge=0)
    difficulty: int = Field(default=0, ge=0, le=100)
    cpc: Decimal = Field(default=0, ge=0)
    competition: str = Field(default="medium", pattern="^(low|medium|high)$")
    intent: str = Field(default="commercial")
    trend: str = Field(default="stable", pattern="^(rising|stable|declining)$")
    platform: str = Field(default="google", max_length=50)


class KeywordOut(BaseModel):
    """Keyword response."""
    id: UUID
    business_id: UUID
    keyword: str
    search_volume: int
    difficulty: int
    cpc: Decimal
    competition: str
    intent: str
    trend: str
    current_rank: int | None
    platform: str
    tracked_at: datetime

    class Config:
        from_attributes = True


class RankingOut(BaseModel):
    """Ranking tracking response."""
    id: UUID
    business_id: UUID
    keyword_id: UUID
    rank_position: int
    impressions: int
    clicks: int
    ctr: Decimal
    tracked_date: datetime

    class Config:
        from_attributes = True


class PageOptimizationCreate(BaseModel):
    """Create page optimization record."""
    page_url: str = Field(..., min_length=1, max_length=500)
    page_title: str = Field(..., min_length=1, max_length=255)
    page_type: str = Field(..., pattern="^(product|category|blog|homepage)$")
    meta_description: str | None = None
    keywords_targeted: list[str] | None = None


class PageOptimizationUpdate(BaseModel):
    """Update page optimization."""
    page_speed_ms: int | None = None
    mobile_score: int | None = Field(None, ge=0, le=100)
    optimization_score: int | None = Field(None, ge=0, le=100)
    organic_traffic_30d: int | None = None
    organic_revenue_30d: Decimal | None = None


class PageOptimizationOut(BaseModel):
    """Page optimization response."""
    id: UUID
    business_id: UUID
    page_url: str
    page_title: str
    page_type: str
    meta_description: str | None
    backlinks_count: int
    internal_links_count: int
    page_speed_ms: int
    mobile_score: int
    optimization_score: int
    organic_traffic_30d: int
    organic_revenue_30d: Decimal
    indexed: bool
    last_updated: datetime

    class Config:
        from_attributes = True


class CompetitorAnalysisCreate(BaseModel):
    """Create competitor analysis."""
    competitor_name: str = Field(..., min_length=1, max_length=255)
    competitor_url: str = Field(..., min_length=1, max_length=500)


class CompetitorAnalysisOut(BaseModel):
    """Competitor analysis response."""
    id: UUID
    business_id: UUID
    competitor_name: str
    competitor_url: str
    domain_authority: int
    backlinks_count: int
    referring_domains: int
    organic_keywords: int
    top_keywords: list | None
    estimated_monthly_traffic: int
    estimated_monthly_revenue: Decimal
    analyzed_at: datetime

    class Config:
        from_attributes = True


class SEORecommendationOut(BaseModel):
    """SEO recommendation response."""
    id: UUID
    business_id: UUID
    page_optimization_id: UUID
    recommendation_type: str
    priority: str
    description: str
    current_value: str | None
    recommended_value: str | None
    potential_impact: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class SEOHealthResponse(BaseModel):
    """SEO health score."""
    overall_score: int
    indexed_pages: int
    ranking_keywords: int
    top_10_keywords: int
    avg_page_speed_ms: int
    avg_mobile_score: int
    organic_traffic_30d: int
    organic_revenue_30d: float
    critical_issues: int
    high_priority_issues: int
