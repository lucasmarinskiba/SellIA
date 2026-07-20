"""Ad Orchestrator API Router

Endpoints para lanzar campaigns:
- POST /ads/campaigns — crear + lanzar campaign
- GET /ads/campaigns/{id}/performance — ver metrics
- POST /ads/campaigns/{id}/optimize — optimizar basado en performance
"""

import logging
from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.core.logger import get_logger
from app.domains.users.models import User
from app.domains.computer_use.services.ad_orchestrator import (
    get_ad_orchestrator,
    AdPlatform,
    CopyTone,
)

logger = get_logger(__name__)
router = APIRouter()


# ========== Models ==========


class CreateCampaignRequest(BaseModel):
    """Request para crear campaign."""

    campaign_name: str = Field(..., min_length=1, max_length=100)
    product_name: str
    main_benefit: str
    discount_pct: Optional[int] = None
    customer_count: int = Field(default=1000)
    urgency_days: int = Field(default=7)
    platforms: List[str] = Field(..., description="facebook, instagram, google_search, tiktok")
    daily_budget: float = Field(..., gt=0)
    duration_days: int = Field(default=7, ge=1, le=90)
    target_audience: Optional[Dict[str, Any]] = None


class CampaignResponse(BaseModel):
    """Response con detalles de campaign."""

    campaign_id: str
    name: str
    platform: str
    format: str
    daily_budget: float
    status: str
    created_at: str


class CampaignPerformanceResponse(BaseModel):
    """Metrics de performance."""

    campaign_id: str
    status: str
    impressions: int
    clicks: int
    ctr: float
    conversions: int
    cpc: float
    cpa: float
    spend: float
    revenue: float
    roas: float


# ========== Endpoints ==========


@router.post("/ads/campaigns", response_model=List[CampaignResponse])
async def create_ad_campaign(
    request: CreateCampaignRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Crea + lanza campaign multi-platform con ad copy auto-generated.

    Genera 5 variantes de copy en diferentes tonos.
    Lanza A/B test en plataformas especificadas.
    """
    try:
        orchestrator = get_ad_orchestrator()

        # Parsear platforms
        try:
            platforms = [AdPlatform(p) for p in request.platforms]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Invalid platform: {e}")

        # Crear campaigns
        success, campaign_ids = await orchestrator.create_campaign(
            campaign_name=request.campaign_name,
            product_info={
                "product_name": request.product_name,
                "main_benefit": request.main_benefit,
                "discount_pct": request.discount_pct or 0,
                "customer_count": request.customer_count,
                "urgency_days": request.urgency_days,
            },
            platforms=platforms,
            daily_budget=request.daily_budget,
            duration_days=request.duration_days,
            target_audience=request.target_audience,
        )

        if not success:
            raise HTTPException(status_code=500, detail="Failed to create campaign")

        # Retornar campaigns
        responses = []
        for campaign_id in campaign_ids:
            campaign = orchestrator.campaigns.get(campaign_id)
            if campaign:
                responses.append(
                    CampaignResponse(
                        campaign_id=campaign.campaign_id,
                        name=campaign.name,
                        platform=campaign.platform.value,
                        format=campaign.format.value,
                        daily_budget=campaign.daily_budget,
                        status=campaign.status,
                        created_at=campaign.created_at.isoformat(),
                    )
                )

        return responses

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating campaign: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ads/campaigns/{campaign_id}/performance", response_model=CampaignPerformanceResponse)
async def get_campaign_performance(
    campaign_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Obtiene metrics de performance de campaign."""
    try:
        orchestrator = get_ad_orchestrator()
        perf = await orchestrator.get_campaign_performance(campaign_id)

        if not perf:
            raise HTTPException(status_code=404, detail="Campaign not found")

        return CampaignPerformanceResponse(**perf)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ads/campaigns/optimize")
async def optimize_campaigns(
    campaign_ids: List[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """
    Optimiza campaigns automáticamente.

    Pausa underperformers (ROAS < 2.0).
    Boosted winners.
    """
    try:
        orchestrator = get_ad_orchestrator()

        optimization_count, paused = await orchestrator.optimize_campaigns(
            user_id=str(current_user.id),
            campaigns=campaign_ids,
        )

        return {
            "optimizations_made": optimization_count,
            "paused_campaigns": paused,
            "message": f"Optimized {optimization_count} campaigns. Paused {len(paused)} underperformers.",
        }

    except Exception as e:
        logger.error(f"Error optimizing campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ads/copy-templates")
async def get_copy_templates(
    current_user: User = Depends(get_current_active_user),
):
    """
    Retorna templates de copy disponibles.

    Educación sobre cómo se generan ad copies.
    """
    templates = {
        "tones": [
            {
                "tone": "urgent",
                "description": "Limited time, scarcity, FOMO",
                "best_for": "Hot leads, closing",
                "example_headline": "⏰ Last 5 spots available",
            },
            {
                "tone": "educational",
                "description": "Learn, discover, master",
                "best_for": "Awareness, consideration stage",
                "example_headline": "Learn the $1M sales secret",
            },
            {
                "tone": "lifestyle",
                "description": "Aspirational, dream, transformation",
                "best_for": "Expressive personalities, emotional connection",
                "example_headline": "Imagine your life as a 7-figure entrepreneur",
            },
            {
                "tone": "discount",
                "description": "Price-focused, savings",
                "best_for": "Price-sensitive audiences, budget buyers",
                "example_headline": "20% off + free shipping",
            },
            {
                "tone": "social_proof",
                "description": "Testimonials, reviews, results",
                "best_for": "Trust-building, analytical personalities",
                "example_headline": "5★ rated by 1,000+ customers",
            },
        ],
        "platforms": {
            "facebook": {
                "optimal_format": "single_image",
                "best_headlines": "25-50 chars",
                "best_body": "125 chars max",
                "recommended_ctas": ["Learn More", "Shop Now", "Sign Up"],
            },
            "instagram": {
                "optimal_format": "carousel",
                "best_headlines": "20-30 chars",
                "best_body": "100 chars max",
                "recommended_ctas": ["Tap to Learn More", "Shop Collection", "Follow"],
            },
            "tiktok": {
                "optimal_format": "video",
                "best_headlines": "Hook in 1 second",
                "best_body": "Text overlay, 5-15 seconds",
                "recommended_ctas": ["Link in bio", "Tap for more", "Download"],
            },
            "google_search": {
                "optimal_format": "text_only",
                "best_headlines": "High intent keywords",
                "best_body": "Problem → Solution",
                "recommended_ctas": ["Get Started", "Free Trial", "Shop Now"],
            },
        },
    }

    return templates
