"""Configuration API: one screen, three owners underneath."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.preferences import catalog, service
from app.domains.users.models import User

router = APIRouter(prefix="/preferences", tags=["preferences"])


async def _resolve_business(
    db: AsyncSession,
    user: User,
    business_id: Optional[uuid.UUID],
) -> Optional[uuid.UUID]:
    """The business being configured: the one asked for, or the user's first."""
    from app.domains.businesses.models import Business

    if business_id:
        result = await db.execute(
            select(Business.id).where(Business.id == business_id, Business.user_id == user.id)
        )
        owned = result.scalar_one_or_none()
        if not owned:
            raise HTTPException(status_code=404, detail="Negocio no encontrado")
        return owned

    result = await db.execute(
        select(Business.id).where(Business.user_id == user.id).order_by(Business.created_at).limit(1)
    )
    return result.scalar_one_or_none()


class PreferencesUpdate(BaseModel):
    """Every field optional: the screen saves sections, not the whole profile."""

    business_type: Optional[str] = None
    sales_model: Optional[str] = None
    niche: Optional[str] = None
    target_audience: Optional[str] = None
    value_proposition: Optional[str] = None
    price_range: Optional[str] = None
    primary_goal: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    primary_language: Optional[str] = None
    tone: Optional[str] = None
    interests: Optional[list[str]] = None
    challenges: Optional[list[str]] = None
    target_platforms: Optional[list[str]] = None
    languages: Optional[list[str]] = None
    markets: Optional[list[str]] = None
    tastes: Optional[list[str]] = None
    banned_topics: Optional[list[str]] = None
    display_currency: Optional[str] = Field(default=None, max_length=3)
    voice_notes: Optional[str] = None
    autonomous_replies: Optional[bool] = None


@router.get("")
async def get_preferences(
    business_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """The saved configuration, the options it can take, and what is missing."""
    resolved = await _resolve_business(db, current_user, business_id)
    profile = await service.load_profile(db, current_user.id, resolved)
    return {
        "business_id": str(resolved) if resolved else None,
        "has_business": resolved is not None,
        "profile": profile,
        "catalog": catalog.full_catalog(),
    }


@router.put("")
async def update_preferences(
    data: PreferencesUpdate,
    business_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    resolved = await _resolve_business(db, current_user, business_id)
    if not resolved:
        raise HTTPException(
            status_code=400,
            detail="Creá tu negocio antes de configurar las preferencias",
        )
    payload = data.model_dump(exclude_unset=True)
    profile = await service.save_profile(db, current_user.id, resolved, payload)
    return {"business_id": str(resolved), "profile": profile}


@router.get("/platform-suggestions")
async def platform_suggestions(
    business_id: Optional[uuid.UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """Platforms that fit this seller, with the reason each one is on the list."""
    resolved = await _resolve_business(db, current_user, business_id)
    if not resolved:
        return {"connected": [], "suggestions": [], "unknowns": ["Todavía no creaste un negocio."]}
    profile = await service.load_profile(db, current_user.id, resolved)
    return await service.suggest_platforms(db, resolved, profile)
