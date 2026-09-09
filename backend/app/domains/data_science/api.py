"""Data science API — the account's own numbers, with their reading."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User

from . import service

router = APIRouter(prefix="/data-science", tags=["Data Science"])


@router.get("/insights")
async def insights(
    days: int = Query(30, ge=7, le=180),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Real metrics for this account, each with the evidence behind it: counts,
    95% Wilson intervals, medians with quartiles, and an explicit statement when
    the sample is too small to conclude anything."""
    return await service.get_insights(db, user, days=days)
