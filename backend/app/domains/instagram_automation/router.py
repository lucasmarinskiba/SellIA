"""Instagram automation API: @sell_.ia + FeedIA synergy."""
from fastapi import APIRouter, Depends, Body
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.domains.instagram_automation.service import InstagramAutomationAgent


router = APIRouter(prefix="/api/v1/instagram-automation", tags=["instagram-automation"])


@router.post("/create-feedia-post")
async def create_feedia_powered_post(
    campaign_id: str = Body(...),
    content_type: str = Body(...),  # reel, carousel, story, static
    theme: str = Body(...),  # founder_story, feature_highlight, social_proof, case_study
    target_personality: str = Body(...),  # pragmatist, impulse_buyer, skeptic, analyst
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate Instagram content powered by FeedIA + SellIA."""
    post = await InstagramAutomationAgent.create_feedia_powered_post(
        db, campaign_id, content_type, theme, target_personality
    )
    return {
        "post_id": post.id,
        "caption": post.caption,
        "content_type": post.content_type,
        "hashtags": post.hashtags,
        "cta_link": post.cta_link,
        "utm_params": post.utm_params,
    }


@router.post("/schedule-campaign")
async def schedule_instagram_campaign(
    campaign_name: str = Body(...),
    num_days: int = Body(...),
    target_audience: str = Body(...),
    theme: str = Body(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Schedule multi-post Instagram campaign."""
    campaign = await InstagramAutomationAgent.schedule_campaign(
        db, campaign_name, num_days, target_audience, theme
    )
    return {
        "campaign_id": campaign.id,
        "name": campaign.name,
        "status": campaign.status,
        "num_posts": campaign.num_posts_planned,
        "frequency": campaign.post_frequency,
        "content_mix": campaign.content_mix,
        "launched_at": campaign.launched_at.isoformat() if campaign.launched_at else None,
    }


@router.post("/track-conversion")
async def track_instagram_conversion(
    user_id: str = Body(...),
    instagram_post_id: str = Body(...),
    campaign_id: str = Body(...),
    interaction_type: str = Body(...),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Track Instagram interaction → SellIA funnel conversion."""
    path = await InstagramAutomationAgent.track_conversion_path(
        db, user_id, instagram_post_id, campaign_id, interaction_type
    )
    return {
        "path_id": path.id,
        "user_id": path.user_id,
        "instagram_post_id": path.instagram_post_id,
        "interaction_at": path.instagram_interaction_at.isoformat(),
        "utm_params": f"utm_source=instagram&utm_medium={interaction_type}",
    }


@router.post("/calculate-roi")
async def calculate_campaign_roi(
    campaign_id: str = Body(...),
    impressions: int = Body(...),
    clicks: int = Body(...),
    conversions: int = Body(...),
    avg_deal_value: float = Body(2999),
) -> dict:
    """Calculate Instagram campaign ROI."""
    # Mock campaign object
    class MockCampaign:
        id = campaign_id

    roi_data = InstagramAutomationAgent.calculate_instagram_roi(
        MockCampaign(), impressions, clicks, conversions, avg_deal_value
    )
    return roi_data


@router.get("/audience-segments/{campaign_id}")
async def get_audience_segments(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get audience segments for campaign targeting."""
    return await InstagramAutomationAgent.get_audience_segments(db, campaign_id)
