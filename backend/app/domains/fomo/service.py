"""
FOMO Engine Service
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.domains.fomo.models import FOMOCampaign, SocialProofEvent


async def get_active_campaigns(db: AsyncSession, page_path: Optional[str] = None, plan_id: Optional[str] = None) -> List[FOMOCampaign]:
    now = datetime.now(timezone.utc)
    query = select(FOMOCampaign).where(
        FOMOCampaign.is_active == True,
    )
    if page_path:
        query = query.where(FOMOCampaign.show_on_pages.contains([page_path]))
    result = await db.execute(query.order_by(desc(FOMOCampaign.created_at)))
    campaigns = result.scalars().all()

    # Filter expired
    active = []
    for c in campaigns:
        if c.ends_at and c.ends_at < now:
            continue
        if c.total_spots and c.spots_taken >= c.total_spots:
            continue
        active.append(c)
    return active


async def get_recent_social_proof(db: AsyncSession, limit: int = 10) -> List[SocialProofEvent]:
    result = await db.execute(
        select(SocialProofEvent)
        .order_by(desc(SocialProofEvent.created_at))
        .limit(limit)
    )
    return result.scalars().all()


async def create_social_proof_event(db: AsyncSession, data: dict) -> SocialProofEvent:
    event = SocialProofEvent(**data)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event
