"""
FOMO Engine Router - Star Player
"""

from typing import Annotated, Optional
from uuid import UUID
from decimal import Decimal

from fastapi import APIRouter, Depends, Query, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.fomo.service import fomo_service

router = APIRouter(prefix="/fomo", tags=["fomo"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ========== CAMPAIGNS ==========
@router.post("/campaigns")
async def create_campaign(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    name: str = Body(...),
    campaign_type: str = Body(...),
    headline: str = Body(...),
    config: dict = Body(...),
    trigger_type: Optional[str] = Body(None),
):
    """Create new FOMO campaign (draft status)."""
    campaign = await fomo_service.create_campaign(
        db,
        user_id=current_user.id,
        name=name,
        campaign_type=campaign_type,
        headline=headline,
        config=config,
        trigger_type=trigger_type,
    )
    await db.commit()
    return {
        "id": str(campaign.id),
        "name": campaign.name,
        "status": campaign.status,
        "created_at": campaign.created_at.isoformat(),
    }


@router.get("/campaigns")
async def get_campaigns(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List all campaigns for user."""
    campaigns = await fomo_service.get_campaigns(db, current_user.id)
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "campaign_type": c.campaign_type,
            "status": c.status,
            "headline": c.headline,
            "created_at": c.created_at.isoformat(),
        }
        for c in campaigns
    ]


@router.post("/campaigns/{campaign_id}/activate")
async def activate_campaign(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Activate a campaign (draft → active)."""
    campaign = await fomo_service.get_campaign(db, campaign_id)
    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Campaign not found")

    campaign = await fomo_service.activate_campaign(db, campaign_id)
    await db.commit()
    return {"id": str(campaign.id), "status": campaign.status}


# ========== EVENTS ==========
@router.post("/events/{campaign_id}/log")
async def log_event(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    event_type: str = Body(...),
    customer_id: Optional[UUID] = Body(None),
    product_id: Optional[UUID] = Body(None),
    metadata: Optional[dict] = Body(None),
):
    """Log event (purchase, view, add_to_cart, abandoned)."""
    event = await fomo_service.log_event(
        db,
        campaign_id=campaign_id,
        event_type=event_type,
        customer_id=customer_id,
        product_id=product_id,
        metadata=metadata,
    )

    # Record metric
    if event_type == 'purchase' and metadata:
        revenue = metadata.get('revenue')
        if revenue:
            await fomo_service.record_metric(
                db,
                campaign_id,
                'conversion',
                Decimal(str(revenue)),
            )
    else:
        await fomo_service.record_metric(db, campaign_id, 'impression')

    await db.commit()
    return {"id": str(event.id), "event_type": event.event_type}


@router.get("/events/{campaign_id}/recent")
async def get_recent_events(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
):
    """Get recent events for widget display."""
    events = await fomo_service.get_recent_events(db, campaign_id, limit)
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "metadata": e.metadata,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]


@router.get("/events/{campaign_id}/count")
async def get_event_count(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    event_type: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=168),
):
    """Get count of events in time window."""
    count = await fomo_service.get_event_count(db, campaign_id, event_type, hours)
    return {"count": count}


# ========== A/B TESTING ==========
@router.post("/ab-tests/{campaign_id}/start")
async def create_ab_test(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    variant_a: dict = Body(...),
    variant_b: dict = Body(...),
):
    """Start A/B test for campaign."""
    campaign = await fomo_service.get_campaign(db, campaign_id)
    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Campaign not found")

    test = await fomo_service.create_ab_test(db, campaign_id, variant_a, variant_b)
    await db.commit()
    return {"id": str(test.id), "status": test.status}


@router.post("/ab-tests/{test_id}/view/{variant}")
async def record_ab_view(
    test_id: UUID,
    variant: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Record view for A/B test."""
    if variant not in ['A', 'B']:
        raise HTTPException(status_code=400, detail="Variant must be A or B")

    await fomo_service.record_ab_test_view(db, test_id, variant)
    await db.commit()
    return {"ok": True}


@router.post("/ab-tests/{test_id}/convert/{variant}")
async def record_ab_conversion(
    test_id: UUID,
    variant: str,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Record conversion for A/B test."""
    if variant not in ['A', 'B']:
        raise HTTPException(status_code=400, detail="Variant must be A or B")

    await fomo_service.record_ab_test_conversion(db, test_id, variant)
    await db.commit()
    return {"ok": True}


@router.get("/ab-tests/{test_id}/stats")
async def get_ab_test_stats(
    test_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get A/B test statistics."""
    stats = await fomo_service.get_ab_test_stats(db, test_id)
    return stats


# ========== ANALYTICS & DASHBOARD ==========
@router.get("/analytics/{campaign_id}/metrics")
async def get_campaign_metrics(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: int = Query(30, ge=1, le=365),
):
    """Get metrics for campaign (last N days)."""
    campaign = await fomo_service.get_campaign(db, campaign_id)
    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Campaign not found")

    metrics = await fomo_service.get_metrics(db, campaign_id, days)
    return metrics


@router.get("/analytics/{campaign_id}/summary")
async def get_campaign_summary(
    campaign_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get summary metrics for campaign."""
    campaign = await fomo_service.get_campaign(db, campaign_id)
    if not campaign or campaign.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Campaign not found")

    summary = await fomo_service.get_summary_metrics(db, campaign_id)
    return summary


@router.get("/analytics")
async def get_all_campaigns_with_analytics(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get all campaigns with analytics (dashboard)."""
    campaigns = await fomo_service.get_campaigns(db, current_user.id)
    result = []

    for campaign in campaigns:
        summary = await fomo_service.get_summary_metrics(db, campaign.id)
        result.append({
            "id": str(campaign.id),
            "name": campaign.name,
            "status": campaign.status,
            "campaign_type": campaign.campaign_type,
            "summary": summary,
        })

    return result


# ========== LEGACY ENDPOINTS (compatibility) ==========
@router.get("/campaigns-active")
async def get_active_campaigns(
    db: Annotated[AsyncSession, Depends(get_db)],
    page: Optional[str] = Query(None),
):
    """Get active campaigns for page display."""
    campaigns = await fomo_service.get_active_campaigns(db, page_path=page)
    return [
        {
            "id": str(c.id),
            "campaign_type": c.campaign_type,
            "headline": c.headline,
            "subheadline": c.subheadline,
            "cta_text": c.cta_text,
            "cta_url": c.cta_url,
            "ends_at": c.ends_at,
            "total_spots": c.total_spots,
            "spots_taken": c.spots_taken,
            "accent_color": c.accent_color,
            "emoji": c.emoji,
            "is_dismissible": c.is_dismissible,
        }
        for c in campaigns
    ]


@router.get("/social-proof")
async def get_social_proof(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(10, ge=1, le=50),
):
    """Get recent social proof events."""
    events = await fomo_service.get_recent_social_proof(db, limit)
    return [
        {
            "event_type": e.event_type,
            "user_display_name": e.user_display_name,
            "action_text": e.action_text,
            "item_name": e.item_name,
            "location": e.location,
            "time_ago_text": e.time_ago_text,
        }
        for e in events
    ]
