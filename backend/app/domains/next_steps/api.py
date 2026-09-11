"""Qué hacer ahora, qué funciona, y a quién responder primero."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User

from . import ranking, service

router = APIRouter(prefix="/next-steps", tags=["Next steps"])


@router.get("")
async def next_steps(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """The prioritised actions for this account, each with the number behind it.

    Nothing here predicts a lift. Each item states a fact about the account's own
    rows and says why it matters; the decision stays with the seller. The response
    also lists which checks could not run, so an empty list cannot be mistaken for
    "everything is fine".
    """
    return await service.compute_actions(db, user)


@router.get("/ranking")
async def business_ranking(
    days: int = Query(90, ge=7, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Which products, customers and platforms are carrying this business.

    Amounts are grouped by currency and never summed across them, and a ranking
    built on too few orders says so instead of crowning a best seller.
    """
    return await ranking.business_ranking(db, user, days=days)


@router.get("/queue")
async def attention_queue(
    limit: int = Query(25, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Open conversations in the order worth answering, with the reason for each."""
    return await ranking.attention_queue(db, user, limit=limit)
