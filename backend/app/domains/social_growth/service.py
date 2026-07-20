"""
Social Growth Toolkit Service
"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.domains.social_growth.models import SocialProfileAudit, ContentCalendarSlot, CompetitorTracking


async def create_audit(db: AsyncSession, user_id: uuid.UUID, platform: str, handle: str, findings: list, recommendations: list, scores: dict) -> SocialProfileAudit:
    audit = SocialProfileAudit(
        user_id=user_id,
        platform=platform,
        handle=handle,
        bio_score=scores.get("bio", 0),
        content_score=scores.get("content", 0),
        engagement_score=scores.get("engagement", 0),
        consistency_score=scores.get("consistency", 0),
        overall_score=scores.get("overall", 0),
        findings=findings,
        recommendations=recommendations,
    )
    db.add(audit)
    await db.commit()
    await db.refresh(audit)
    return audit


async def get_latest_audit(db: AsyncSession, user_id: uuid.UUID, platform: str) -> Optional[SocialProfileAudit]:
    result = await db.execute(
        select(SocialProfileAudit)
        .where(SocialProfileAudit.user_id == user_id, SocialProfileAudit.platform == platform)
        .order_by(desc(SocialProfileAudit.created_at))
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_calendar_slots(db: AsyncSession, user_id: uuid.UUID, days: int = 14) -> List[ContentCalendarSlot]:
    since = datetime.now(timezone.utc) - timedelta(days=1)
    until = datetime.now(timezone.utc) + timedelta(days=days)
    result = await db.execute(
        select(ContentCalendarSlot)
        .where(
            ContentCalendarSlot.user_id == user_id,
            ContentCalendarSlot.scheduled_at >= since,
            ContentCalendarSlot.scheduled_at <= until,
        )
        .order_by(ContentCalendarSlot.scheduled_at)
    )
    return result.scalars().all()


async def get_competitors(db: AsyncSession, user_id: uuid.UUID) -> List[CompetitorTracking]:
    result = await db.execute(
        select(CompetitorTracking)
        .where(CompetitorTracking.user_id == user_id)
        .order_by(desc(CompetitorTracking.created_at))
    )
    return result.scalars().all()
