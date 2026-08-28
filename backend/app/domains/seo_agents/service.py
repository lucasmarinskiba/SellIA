"""SEO Agents services — content generation, keyword gaps, backlinks, reviews,
content calendar, entity signals, multi-location SEO, topical clusters."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
import anthropic

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import timedelta

from app.core.logger import get_logger
from app.domains.seo_agents.models import (
    GeneratedContent,
    CompetitorKeywordGap,
    KeywordOpportunity,
    BacklinkOpportunity,
    ReviewCampaign,
    ReviewAggregate,
    ContentCalendarEntry,
    EntitySignal,
    LocationSEOProfile,
    TopicalCluster,
)

logger = get_logger(__name__)
client = anthropic.Anthropic()


class ContentGenerationService:
    """AI-powered content generation for products/services."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_content(
        self,
        business_id: uuid.UUID,
        content_type: str,  # product_description, landing_page, blog_post, service_page
        target_keyword: str,
        product_name: str,
        product_description: str = "",
        competitor_content: Optional[list[str]] = None,
        tone: str = "professional",
    ) -> GeneratedContent:
        """Generate SEO-optimized content using Claude."""

        # Build prompt for Claude
        prompt = f"""Generate SEO-optimized {content_type} for:
Product/Service: {product_name}
Target Keyword: {target_keyword}
Description: {product_description}

Requirements:
1. Title: 50-60 chars, include target keyword
2. Meta Description: 150-160 chars, compelling CTA
3. H1: Include keyword naturally
4. Body: 2000+ words, 4-5 H2 sections, 1.5% keyword density
5. Include 3-5 internal link opportunities
6. Tone: {tone}
7. Structure: H1 → Intro → H2s with content → FAQ → CTA

Return JSON:
{{
  "title": "...",
  "meta": "...",
  "h1": "...",
  "body": "...",
  "h2_sections": ["section1", "section2", ...],
  "internal_links": [
    {{"anchor": "text", "url": "/path"}}
  ]
}}"""

        # Call Claude API
        message = client.messages.create(
            model="claude-opus-5",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}],
        )

        # Parse response
        try:
            import json
            response_text = message.content[0].text
            # Extract JSON from response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            json_str = response_text[json_start:json_end]
            content_data = json.loads(json_str)
        except (json.JSONDecodeError, IndexError) as e:
            logger.error(f"Failed to parse Claude response: {e}")
            content_data = {
                "title": f"{target_keyword} | {product_name}",
                "meta": f"Discover {product_name}. {product_description}",
                "h1": f"{target_keyword}: Everything You Need to Know",
                "body": product_description or "Content pending...",
                "h2_sections": ["Overview", "Benefits", "How It Works"],
                "internal_links": [],
            }

        # Calculate metrics
        body_word_count = len(content_data.get("body", "").split())
        keyword_count = content_data.get("body", "").lower().count(target_keyword.lower())
        keyword_density = (keyword_count / body_word_count * 100) if body_word_count > 0 else 0

        # SEO score
        seo_score = self._calculate_seo_score(
            content_data.get("title", ""),
            content_data.get("meta", ""),
            target_keyword,
            content_data.get("body", ""),
        )

        # Create record
        content = GeneratedContent(
            business_id=business_id,
            content_type=content_type,
            target_keyword=target_keyword,
            product_name=product_name,
            product_description=product_description,
            title=content_data.get("title", ""),
            meta_description=content_data.get("meta", ""),
            h1=content_data.get("h1", ""),
            body=content_data.get("body", ""),
            h2_sections=content_data.get("h2_sections", []),
            internal_links=content_data.get("internal_links", []),
            seo_score=seo_score,
            keyword_density=keyword_density,
            readability_score=self._calculate_readability(content_data.get("body", "")),
            content_length=body_word_count,
        )
        self.db.add(content)
        await self.db.commit()
        logger.info(f"Generated {content_type} for {product_name} (score: {seo_score})")
        return content

    def _calculate_seo_score(self, title: str, meta: str, keyword: str, body: str) -> int:
        """SEO score: title length + meta length + keyword presence."""
        score = 0

        # Title (50-60 chars optimal)
        title_len = len(title)
        if 50 <= title_len <= 60:
            score += 35
        elif 40 <= title_len <= 70:
            score += 25
        elif title_len >= 40:
            score += 15

        # Meta (150-160 chars optimal)
        meta_len = len(meta)
        if 150 <= meta_len <= 160:
            score += 35
        elif 140 <= meta_len <= 170:
            score += 25
        elif meta_len >= 140:
            score += 15

        # Keyword presence
        keyword_lower = keyword.lower()
        if keyword_lower in title.lower():
            score += 15
        if keyword_lower in meta.lower():
            score += 10
        if body.lower().count(keyword_lower) >= 3:
            score += 10

        return min(100, score)

    def _calculate_readability(self, text: str) -> float:
        """Simple readability score (Flesch-Kincaid approximation)."""
        sentences = len(text.split("."))
        words = len(text.split())
        syllables = sum(len(word) // 3 for word in text.split())  # rough estimate

        if sentences == 0 or words == 0:
            return 50.0

        score = 206.835 - 1.015 * (words / sentences) - 84.6 * (syllables / words)
        return max(0, min(100, score))

    async def list_content(
        self,
        business_id: uuid.UUID,
        status: Optional[str] = None,
    ) -> list[GeneratedContent]:
        """List generated content."""
        query = select(GeneratedContent).where(GeneratedContent.business_id == business_id)
        if status:
            query = query.where(GeneratedContent.status == status)
        query = query.order_by(desc(GeneratedContent.seo_score))
        return (await self.db.execute(query)).scalars().all()


class CompetitorKeywordService:
    """Monitor competitor keyword rankings + identify gaps."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_gap(
        self,
        business_id: uuid.UUID,
        keyword: str,
        search_volume: int,
        difficulty: int,
        business_rank: Optional[int] = None,
        competitor_ranks: Optional[dict] = None,  # {1: 3, 2: 5, 3: 8}
    ) -> CompetitorKeywordGap:
        """Analyze keyword gap vs competitors."""
        competitor_ranks = competitor_ranks or {}

        # Calculate opportunity score
        opportunity_score = self._calculate_opportunity(
            search_volume, difficulty, business_rank, competitor_ranks
        )

        gap = CompetitorKeywordGap(
            business_id=business_id,
            keyword=keyword,
            search_volume=search_volume,
            difficulty=difficulty,
            business_rank=business_rank,
            competitor_1_rank=competitor_ranks.get(1),
            competitor_2_rank=competitor_ranks.get(2),
            competitor_3_rank=competitor_ranks.get(3),
            opportunity_score=opportunity_score,
        )
        self.db.add(gap)
        await self.db.commit()
        logger.info(f"Analyzed gap for '{keyword}' (opportunity: {opportunity_score:.1f})")
        return gap

    def _calculate_opportunity(
        self,
        search_volume: int,
        difficulty: int,
        business_rank: Optional[int],
        competitor_ranks: dict,
    ) -> float:
        """Opportunity = search_volume * (1 - difficulty/100) * rank_gap_factor."""
        base_opportunity = search_volume * (1 - difficulty / 100)

        # Rank gap factor: if competitors rank but business doesn't, 1.5x; otherwise 1.0x
        if business_rank is None and any(competitor_ranks.values()):
            rank_gap_factor = 1.5
        else:
            rank_gap_factor = 1.0

        score = base_opportunity * rank_gap_factor
        return min(100.0, score / 10)  # Normalize to 0-100 (search_volume up to ~1000 maps to full range)

    async def list_gaps(
        self,
        business_id: uuid.UUID,
        min_opportunity: float = 50.0,
    ) -> list[CompetitorKeywordGap]:
        """List keyword gaps ranked by opportunity."""
        query = (
            select(CompetitorKeywordGap)
            .where(
                and_(
                    CompetitorKeywordGap.business_id == business_id,
                    CompetitorKeywordGap.opportunity_score >= min_opportunity,
                )
            )
            .order_by(desc(CompetitorKeywordGap.opportunity_score))
        )
        return (await self.db.execute(query)).scalars().all()

    async def identify_opportunities(
        self,
        business_id: uuid.UUID,
        gaps: list[CompetitorKeywordGap],
    ) -> list[KeywordOpportunity]:
        """Create opportunity records from top gaps."""
        opportunities = []
        for gap in gaps[:10]:  # Top 10 opportunities
            opp = KeywordOpportunity(
                business_id=business_id,
                keyword=gap.keyword,
                search_volume=gap.search_volume,
                difficulty=gap.difficulty,
                opportunity_score=gap.opportunity_score,
                estimated_traffic=int(gap.search_volume * 0.05),  # Rough: ~5% CTR at #3
                content_gap=True,
            )
            self.db.add(opp)
            opportunities.append(opp)
        await self.db.commit()
        logger.info(f"Created {len(opportunities)} keyword opportunities")
        return opportunities


class BacklinkStrategyService:
    """Identify + score backlink outreach opportunities."""

    # Niche-relevance keyword overlap: naive but deterministic scoring hook.
    # Real deployment would call a backlink data API (Ahrefs/Moz/Semrush) for domain_authority.
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_opportunity(
        self,
        business_id: uuid.UUID,
        domain: str,
        opportunity_type: str,  # guest_post, directory, resource_page, broken_link, competitor_backlink
        domain_authority: int,
        niche_keywords: list[str],
        domain_topic_keywords: list[str],
        target_url: Optional[str] = None,
        contact_email: Optional[str] = None,
        contact_name: Optional[str] = None,
    ) -> BacklinkOpportunity:
        """Score + add a backlink opportunity."""
        relevance_score = self._calculate_relevance(niche_keywords, domain_topic_keywords)
        priority_score = self._calculate_priority(domain_authority, relevance_score)

        opportunity = BacklinkOpportunity(
            business_id=business_id,
            domain=domain,
            target_url=target_url,
            contact_email=contact_email,
            contact_name=contact_name,
            opportunity_type=opportunity_type,
            domain_authority=domain_authority,
            relevance_score=relevance_score,
            priority_score=priority_score,
        )
        self.db.add(opportunity)
        await self.db.commit()
        logger.info(f"Backlink opportunity added: {domain} (priority: {priority_score:.1f})")
        return opportunity

    def _calculate_relevance(self, niche_keywords: list[str], domain_topic_keywords: list[str]) -> float:
        """Relevance = overlap ratio between niche and domain topic keywords, 0-100."""
        if not niche_keywords or not domain_topic_keywords:
            return 0.0
        niche_set = {k.lower().strip() for k in niche_keywords}
        domain_set = {k.lower().strip() for k in domain_topic_keywords}
        overlap = len(niche_set & domain_set)
        return min(100.0, (overlap / len(niche_set)) * 100)

    def _calculate_priority(self, domain_authority: int, relevance_score: float) -> float:
        """Priority weights DA 60% + relevance 40% — a highly relevant DA30 site
        can outrank an irrelevant DA70 directory for actual outreach value."""
        return (domain_authority * 0.6) + (relevance_score * 0.4)

    async def update_status(
        self,
        opportunity_id: uuid.UUID,
        status: str,  # identified, contacted, negotiating, acquired, rejected
        acquired_url: Optional[str] = None,
    ) -> BacklinkOpportunity:
        """Update outreach status."""
        opp = (
            await self.db.execute(
                select(BacklinkOpportunity).where(BacklinkOpportunity.id == opportunity_id)
            )
        ).scalar_one_or_none()
        if not opp:
            raise ValueError(f"Backlink opportunity {opportunity_id} not found")

        opp.status = status
        if status == "contacted":
            opp.outreach_sent_at = datetime.now(timezone.utc)
        elif status == "acquired":
            opp.acquired_at = datetime.now(timezone.utc)
            opp.acquired_url = acquired_url
        await self.db.commit()
        logger.info(f"Backlink opportunity {opportunity_id} status -> {status}")
        return opp

    async def list_opportunities(
        self,
        business_id: uuid.UUID,
        status: Optional[str] = None,
        min_priority: float = 0.0,
    ) -> list[BacklinkOpportunity]:
        """List opportunities ranked by priority."""
        query = select(BacklinkOpportunity).where(
            and_(
                BacklinkOpportunity.business_id == business_id,
                BacklinkOpportunity.priority_score >= min_priority,
            )
        )
        if status:
            query = query.where(BacklinkOpportunity.status == status)
        query = query.order_by(desc(BacklinkOpportunity.priority_score))
        return (await self.db.execute(query)).scalars().all()


class ReviewOrchestrationService:
    """Solicit + aggregate customer reviews for social proof + AggregateRating schema."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_campaign(
        self,
        business_id: uuid.UUID,
        customer_name: str,
        customer_email: str,
        service_type: Optional[str] = None,
        review_platform: str = "google",
        review_url: Optional[str] = None,
    ) -> ReviewCampaign:
        """Create + mark-sent a review request campaign.

        Actual email/SMS dispatch is left to the existing sequences/notification
        infrastructure — this records intent + tracks the funnel from request to review.
        """
        campaign = ReviewCampaign(
            business_id=business_id,
            customer_name=customer_name,
            customer_email=customer_email,
            service_type=service_type,
            review_platform=review_platform,
            review_url=review_url,
            status="sent",
            sent_at=datetime.now(timezone.utc),
        )
        self.db.add(campaign)
        await self.db.commit()
        logger.info(f"Review campaign created for {customer_name} ({review_platform})")
        return campaign

    async def record_review(
        self,
        campaign_id: uuid.UUID,
        rating: int,
        review_text: Optional[str] = None,
    ) -> ReviewCampaign:
        """Record a completed review + refresh the business aggregate."""
        if not 1 <= rating <= 5:
            raise ValueError("rating must be between 1 and 5")

        campaign = (
            await self.db.execute(
                select(ReviewCampaign).where(ReviewCampaign.id == campaign_id)
            )
        ).scalar_one_or_none()
        if not campaign:
            raise ValueError(f"Review campaign {campaign_id} not found")

        campaign.status = "completed"
        campaign.rating = rating
        campaign.review_text = review_text
        campaign.completed_at = datetime.now(timezone.utc)
        await self.db.commit()

        await self._refresh_aggregate(campaign.business_id)
        logger.info(f"Review recorded: {rating}/5 for campaign {campaign_id}")
        return campaign

    async def _refresh_aggregate(self, business_id: uuid.UUID) -> ReviewAggregate:
        """Recompute the AggregateRating rollup from completed campaigns."""
        completed = (
            await self.db.execute(
                select(ReviewCampaign).where(
                    and_(
                        ReviewCampaign.business_id == business_id,
                        ReviewCampaign.status == "completed",
                    )
                )
            )
        ).scalars().all()

        star_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for c in completed:
            if c.rating in star_counts:
                star_counts[c.rating] += 1

        total = len(completed)
        avg = (sum(c.rating for c in completed) / total) if total else 0.0

        aggregate = (
            await self.db.execute(
                select(ReviewAggregate).where(ReviewAggregate.business_id == business_id)
            )
        ).scalar_one_or_none()

        if not aggregate:
            aggregate = ReviewAggregate(business_id=business_id)
            self.db.add(aggregate)

        aggregate.total_reviews = total
        aggregate.average_rating = round(avg, 2)
        aggregate.one_star = star_counts[1]
        aggregate.two_star = star_counts[2]
        aggregate.three_star = star_counts[3]
        aggregate.four_star = star_counts[4]
        aggregate.five_star = star_counts[5]
        await self.db.commit()
        return aggregate

    async def get_aggregate(self, business_id: uuid.UUID) -> Optional[ReviewAggregate]:
        """Get the AggregateRating rollup for a business."""
        return (
            await self.db.execute(
                select(ReviewAggregate).where(ReviewAggregate.business_id == business_id)
            )
        ).scalar_one_or_none()

    async def list_campaigns(
        self,
        business_id: uuid.UUID,
        status: Optional[str] = None,
    ) -> list[ReviewCampaign]:
        """List review campaigns."""
        query = select(ReviewCampaign).where(ReviewCampaign.business_id == business_id)
        if status:
            query = query.where(ReviewCampaign.status == status)
        query = query.order_by(desc(ReviewCampaign.created_at))
        return (await self.db.execute(query)).scalars().all()


class ContentCalendarService:
    """Plan a content pipeline ahead of generation — spaces entries across a rolling window."""

    CONTENT_TYPE_ROTATION = ["blog_post", "landing_page", "guide", "video"]

    def __init__(self, db: AsyncSession):
        self.db = db

    def _priority_for_score(self, opportunity_score: float) -> str:
        """Map a 0-100 opportunity score to a scheduling priority band."""
        if opportunity_score >= 70:
            return "high"
        elif opportunity_score >= 40:
            return "medium"
        return "low"

    async def generate_calendar(
        self,
        business_id: uuid.UUID,
        target_keywords: list[str],
        days: int = 90,
        cadence_days: int = 7,
        keyword_opportunities: Optional[dict[str, float]] = None,
        start_date: Optional[datetime] = None,
    ) -> list[ContentCalendarEntry]:
        """Generate a content calendar: one entry per keyword, spaced by cadence_days,
        content_type cycling round-robin, priority driven by keyword opportunity score.
        Stops once the schedule would exceed the `days` window.
        """
        keyword_opportunities = keyword_opportunities or {}
        start = start_date or datetime.now(timezone.utc)
        entries = []

        for i, keyword in enumerate(target_keywords):
            offset_days = i * cadence_days
            if offset_days > days:
                break

            content_type = self.CONTENT_TYPE_ROTATION[i % len(self.CONTENT_TYPE_ROTATION)]
            opportunity_score = keyword_opportunities.get(keyword, 50.0)
            priority = self._priority_for_score(opportunity_score)

            entry = ContentCalendarEntry(
                business_id=business_id,
                title=f"{keyword.title()} — {content_type.replace('_', ' ').title()}",
                content_type=content_type,
                target_keyword=keyword,
                priority=priority,
                planned_date=start + timedelta(days=offset_days),
                seo_target_score=85,
            )
            self.db.add(entry)
            entries.append(entry)

        await self.db.commit()
        logger.info(f"Generated {len(entries)} calendar entries for business {business_id}")
        return entries

    async def update_entry_status(
        self,
        entry_id: uuid.UUID,
        status: str,  # planned, in_progress, published, skipped
        content_id: Optional[uuid.UUID] = None,
    ) -> ContentCalendarEntry:
        """Update a calendar entry's status, optionally linking generated content."""
        entry = (
            await self.db.execute(
                select(ContentCalendarEntry).where(ContentCalendarEntry.id == entry_id)
            )
        ).scalar_one_or_none()
        if not entry:
            raise ValueError(f"Calendar entry {entry_id} not found")

        entry.status = status
        if content_id:
            entry.content_id = content_id
        await self.db.commit()
        logger.info(f"Calendar entry {entry_id} status -> {status}")
        return entry

    async def list_calendar(
        self,
        business_id: uuid.UUID,
        status: Optional[str] = None,
    ) -> list[ContentCalendarEntry]:
        """List calendar entries in publication order."""
        query = select(ContentCalendarEntry).where(ContentCalendarEntry.business_id == business_id)
        if status:
            query = query.where(ContentCalendarEntry.status == status)
        query = query.order_by(ContentCalendarEntry.planned_date)
        return (await self.db.execute(query)).scalars().all()

    async def upcoming_entries(
        self,
        business_id: uuid.UUID,
        within_days: int = 7,
    ) -> list[ContentCalendarEntry]:
        """Entries due within the next `within_days` (still planned/in_progress)."""
        now = datetime.now(timezone.utc)
        cutoff = now + timedelta(days=within_days)
        query = (
            select(ContentCalendarEntry)
            .where(
                and_(
                    ContentCalendarEntry.business_id == business_id,
                    ContentCalendarEntry.status.in_(["planned", "in_progress"]),
                    ContentCalendarEntry.planned_date <= cutoff,
                )
            )
            .order_by(ContentCalendarEntry.planned_date)
        )
        return (await self.db.execute(query)).scalars().all()


class EntityOptimizationService:
    """Build + track schema.org entity markup for brand/product/person knowledge graph signals."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _build_schema(
        self,
        entity_type: str,  # Organization, Person, Product, LocalBusiness
        entity_name: str,
        external_links: Optional[list[str]] = None,
    ) -> dict:
        """Build JSON-LD schema.org markup for the entity."""
        schema = {
            "@context": "https://schema.org",
            "@type": entity_type,
            "name": entity_name,
        }
        if external_links:
            schema["sameAs"] = external_links
        return schema

    async def create_entity(
        self,
        business_id: uuid.UUID,
        entity_type: str,
        entity_name: str,
        external_links: Optional[list[str]] = None,
        co_mention_targets: Optional[list[str]] = None,
    ) -> EntitySignal:
        """Create + score an entity signal with generated schema.org markup."""
        schema_json = self._build_schema(entity_type, entity_name, external_links)

        entity = EntitySignal(
            business_id=business_id,
            entity_type=entity_type,
            entity_name=entity_name,
            schema_json=schema_json,
            external_links=external_links or [],
            co_mention_targets=co_mention_targets or [],
        )
        self.db.add(entity)
        await self.db.commit()
        logger.info(f"Entity signal created: {entity_type} '{entity_name}'")
        return entity

    async def update_entity(
        self,
        entity_id: uuid.UUID,
        external_links: Optional[list[str]] = None,
        co_mention_targets: Optional[list[str]] = None,
        status: Optional[str] = None,
        published_url: Optional[str] = None,
    ) -> EntitySignal:
        """Update entity links/targets/status, regenerating schema if links change."""
        entity = (
            await self.db.execute(
                select(EntitySignal).where(EntitySignal.id == entity_id)
            )
        ).scalar_one_or_none()
        if not entity:
            raise ValueError(f"Entity signal {entity_id} not found")

        if external_links is not None:
            entity.external_links = external_links
            entity.schema_json = self._build_schema(entity.entity_type, entity.entity_name, external_links)
        if co_mention_targets is not None:
            entity.co_mention_targets = co_mention_targets
        if status is not None:
            entity.status = status
        if published_url is not None:
            entity.published_url = published_url

        await self.db.commit()
        logger.info(f"Entity signal {entity_id} updated")
        return entity

    async def list_entities(
        self,
        business_id: uuid.UUID,
        entity_type: Optional[str] = None,
    ) -> list[EntitySignal]:
        """List entity signals for a business."""
        query = select(EntitySignal).where(EntitySignal.business_id == business_id)
        if entity_type:
            query = query.where(EntitySignal.entity_type == entity_type)
        query = query.order_by(desc(EntitySignal.last_updated))
        return (await self.db.execute(query)).scalars().all()


class MultiLocationSEOService:
    """LocalBusiness schema + location-specific keywords + NAP citation tracking
    for businesses with multiple branches or defined service areas."""

    # Directories checked for NAP (Name/Address/Phone) consistency.
    # Real deployment would verify each via its own API/scrape; here the caller
    # reports what it has confirmed and this service tracks the rollup.
    CITATION_PLATFORMS = ["google_business", "yelp", "facebook", "bing_places", "apple_maps"]

    def __init__(self, db: AsyncSession):
        self.db = db

    def _build_local_schema(
        self,
        location_name: str,
        address: str,
        city: str,
        state: Optional[str],
        zip_code: Optional[str],
        country: str,
    ) -> dict:
        """Build LocalBusiness JSON-LD schema.org markup."""
        schema = {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": location_name,
            "address": {
                "@type": "PostalAddress",
                "streetAddress": address,
                "addressLocality": city,
                "addressCountry": country,
            },
        }
        if state:
            schema["address"]["addressRegion"] = state
        if zip_code:
            schema["address"]["postalCode"] = zip_code
        return schema

    def _generate_location_keywords(self, service_type: str, city: str) -> list[str]:
        """Generate location-specific keyword targets."""
        return [
            f"{service_type} in {city}",
            f"{service_type} near me",
            f"best {service_type} {city}",
            f"{city} {service_type}",
        ]

    async def create_location_profile(
        self,
        business_id: uuid.UUID,
        location_name: str,
        address: str,
        city: str,
        service_type: str,
        state: Optional[str] = None,
        zip_code: Optional[str] = None,
        country: str = "US",
        service_area_radius_km: Optional[float] = None,
    ) -> LocationSEOProfile:
        """Create a location profile with generated schema + keyword targets."""
        schema_json = self._build_local_schema(location_name, address, city, state, zip_code, country)
        keywords = self._generate_location_keywords(service_type, city)
        citation_status = {platform: False for platform in self.CITATION_PLATFORMS}

        profile = LocationSEOProfile(
            business_id=business_id,
            location_name=location_name,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            country=country,
            service_area_radius_km=service_area_radius_km,
            local_schema_json=schema_json,
            location_keywords=keywords,
            citation_status=citation_status,
            nap_consistent=False,
        )
        self.db.add(profile)
        await self.db.commit()
        logger.info(f"Location profile created: {location_name} ({city})")
        return profile

    async def update_citation_status(
        self,
        profile_id: uuid.UUID,
        platform: str,
        confirmed: bool,
    ) -> LocationSEOProfile:
        """Mark a directory citation as confirmed/unconfirmed; recomputes NAP consistency."""
        if platform not in self.CITATION_PLATFORMS:
            raise ValueError(f"Unknown citation platform: {platform}")

        profile = (
            await self.db.execute(
                select(LocationSEOProfile).where(LocationSEOProfile.id == profile_id)
            )
        ).scalar_one_or_none()
        if not profile:
            raise ValueError(f"Location profile {profile_id} not found")

        citation_status = dict(profile.citation_status or {})
        citation_status[platform] = confirmed
        profile.citation_status = citation_status
        profile.nap_consistent = all(citation_status.get(p, False) for p in self.CITATION_PLATFORMS)

        await self.db.commit()
        logger.info(f"Citation status updated: {profile_id} {platform}={confirmed}")
        return profile

    async def list_locations(self, business_id: uuid.UUID) -> list[LocationSEOProfile]:
        """List all location profiles for a business."""
        query = select(LocationSEOProfile).where(LocationSEOProfile.business_id == business_id)
        query = query.order_by(LocationSEOProfile.city)
        return (await self.db.execute(query)).scalars().all()

    async def citation_consistency_report(self, business_id: uuid.UUID) -> dict:
        """Aggregate NAP citation coverage across all of a business's locations."""
        locations = await self.list_locations(business_id)
        total = len(locations)
        if total == 0:
            return {"total_locations": 0, "avg_citation_coverage_pct": 0.0, "fully_consistent": 0, "inconsistent_locations": []}

        coverage_sum = 0.0
        inconsistent = []
        for loc in locations:
            statuses = loc.citation_status or {}
            confirmed = sum(1 for v in statuses.values() if v)
            coverage = (confirmed / len(self.CITATION_PLATFORMS)) * 100
            coverage_sum += coverage
            if not loc.nap_consistent:
                inconsistent.append({"location_name": loc.location_name, "city": loc.city, "coverage_pct": round(coverage, 1)})

        fully_consistent = sum(1 for loc in locations if loc.nap_consistent)

        return {
            "total_locations": total,
            "avg_citation_coverage_pct": round(coverage_sum / total, 1),
            "fully_consistent": fully_consistent,
            "inconsistent_locations": inconsistent,
        }


class TopicalClusterService:
    """Groups pillar + cluster content into a topical authority structure that
    drives internal linking strategy."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def _calculate_authority_score(self, cluster_size: int) -> float:
        """Authority score scales with cluster breadth, capped at 100.
        10 points per cluster subtopic — a 10-subtopic cluster maxes the score."""
        return min(100.0, cluster_size * 10.0)

    def _build_linking_map(self, pillar_topic: str, cluster_topics: list[str]) -> dict:
        """Build the internal-linking skeleton: pillar links to every cluster,
        each cluster links back to the pillar (hub-and-spoke)."""
        pillar_slug = pillar_topic.lower().replace(" ", "-")
        return {
            "pillar": pillar_slug,
            "clusters": [
                {
                    "topic": topic,
                    "slug": topic.lower().replace(" ", "-"),
                    "anchor_text": topic,
                    "links_to_pillar": True,
                }
                for topic in cluster_topics
            ],
        }

    async def create_cluster(
        self,
        business_id: uuid.UUID,
        pillar_topic: str,
        cluster_topics: list[str],
        pillar_content_id: Optional[uuid.UUID] = None,
    ) -> TopicalCluster:
        """Create a topical cluster with a generated internal-linking map."""
        linking_map = self._build_linking_map(pillar_topic, cluster_topics)
        authority_score = self._calculate_authority_score(len(cluster_topics))

        cluster = TopicalCluster(
            business_id=business_id,
            pillar_topic=pillar_topic,
            pillar_content_id=pillar_content_id,
            cluster_topics=cluster_topics,
            internal_linking_map=linking_map,
            authority_score=authority_score,
        )
        self.db.add(cluster)
        await self.db.commit()
        logger.info(f"Topical cluster created: '{pillar_topic}' ({len(cluster_topics)} subtopics)")
        return cluster

    async def add_cluster_topic(
        self,
        cluster_id: uuid.UUID,
        topic: str,
    ) -> TopicalCluster:
        """Add a subtopic to an existing cluster; regenerates the linking map + score."""
        cluster = (
            await self.db.execute(
                select(TopicalCluster).where(TopicalCluster.id == cluster_id)
            )
        ).scalar_one_or_none()
        if not cluster:
            raise ValueError(f"Topical cluster {cluster_id} not found")

        topics = list(cluster.cluster_topics or [])
        topics.append(topic)
        cluster.cluster_topics = topics
        cluster.internal_linking_map = self._build_linking_map(cluster.pillar_topic, topics)
        cluster.authority_score = self._calculate_authority_score(len(topics))

        await self.db.commit()
        logger.info(f"Cluster {cluster_id} grew to {len(topics)} subtopics")
        return cluster

    async def get_linking_map(self, cluster_id: uuid.UUID) -> Optional[dict]:
        """Get the internal-linking map for a cluster."""
        cluster = (
            await self.db.execute(
                select(TopicalCluster).where(TopicalCluster.id == cluster_id)
            )
        ).scalar_one_or_none()
        return cluster.internal_linking_map if cluster else None

    async def list_clusters(self, business_id: uuid.UUID) -> list[TopicalCluster]:
        """List topical clusters ranked by authority score."""
        query = (
            select(TopicalCluster)
            .where(TopicalCluster.business_id == business_id)
            .order_by(desc(TopicalCluster.authority_score))
        )
        return (await self.db.execute(query)).scalars().all()
