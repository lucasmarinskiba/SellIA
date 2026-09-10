"""Chatbots API: one sales bot per platform, configured and testable."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User

from . import service
from .models import BotFocus

router = APIRouter(prefix="/chatbots", tags=["Chatbots"])


class BotIn(BaseModel):
    enabled: Optional[bool] = None
    personality_slug: Optional[str] = Field(None, max_length=50)
    focus: Optional[BotFocus] = None
    custom_instructions: Optional[str] = Field(None, max_length=4000)
    handoff_keywords: Optional[list[str]] = None
    max_ai_replies: Optional[int] = Field(None, ge=1, le=50)


class TestIn(BaseModel):
    question: str = Field(..., min_length=2, max_length=1000)


async def _business_ids(db: AsyncSession, user: User) -> list[Any]:
    from app.domains.authority.service import business_ids_for

    return await business_ids_for(db, user.id)


@router.get("")
async def list_bots(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """One bot per connected platform, with what it really did there."""
    business_ids = await _business_ids(db, user)
    return await service.overview(db, business_ids)


@router.get("/personalities")
async def list_personalities(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return {"personalities": await service.personalities(db)}


@router.put("/{platform}")
async def update_bot(
    platform: str,
    payload: BotIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    business_ids = await _business_ids(db, user)
    if not business_ids:
        raise HTTPException(status_code=400, detail="Necesitás un negocio creado.")

    changes = payload.model_dump(exclude_unset=True)
    if "focus" in changes and changes["focus"] is not None:
        changes["focus"] = changes["focus"].value
    bot = await service.upsert_bot(db, business_ids[0], platform, changes)
    return service.serialize(bot)


@router.post("/{platform}/test")
async def test_bot(
    platform: str,
    payload: TestIn,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Preview this platform's bot on a question, sending nothing to anyone."""
    business_ids = await _business_ids(db, user)
    if not business_ids:
        raise HTTPException(status_code=400, detail="Necesitás un negocio creado.")
    return await service.test_reply(db, business_ids[0], platform, payload.question)
