"""Instagram automation service: @sell_.ia brand + FOMO Intelligence + FeedIA synergy.

create_feedia_powered_post() ya NO inventa copy ("Only 47 seats left", "Backed by
Y Combinator") — ese texto era FOMO fabricada, exactamente lo que el framework de
fomo_intelligence existe para prohibir. Ahora cada post se arma a partir de una
FOMOStrategyApplication real (escasez_real / prueba_social / exclusividad /
transparencia), registrada con su dato real, y el caption sale de esa
`generated_message` validada — no de un diccionario hardcodeado.
"""
import uuid
from datetime import datetime, timezone, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.instagram_automation.models import (
    InstagramPost, InstagramCampaign, InstagramAudience, InstagramConversionPath
)
from app.domains.instagram_automation.graph_publisher import (
    InstagramGraphPublisher, InstagramNotConfiguredError, InstagramPublishError,
)
from app.domains.fomo_intelligence.service import FOMOIntelligenceService


CTA_BY_PERSONALITY = {
    "pragmatist": "Calculá tu ROI →",
    "impulse_buyer": "Sumate ahora →",
    "skeptic": "Mirá el caso real →",
    "analyst": "Ver el detalle →",
    "social_proof_seeker": "Sumate a la comunidad →",
    "status_conscious": "Pedí tu acceso →",
    "early_adopter": "Entrá primero →",
    "value_maximizer": "Compará el valor →",
}

HASHTAGS = "#sell_.ia #AISales #SalesAutomation #SalesTech #Startup #AI"


class InstagramAutomationAgent:
    """Automates @sell_.ia Instagram promotion, respaldado en FOMO Intelligence real."""

    @staticmethod
    async def create_feedia_powered_post(
        db: AsyncSession,
        campaign_id: str,
        content_type: str,  # reel, carousel, story, static
        business_id: str,
        strategy_type: str,  # escasez_real | prueba_social | exclusividad | transparencia
        real_data_source: str,
        data_snapshot: dict,
        media_url: str,
        target_personality: str = "pragmatist",
        publish_live: bool = False,
    ) -> InstagramPost:
        """Registra una aplicación real de FOMO Intelligence y arma el post a partir de ella.

        Si publish_live=True e INSTAGRAM_BUSINESS_ACCOUNT_ID/INSTAGRAM_ACCESS_TOKEN
        están configurados, publica de verdad en @sell_.ia y guarda media_id/permalink
        reales. Si no, guarda el post en estado pending_credentials — nunca simula
        un post exitoso.
        """
        # 1. Registrar la estrategia FOMO con su dato real (valida + rechaza fake data)
        fomo_application = await FOMOIntelligenceService.register_strategy_application(
            db=db,
            business_id=business_id,
            strategy_type=strategy_type,
            target_type="instagram_post",
            target_id=campaign_id,
            real_data_source=real_data_source,
            data_snapshot=data_snapshot,
            channel="instagram",
            personality_target=target_personality,
        )

        cta = CTA_BY_PERSONALITY.get(target_personality, "Ver más →")
        caption = f"{fomo_application.generated_message}\n\n{cta}\n\n{HASHTAGS}"

        post = InstagramPost(
            id="ig_" + uuid.uuid4().hex[:8],
            caption=caption,
            hashtags=HASHTAGS,
            content_type=content_type,
            media_url=media_url,
            cta_link="https://sellia-brain.vercel.app/instagram-campaign",
            utm_params=f"utm_source=instagram&utm_medium={content_type}&utm_campaign={campaign_id}",
            fomo_application_id=fomo_application.id,
            publish_status="draft",
        )

        if publish_live:
            publisher = InstagramGraphPublisher()
            try:
                if content_type == "reel":
                    result = await publisher.publish_reel(video_url=media_url, caption=caption)
                else:
                    result = await publisher.publish_image(image_url=media_url, caption=caption)
                post.ig_media_id = result["media_id"]
                post.ig_permalink = result["permalink"]
                post.publish_status = "published"
                post.posted_at = datetime.now(timezone.utc)
            except InstagramNotConfiguredError as e:
                post.publish_status = "pending_credentials"
                post.publish_error = str(e)
            except InstagramPublishError as e:
                post.publish_status = "failed"
                post.publish_error = str(e)

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
