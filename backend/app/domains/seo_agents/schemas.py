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


class GenerateCalendarRequest(BaseModel):
    """Request to generate a content calendar."""

    target_keywords: list[str]
    days: int = 90
    cadence_days: int = 7
    keyword_opportunities: dict[str, float] | None = None  # keyword -> opportunity_score (0-100)


class ContentCalendarEntryOut(BaseModel):
    """Content calendar entry response."""

    id: UUID
    title: str
    content_type: str
    target_keyword: str
    priority: str
    planned_date: str  # ISO datetime
    status: str
    seo_target_score: int


class CreateEntityRequest(BaseModel):
    """Request to create an entity signal."""

    entity_type: str  # Organization, Person, Product, LocalBusiness
    entity_name: str
    external_links: list[str] | None = None
    co_mention_targets: list[str] | None = None


class EntitySignalOut(BaseModel):
    """Entity signal response."""

    id: UUID
    entity_type: str
    entity_name: str
    schema_json: dict | None
    external_links: list | None
    co_mention_targets: list | None
    status: str


class CreateLocationRequest(BaseModel):
    """Request to create a location SEO profile."""

    location_name: str
    address: str
    city: str
    service_type: str
    state: str | None = None
    zip_code: str | None = None
    country: str = "US"
    service_area_radius_km: float | None = None


class LocationSEOProfileOut(BaseModel):
    """Location SEO profile response."""

    id: UUID
    location_name: str
    city: str
    local_schema_json: dict | None
    location_keywords: list | None
    citation_status: dict | None
    nap_consistent: bool


class CitationConsistencyReportOut(BaseModel):
    """NAP citation consistency rollup."""

    total_locations: int
    avg_citation_coverage_pct: float
    fully_consistent: int
    inconsistent_locations: list


class CreateClusterRequest(BaseModel):
    """Request to create a topical cluster."""

    pillar_topic: str
    cluster_topics: list[str]
    pillar_content_id: UUID | None = None


class TopicalClusterOut(BaseModel):
    """Topical cluster response."""

    id: UUID
    pillar_topic: str
    cluster_topics: list | None
    internal_linking_map: dict | None
    authority_score: float
