"""
FOMO Engine Router
"""

from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.fomo import service as fomo_service

router = APIRouter(prefix="/fomo", tags=["fomo"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/campaigns")
async def get_campaigns(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    page: Optional[str] = Query(None),
):
    campaigns = await fomo_service.get_active_campaigns(db, page_path=page)
    return [
        {
            "id": c.id,
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
