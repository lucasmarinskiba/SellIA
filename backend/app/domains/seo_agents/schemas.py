"""SEO Agents schemas — request/response models."""

from uuid import UUID
from pydantic import BaseModel


class GenerateContentRequest(BaseModel):
    """Request to generate SEO content."""

    content_type: str  # product_description, landing_page, blog_post, service_page
    target_keyword: str
    product_name: str
    product_description: str = ""
    tone: str = "professional"


class GeneratedContentOut(BaseModel):
    """Generated content response."""

    id: UUID
    product_name: str
    target_keyword: str
    title: str
    meta_description: str
    h1: str
    seo_score: int
    keyword_density: float
    content_length: int
    status: str


class CompetitorKeywordGapIn(BaseModel):
    """Request to analyze keyword gap."""

    keyword: str
    search_volume: int
    difficulty: int
    business_rank: int | None = None
    competitor_1_rank: int | None = None
    competitor_2_rank: int | None = None
    competitor_3_rank: int | None = None


class CompetitorKeywordGapOut(BaseModel):
    """Keyword gap analysis response."""

    id: UUID
    keyword: str
    search_volume: int
    difficulty: int
    business_rank: int | None
    competitor_1_rank: int | None
    opportunity_score: float
    action_taken: str | None


class KeywordOpportunityOut(BaseModel):
    """High-opportunity keyword."""

    id: UUID
    keyword: str
    search_volume: int
    difficulty: int
    opportunity_score: float
    estimated_traffic: int
    status: str
