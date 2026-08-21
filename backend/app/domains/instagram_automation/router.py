"""Instagram automation API: @sell_.ia + FOMO Intelligence + FeedIA synergy."""
from fastapi import APIRouter, Depends, Body, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.domains.instagram_automation.service import InstagramAutomationAgent
from app.domains.instagram_automation.graph_publisher import InstagramGraphPublisher


router = APIRouter(prefix="/api/v1/instagram-automation", tags=["instagram-automation"])


@router.get("/publisher-status")
async def get_publisher_status() -> dict:
    """Chequea si hay credenciales de Meta Graph API configuradas para publicar en vivo."""
    publisher = InstagramGraphPublisher()
    return {
        "configured": publisher.is_configured(),
        "note": (
            "Publicación en vivo habilitada." if publisher.is_configured() else
            "Faltan INSTAGRAM_BUSINESS_ACCOUNT_ID / INSTAGRAM_ACCESS_TOKEN. "
            "Los posts se registran en la base pero quedan en pending_credentials "
            "hasta configurar el token de @sell_.ia en Meta Business Suite."
        ),
    }


@router.post("/create-feedia-post")
async def create_feedia_powered_post(
    business_id: str = Body(...),
    campaign_id: str = Body(...),
    content_type: str = Body(..., description="reel | carousel | story | static"),
    strategy_type: str = Body(..., description="escasez_real | prueba_social | exclusividad | transparencia"),
    real_data_source: str = Body(..., description="De dónde sale el dato real del post"),
    data_snapshot: dict = Body(..., description="El dato real requerido por la estrategia elegida"),
    media_url: str = Body(...),
    target_personality: str = Body("pragmatist"),
    publish_live: bool = Body(False, description="Si true, publica de verdad en @sell_.ia (requiere credenciales)"),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Registra la estrategia FOMO con dato real y arma/publica el post en @sell_.ia.

    El caption NO se genera con copy inventado: sale de la aplicación registrada
    en fomo_intelligence (rechaza data_snapshot incompleto con 422).
    publish_live=false (default) solo guarda el borrador; true intenta publicar
    de verdad vía Graph API y devuelve el permalink real o el error real.
    """
    try:
        post = await InstagramAutomationAgent.create_feedia_powered_post(
            db, campaign_id, content_type, business_id, strategy_type,
            real_data_source, data_snapshot, media_url, target_personality, publish_live,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    return {
        "post_id": post.id,
        "caption": post.caption,
        "content_type": post.content_type,
        "hashtags": post.hashtags,
        "fomo_application_id": post.fomo_application_id,
        "publish_status": post.publish_status,
        "ig_media_id": post.ig_media_id,
        "ig_permalink": post.ig_permalink,
        "publish_error": post.publish_error,
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
