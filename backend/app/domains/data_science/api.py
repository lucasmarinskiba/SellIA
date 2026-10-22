"""Data science API — the account's own numbers, with their reading."""

from __future__ import annotations

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User

from . import sales, service

router = APIRouter(prefix="/data-science", tags=["Data Science"])


@router.get("/insights")
async def insights(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: Annotated[int, Query(ge=7, le=180)] = 30,
) -> dict[str, Any]:
    """Real metrics for this account, each with the evidence behind it: counts,
    95% Wilson intervals, medians with quartiles, and an explicit statement when
    the sample is too small to conclude anything."""
    return await service.get_insights(db, user, days=days)


@router.get("/sales")
async def sales_analysis(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    days: Annotated[int, Query(ge=7, le=365)] = 90,
) -> dict[str, Any]:
    """The account's real orders, analysed: revenue over time, ticket
    distribution, per-platform comparison, when people buy, the status funnel,
    repeat customers and revenue concentration. Amounts are grouped by currency
    and never summed across them."""
    return await sales.get_sales_analysis(db, user, days=days)
