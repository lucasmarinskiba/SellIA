"""Phase X8: Auto-Marketing & Growth Agent API."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.domains.auto_marketing.service import AutoMarketingAgent
from app.domains.auto_marketing.models import MarketingChannel


router = APIRouter(prefix="/api/v1/auto-marketing", tags=["auto-marketing"])


@router.get("/content-calendar")
async def get_content_calendar(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate optimized 30-day content calendar across channels."""
    calendar = await AutoMarketingAgent.generate_content_calendar(db, days)
    return {
        "calendar_length_days": days,
        "total_posts": len(calendar),
        "by_channel": {
            ch: len([c for c in calendar if c["channel"] == ch])
            for ch in [MarketingChannel.INSTAGRAM, MarketingChannel.LINKEDIN, MarketingChannel.TIKTOK]
        },
        "calendar": calendar[:10],  # First 10 days
    }


@router.post("/create-results-post")
async def create_results_post(
    result_metric: str,
    time_frame: str,
    customer_type: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create high-impact results post for maximum engagement."""
    content = await AutoMarketingAgent.create_results_post(
        db, result_metric, time_frame, customer_type
    )
    return {
        "content_id": content.id,
        "title": content.title,
        "hook": content.hook,
        "channels": [content.primary_channel] + content.secondary_channels,
        "cta": content.cta,
    }


@router.get("/viral-formula")
async def get_viral_formula() -> dict:
    """Get proven formula for viral content (hooks + psychology + distribution)."""
    formula = AutoMarketingAgent.get_viral_content_formula()
    return formula


@router.post("/launch-growth-hack")
async def launch_experiment(
    hypothesis: str,
    tactic: str,
    channel: MarketingChannel,
    variant_a: str,
    variant_b: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Launch A/B test to find optimal messaging."""
    experiment = await AutoMarketingAgent.launch_growth_hack(
        db, hypothesis, tactic, channel, variant_a, variant_b
    )
    return {
        "experiment_id": experiment.id,
        "status": experiment.status,
        "channel": experiment.channel,
        "hypothesis": experiment.hypothesis,
        "message": f"A/B test live on {channel}. Check results in 7 days.",
    }


@router.get("/micro-influencers")
async def find_influencers(
    niche: str = "SaaS",
    min_followers: int = 10000,
    max_followers: int = 100000,
) -> dict:
    """Find micro-influencers for partnerships (high engagement, authentic audiences)."""
    influencers = await AutoMarketingAgent.identify_micro_influencers(
        None, niche, min_followers, max_followers
    )
    return {
        "niche": niche,
        "influencers_found": len(influencers),
        "influencers": influencers,
        "next_step": "Reach out with partnership proposal",
    }


@router.get("/channel-performance/{channel}")
async def get_performance(
    channel: MarketingChannel,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Measure channel ROI and growth metrics."""
    metrics = await AutoMarketingAgent.measure_channel_performance(db, channel)
    return metrics
