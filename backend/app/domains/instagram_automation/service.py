"""Instagram automation service: @sell_.ia brand + FeedIA synergy."""
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.instagram_automation.models import (
    InstagramPost, InstagramCampaign, InstagramAudience, InstagramConversionPath
)


class InstagramAutomationAgent:
    """Automates @sell_.ia Instagram promotion + FeedIA content generation."""

    @staticmethod
    async def create_feedia_powered_post(
        db: AsyncSession,
        campaign_id: str,
        content_type: str,  # reel, carousel, story, static
        theme: str,  # founder_story, feature_highlight, social_proof, case_study
        target_personality: str,  # pragmatist, impulse_buyer, skeptic, analyst
    ) -> InstagramPost:
        """Generate Instagram content via FeedIA AI + SellIA positioning."""

        # FeedIA generates creative content
        content_prompts = {
            "founder_story": {
                "reel": "30sec video: Lucas building SellIA from frustration → solution",
                "carousel": "5-slide story arc: Problem → Discovery → Launch → Growth",
                "story": "Behind-the-scenes: Building AI sales agents",
            },
            "feature_highlight": {
                "reel": "Show X9 personality profiling in action (visual demo)",
                "carousel": "Feature comparison: SellIA vs competitors (5 screens)",
                "story": "Feature tip of the day: @mention for tricks",
            },
            "social_proof": {
                "reel": "Customer testimonial: 'SellIA closed $XXX in 30 days'",
                "carousel": "Case study: Early customer ROI metrics",
                "story": "Milestone: 'Xth customer closed via SellIA'",
            },
            "case_study": {
                "reel": "Before/after: Sales team metrics transformation",
                "carousel": "Deep dive: How [Company] scaled with SellIA",
                "story": "Quick stat: 'Avg deal cycle: 28 → 14 days'",
            }
        }

        prompt = content_prompts.get(theme, {}).get(content_type, "Create viral sales content")

        # Personality-specific messaging
        personality_hooks = {
            "pragmatist": "ROI-first: 'Close 2.3x more deals with AI'",
            "impulse_buyer": "FOMO: 'Only 47 seats left in beta'",
            "skeptic": "Proof: 'Backed by Y Combinator + Stripe'",
            "analyst": "Deep: 'ML algorithms that learn from every deal'",
        }

        hook = personality_hooks.get(target_personality, "AI sales agents that close deals")

        # CTA tailored to personality
        cta_links = {
            "pragmatist": "Calculate your ROI →",
            "impulse_buyer": "Get early access (48h)",
            "skeptic": "See proof: [case study]",
            "analyst": "Deep dive: [whitepaper]",
        }

        cta = cta_links.get(target_personality, "Learn more →")

        hashtags = "#sell_.ia #AISales #SalesAutomation #SalesTech #Startup #AI #FeedIA"

        post = InstagramPost(
            id="ig_" + __import__('uuid').uuid4().hex[:8],
            caption=f"{hook}\n\n{cta}\n\n{hashtags}",
            hashtags=hashtags,
            content_type=content_type,
            media_url="https://cdn.sell-ia.app/instagram/auto-generated.jpg",  # FeedIA generates
            cta_link="https://sellia-brain.vercel.app/instagram-campaign",
            utm_params=f"utm_source=instagram&utm_medium={content_type}&utm_campaign={campaign_id}",
        )
        db.add(post)
        await db.commit()
        await db.refresh(post)
        return post

    @staticmethod
    async def schedule_campaign(
        db: AsyncSession,
        campaign_name: str,
        num_days: int,  # 7, 14, 30
        target_audience: str,
        theme: str,
    ) -> InstagramCampaign:
        """Schedule multi-post Instagram campaign via FeedIA."""

        # Content mix: 40% reels, 30% carousels, 30% stories
        content_mix = {"reels": 0.4, "carousels": 0.3, "stories": 0.3}

        frequency_map = {7: "daily", 14: "3x_weekly", 30: "daily"}

        campaign = InstagramCampaign(
            id="camp_" + __import__('uuid').uuid4().hex[:8],
            name=campaign_name,
            theme=theme,
            target_audience=target_audience,
            num_posts_planned=num_days,
            post_frequency=frequency_map.get(num_days, "daily"),
            content_mix=content_mix,
            feedia_integration=True,
            status="scheduled",
            launched_at=datetime.now(timezone.utc),
        )
        db.add(campaign)
        await db.commit()
        await db.refresh(campaign)
        return campaign

    @staticmethod
    async def track_conversion_path(
        db: AsyncSession,
        user_id: str,
        instagram_post_id: str,
        campaign_id: str,
        interaction_type: str,  # like, comment, share, click, story_swipe
    ) -> InstagramConversionPath:
        """Track user journey: Instagram → SellIA funnel."""

        path = InstagramConversionPath(
            id="igpath_" + __import__('uuid').uuid4().hex[:8],
            user_id=user_id,
            instagram_interaction_at=datetime.now(timezone.utc),
            instagram_post_id=instagram_post_id,
            campaign_id=campaign_id,
            utm_medium=interaction_type,
        )
        db.add(path)
        await db.commit()
        await db.refresh(path)
        return path

    @staticmethod
    def calculate_instagram_roi(
        campaign: InstagramCampaign,
        impressions: int,
        clicks: int,
        conversions: int,
        avg_deal_value: float = 2999,
    ) -> dict:
        """Calculate Instagram campaign ROI."""

        click_through_rate = clicks / max(impressions, 1)
        conversion_rate = conversions / max(clicks, 1)
        revenue = conversions * avg_deal_value

        # Estimated cost: $1 per 1000 impressions (CPM)
        cost = impressions / 1000
        roi = (revenue - cost) / max(cost, 1)

        return {
            "campaign_id": campaign.id,
            "impressions": impressions,
            "clicks": clicks,
            "conversions": conversions,
            "ctr": click_through_rate,
            "conversion_rate": conversion_rate,
            "revenue": revenue,
            "cost": cost,
            "roi": roi,
            "roi_percentage": roi * 100,
        }

    @staticmethod
    async def get_audience_segments(
        db: AsyncSession,
        campaign_id: str,
    ) -> dict:
        """Get audience segments following @sell_.ia for targeting."""

        # Simulated segments
        segments = {
            "high_intent": {
                "description": "Followed SellIA + engaged with 3+ posts",
                "count": 247,
                "avg_engagement": 0.087,
                "estimated_conversion": 0.15,
            },
            "interested_viewers": {
                "description": "Viewed stories, not yet followers",
                "count": 1203,
                "avg_engagement": 0.032,
                "estimated_conversion": 0.04,
            },
            "competitor_followers": {
                "description": "Follow sales tools (HubSpot, Salesforce, Outreach)",
                "count": 5432,
                "avg_engagement": 0.018,
                "estimated_conversion": 0.02,
            },
            "industry_influencers": {
                "description": "B2B sales influencers, 10k+ followers",
                "count": 87,
                "avg_engagement": 0.156,
                "estimated_conversion": 0.22,
            },
        }

        return {
            "campaign_id": campaign_id,
            "total_followers": sum(s["count"] for s in segments.values()),
            "segments": segments,
        }
