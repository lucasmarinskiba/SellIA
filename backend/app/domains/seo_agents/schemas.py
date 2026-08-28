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


class BacklinkOpportunityIn(BaseModel):
    """Request to add a backlink opportunity."""

    domain: str
    opportunity_type: str  # guest_post, directory, resource_page, broken_link, competitor_backlink
    domain_authority: int
    niche_keywords: list[str]
    domain_topic_keywords: list[str]
    target_url: str | None = None
    contact_email: str | None = None
    contact_name: str | None = None


class BacklinkOpportunityOut(BaseModel):
    """Backlink opportunity response."""

    id: UUID
    domain: str
    opportunity_type: str
    domain_authority: int
    relevance_score: float
    priority_score: float
    status: str
    contact_email: str | None


class ReviewCampaignIn(BaseModel):
    """Request to create a review campaign."""

    customer_name: str
    customer_email: str
    service_type: str | None = None
    review_platform: str = "google"
    review_url: str | None = None


class ReviewCampaignOut(BaseModel):
    """Review campaign response."""

    id: UUID
    customer_name: str
    service_type: str | None
    review_platform: str
    status: str
    rating: int | None


class ReviewAggregateOut(BaseModel):
    """AggregateRating rollup."""

    total_reviews: int
    average_rating: float
    five_star: int
    four_star: int
    three_star: int
    two_star: int
    one_star: int
