"""Configuration API: one screen, three owners underneath."""

from __future__ import annotations

import uuid
from typing import Annotated, Any

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
    business_id: uuid.UUID | None,
) -> uuid.UUID | None:
    """The business being configured: the one asked for, or the user's first."""
    from app.domains.businesses.models import Business

    if business_id:
        result = await db.execute(
            select(Business.id).where(
                Business.id == business_id, Business.user_id == user.id
            )
        )
        owned = result.scalar_one_or_none()
        if not owned:
            raise HTTPException(status_code=404, detail="Negocio no encontrado")
        return owned

    # Ordered by name, not by creation date: the businesses table has no
    # created_at column, and reaching for one raised AttributeError on every
    # call to this endpoint — a 500 before any of it ran.
    result = await db.execute(
        select(Business.id)
        .where(Business.user_id == user.id, Business.is_active.is_(True))
        .order_by(Business.name)
        .limit(1)
    )
    return result.scalar_one_or_none()


class PreferencesUpdate(BaseModel):
    """Every field optional: the screen saves sections, not the whole profile."""

    business_type: str | None = None
    sales_model: str | None = None
    niche: str | None = None
    target_audience: str | None = None
    value_proposition: str | None = None
    price_range: str | None = None
    primary_goal: str | None = None
    country: str | None = None
    city: str | None = None
    primary_language: str | None = None
    tone: str | None = None
    interests: list[str] | None = None
    challenges: list[str] | None = None
    target_platforms: list[str] | None = None
    languages: list[str] | None = None
    markets: list[str] | None = None
    tastes: list[str] | None = None
    banned_topics: list[str] | None = None
    display_currency: str | None = Field(default=None, max_length=3)
    voice_notes: str | None = None
    autonomous_replies: bool | None = None


@router.get("")
async def get_preferences(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    business_id: Annotated[uuid.UUID | None, Query()] = None,
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
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    business_id: Annotated[uuid.UUID | None, Query()] = None,
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
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_active_user)],
    business_id: Annotated[uuid.UUID | None, Query()] = None,
) -> dict[str, Any]:
    """Platforms that fit this seller, with the reason each one is on the list."""
    resolved = await _resolve_business(db, current_user, business_id)
    if not resolved:
        return {
            "connected": [],
            "suggestions": [],
            "unknowns": ["Todavía no creaste un negocio."],
        }
    profile = await service.load_profile(db, current_user.id, resolved)
    return await service.suggest_platforms(db, resolved, profile)
