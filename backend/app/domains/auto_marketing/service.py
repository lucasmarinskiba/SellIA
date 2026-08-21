"""Phase X8: Auto-Marketing & Growth Agent Service."""
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.domains.auto_marketing.models import (
    AutoMarketingContent, CustomerSuccessStory, GrowthHackingExperiment,
    InfluencerCollaboration, GrowthMetrics, MarketingChannel, ContentType, ContentPillar
)


class AutoMarketingAgent:
    """AI Agent that auto-promotes SellIA for growth."""

    @staticmethod
    async def generate_content_calendar(
        db: AsyncSession,
        days_ahead: int = 30,
    ) -> List[Dict]:
        """Generate 30-day content calendar across channels."""

        content_calendar = []

        # Content distribution: Pillar mix
        pillar_sequence = [
            ContentPillar.RESULTS,  # Day 1: "150% sales increase"
            ContentPillar.TRANSFORMATION,  # Day 2: Before/after
            ContentPillar.EDUCATION,  # Day 3: How-to tip
            ContentPillar.SOCIAL_PROOF,  # Day 4: Testimonial
            ContentPillar.PRODUCT_FEATURES,  # Day 5: Feature highlight
            ContentPillar.PROBLEM_SOLVING,  # Day 6: Pain point solution
            ContentPillar.CULTURE,  # Day 7: Behind-the-scenes
            ContentPillar.URGENCY,  # Day 8: Limited offer
        ]

        channels_schedule = {
            MarketingChannel.INSTAGRAM: [0, 1, 3, 5],  # Mon, Tue, Thu, Sat (morning + evening)
            MarketingChannel.LINKEDIN: [1, 4],  # Tue, Fri (morning)
            MarketingChannel.TIKTOK: [2, 4, 6],  # Wed, Fri, Sun
            MarketingChannel.EMAIL: [3],  # Thu
        }

        for day in range(days_ahead):
            day_date = datetime.now(timezone.utc) + timedelta(days=day)
            pillar = pillar_sequence[day % len(pillar_sequence)]

            for channel, schedule_days in channels_schedule.items():
                if day % 7 in schedule_days:
                    content_calendar.append({
                        "date": day_date.strftime("%Y-%m-%d"),
                        "channel": channel,
                        "pillar": pillar,
                        "content_type": AutoMarketingAgent._select_content_type(channel, pillar),
                    })

        return content_calendar

    @staticmethod
    def _select_content_type(channel: MarketingChannel, pillar: ContentPillar) -> ContentType:
        """Select best content type for channel/pillar combo."""
        if channel == MarketingChannel.INSTAGRAM:
            if pillar == ContentPillar.RESULTS:
                return ContentType.CAROUSEL
            elif pillar == ContentPillar.TRANSFORMATION:
                return ContentType.REEL
            else:
                return ContentType.REEL

        elif channel == MarketingChannel.TIKTOK:
            return ContentType.REEL

        elif channel == MarketingChannel.LINKEDIN:
            if pillar == ContentPillar.EDUCATION:
                return ContentType.ARTICLE
            else:
                return ContentType.POST

        return ContentType.POST

    @staticmethod
    async def create_results_post(
        db: AsyncSession,
        result_metric: str,  # "150% sales increase"
        time_frame: str,  # "3 months"
        customer_type: str,  # "SaaS startups"
        hook: Optional[str] = None,
    ) -> AutoMarketingContent:
        """Create high-impact results post (proven engagement driver)."""

        hook = hook or f"🚀 {result_metric} in {time_frame}"

        content = AutoMarketingContent(
            title=f"{result_metric} - {customer_type}",
            content=f"""
            {result_metric} achieved by {customer_type} using SellIA in just {time_frame}.

            How? By leveraging:
            ✅ AI-powered perception engineering
            ✅ FOMO psychology tactics
            ✅ Personalized customer journeys
            ✅ Real-time conversion optimization

            Your business could be next. Ready to 10x your sales?
            """,
            content_type=ContentType.CAROUSEL,
            pillar=ContentPillar.RESULTS,
            primary_channel=MarketingChannel.INSTAGRAM,
            secondary_channels=[MarketingChannel.LINKEDIN, MarketingChannel.EMAIL],
            hook=hook,
            cta="Link in bio → Start free trial",
            hashtags=["#SellIA", "#SalesAI", "#Growth", "#Automation"],
            emotion_triggered="aspiration",
            cognitive_bias="anchoring",
        )
        db.add(content)
        await db.commit()
        return content

    @staticmethod
    async def create_testimonial_content(
        db: AsyncSession,
        story: CustomerSuccessStory,
    ) -> List[AutoMarketingContent]:
        """Convert customer success story into multi-channel content."""

        contents = []

        # Instagram version (short + visual)
        instagram_content = AutoMarketingContent(
            title=f"{story.customer_name} - {story.result_summary}",
            content=story.short_story or f"Client increased sales by {story.result_metrics.get('sales_increase', 'X%')}",
            content_type=ContentType.REEL,
            pillar=ContentPillar.SOCIAL_PROOF,
            primary_channel=MarketingChannel.INSTAGRAM,
            hook=f"💬 Hear from {story.customer_name}",
            cta="Learn how →",
            hashtags=["#ClientWin", "#SellIA", "#CaseStudy"],
            emotion_triggered="trust",
            cognitive_bias="social_proof",
        )
        contents.append(instagram_content)

        # LinkedIn version (professional)
        linkedin_content = AutoMarketingContent(
            title=f"How {story.company_name} Achieved {story.result_summary}",
            content=story.medium_story or f"""
            {story.problem_statement}

            Solution: {story.solution_applied}

            Results: {story.result_summary}

            Read the full case study in comments ↓
            """,
            content_type=ContentType.ARTICLE,
            pillar=ContentPillar.SOCIAL_PROOF,
            primary_channel=MarketingChannel.LINKEDIN,
            hook=f"📊 {story.company_name} case study",
            cta="Read the full story",
            hashtags=["#CaseStudy", "#Growth", "#AI"],
            emotion_triggered="aspiration",
        )
        contents.append(linkedin_content)

        for content in contents:
            db.add(content)
        await db.commit()

        return contents

    @staticmethod
    async def launch_growth_hack(
        db: AsyncSession,
        hypothesis: str,
        tactic: str,
        channel: MarketingChannel,
        variant_a_content: str,
        variant_b_content: str,
    ) -> GrowthHackingExperiment:
        """Launch A/B test to find what works."""

        experiment = GrowthHackingExperiment(
            hypothesis=hypothesis,
            tactic=tactic,
            channel=channel,
            variant_a=variant_a_content,
            variant_b=variant_b_content,
            start_date=datetime.now(timezone.utc),
            status="running",
        )
        db.add(experiment)
        await db.commit()
        await db.refresh(experiment)
        return experiment

    @staticmethod
    async def identify_micro_influencers(
        db: AsyncSession,
        niche: str = "SaaS",
        min_followers: int = 10000,
        max_followers: int = 100000,
    ) -> List[Dict]:
        """Find micro-influencers for partnerships (high engagement)."""

        # Curated list of micro-influencers by niche
        influencers_by_niche = {
            "SaaS": [
                {"name": "Sarah Chen", "handle": "@sarahcodes", "followers": 45000, "engagement": 0.082},
                {"name": "Alex Rivera", "handle": "@alexrivtech", "followers": 32000, "engagement": 0.095},
            ],
            "Sales": [
                {"name": "Mike Thompson", "handle": "@mikesales", "followers": 55000, "engagement": 0.071},
            ],
            "Marketing": [
                {"name": "Lisa Wang", "handle": "@lisamarkets", "followers": 38000, "engagement": 0.088},
            ],
        }

        matching_influencers = influencers_by_niche.get(niche, [])

        return [
            inf for inf in matching_influencers
            if min_followers <= inf.get("followers", 0) <= max_followers
        ]

    @staticmethod
    async def measure_channel_performance(
        db: AsyncSession,
        channel: MarketingChannel,
        date: Optional[datetime] = None,
    ) -> Dict:
        """Measure daily performance by channel."""

        if not date:
            date = datetime.now(timezone.utc)

        # Fetch metrics
        result = await db.execute(
            select(GrowthMetrics).where(
                GrowthMetrics.channel == channel,
                GrowthMetrics.date >= date.replace(hour=0, minute=0, second=0)
            )
        )
        metrics = result.scalar()

        if not metrics:
            return {"channel": channel, "status": "no_data"}

        return {
            "channel": channel,
            "date": date.strftime("%Y-%m-%d"),
            "impressions": metrics.total_impressions,
            "engagement_rate": f"{metrics.engagement_rate*100:.1f}%",
            "conversions": metrics.total_conversions,
            "conversion_rate": f"{metrics.conversion_rate*100:.2f}%",
            "trend": f"{metrics.trend_vs_yesterday:+.1f}%" if metrics.trend_vs_yesterday else "N/A",
        }

    @staticmethod
    def get_viral_content_formula() -> Dict:
        """Return proven formula for viral content."""

        return {
            "structure": {
                "hook": "First 3 seconds grab attention (shocking stat, question, or bold claim)",
                "story": "2-3 sentence relatable problem",
                "solution": "How SellIA solves it (specific, credible)",
                "proof": "Metric or testimonial (third-party validation)",
                "cta": "Clear action (link, DM, signup)",
            },
            "psychology_layers": {
                "layer_1": "Emotion (aspiration, urgency, belonging)",
                "layer_2": "Logic (metrics, proof points)",
                "layer_3": "Identity (\"be someone who...\")",
            },
            "distribution_rules": {
                "instagram": "Reel > Carousel > Post (video rules)",
                "linkedin": "Professional story > Feature highlight",
                "tiktok": "Relatable humor > Serious education",
                "email": "Personalization > Broadcast",
            },
            "posting_rhythm": {
                "instagram": "2-3x/week (stories daily)",
                "linkedin": "4-5x/week (morning 8-10am)",
                "tiktok": "3-5x/week (timing: 6-9pm)",
                "email": "2x/week (Wed + Fri)",
            }
        }
