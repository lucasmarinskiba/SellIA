from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.ad_copywriter.service import AdCopywriterService

router = APIRouter(prefix="/ad-copywriter", tags=["ad-copywriter"])


class AdCampaignCreate(BaseModel):
    product_id: UUID
    platform: str = Field(..., description="meta, google o tiktok")
    budget: float = Field(..., gt=0)
    campaign_name: Optional[str] = None


@router.post("/campaigns", status_code=status.HTTP_201_CREATED)
async def create_campaign(
    payload: AdCampaignCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AdCopywriterService(db)
    try:
        campaign = await service.create_ad_campaign(
            business_id=current_user.business_id,
            product_id=payload.product_id,
            platform=payload.platform,
            budget=payload.budget,
            campaign_name=payload.campaign_name,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "id": campaign.id,
        "business_id": campaign.business_id,
        "campaign_name": campaign.campaign_name,
        "platform": campaign.platform,
        "objective": campaign.objective,
        "budget": float(campaign.budget) if campaign.budget else None,
        "status": campaign.status,
        "created_at": campaign.created_at,
    }


@router.get("/campaigns")
async def list_campaigns(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AdCopywriterService(db)
    result = await service.list_campaigns(
        business_id=current_user.business_id,
        limit=limit,
        offset=offset,
    )
    return {
        "total": result["total"],
        "campaigns": [
            {
                "id": c.id,
                "campaign_name": c.campaign_name,
                "platform": c.platform,
                "objective": c.objective,
                "status": c.status,
                "created_at": c.created_at,
            }
            for c in result["campaigns"]
        ],
    }


@router.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AdCopywriterService(db)
    data = await service.get_campaign_with_variants(campaign_id, current_user.business_id)
    if not data:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign = data["campaign"]
    variants = data["variants"]
    return {
        "id": campaign.id,
        "business_id": campaign.business_id,
        "campaign_name": campaign.campaign_name,
        "platform": campaign.platform,
        "objective": campaign.objective,
        "budget": float(campaign.budget) if campaign.budget else None,
        "status": campaign.status,
        "target_audience": campaign.target_audience,
        "created_at": campaign.created_at,
        "variants": [
            {
                "id": v.id,
                "variant_name": v.variant_name,
                "headline": v.headline,
                "body": v.body,
                "cta": v.cta,
                "image_prompt": v.image_prompt,
                "targeting": v.targeting,
                "predicted_ctr": float(v.predicted_ctr) if v.predicted_ctr else None,
            }
            for v in variants
        ],
    }


@router.post("/campaigns/{campaign_id}/export")
async def export_campaign(
    campaign_id: UUID,
    platform: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = AdCopywriterService(db)
    try:
        export = await service.export_campaign(campaign_id, platform, current_user.business_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return export
