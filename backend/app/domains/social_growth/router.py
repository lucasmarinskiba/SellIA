"""
Social Growth Toolkit Router
"""

from typing import Annotated, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.social_growth import service as social_service

router = APIRouter(prefix="/social-growth", tags=["social-growth"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/audit")
async def create_audit(
    platform: str,
    handle: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Run a social media profile audit (mock AI analysis for now)."""
    # In production, this would call an external API or AI service
    scores = {"bio": 72, "content": 65, "engagement": 58, "consistency": 80, "overall": 69}
    findings = [
        {"area": "bio", "issue": "Falta CTA claro", "suggestion": "Agregá 'DM para info' o un Linktree", "priority": "high"},
        {"area": "content", "issue": "Poco uso de Reels", "suggestion": "Publicá al menos 3 Reels por semana", "priority": "medium"},
        {"area": "engagement", "issue": "Respuestas lentas", "suggestion": "Respondé en menos de 1 hora", "priority": "high"},
    ]
    recommendations = [
        {"action": "Optimizar bio con keywords", "expected_impact": "+20% descubrimiento"},
        {"action": "Crear carrusel educativo semanal", "expected_impact": "+35% guardados"},
        {"action": "Usar Stories con encuestas", "expected_impact": "+50% interacción"},
    ]
    audit = await social_service.create_audit(db, current_user.id, platform, handle, findings, recommendations, scores)
    return {
        "overall_score": audit.overall_score,
        "scores": {
            "bio": audit.bio_score,
            "content": audit.content_score,
            "engagement": audit.engagement_score,
            "consistency": audit.consistency_score,
        },
        "findings": audit.findings,
        "recommendations": audit.recommendations,
    }


@router.get("/audit/{platform}")
async def get_latest_audit(
    platform: str,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    audit = await social_service.get_latest_audit(db, current_user.id, platform)
    if not audit:
        raise HTTPException(status_code=404, detail="No audit found. Run POST /audit first.")
    return {
        "overall_score": audit.overall_score,
        "scores": {
            "bio": audit.bio_score,
            "content": audit.content_score,
            "engagement": audit.engagement_score,
            "consistency": audit.consistency_score,
        },
        "findings": audit.findings,
        "recommendations": audit.recommendations,
        "created_at": audit.created_at,
    }


@router.get("/calendar")
async def get_calendar(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    days: int = Query(14, ge=1, le=30),
):
    slots = await social_service.get_calendar_slots(db, current_user.id, days)
    return [
        {
            "id": s.id,
            "platform": s.platform,
            "scheduled_at": s.scheduled_at,
            "content_type": s.content_type,
            "topic": s.topic,
            "caption_draft": s.caption_draft,
            "hashtag_suggestions": s.hashtag_suggestions,
            "best_time_reason": s.best_time_reason,
            "status": s.status,
        }
        for s in slots
    ]


@router.get("/competitors")
async def list_competitors(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    competitors = await social_service.get_competitors(db, current_user.id)
    return [
        {
            "id": c.id,
            "platform": c.platform,
            "competitor_handle": c.competitor_handle,
            "competitor_name": c.competitor_name,
            "follower_count": c.follower_count,
            "avg_likes": c.avg_likes,
            "post_frequency": c.post_frequency,
            "top_hashtags": c.top_hashtags,
            "content_themes": c.content_themes,
            "last_synced_at": c.last_synced_at,
        }
        for c in competitors
    ]
