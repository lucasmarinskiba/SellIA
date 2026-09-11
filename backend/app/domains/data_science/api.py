"""Data science API — the account's own numbers, with their reading."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User

from . import sales, service

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


@router.get("/sales")
async def sales_analysis(
    days: int = Query(90, ge=7, le=365),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """The account's real orders, analysed: revenue over time, ticket
    distribution, per-platform comparison, when people buy, the status funnel,
    repeat customers and revenue concentration. Amounts are grouped by currency
    and never summed across them."""
    return await sales.get_sales_analysis(db, user, days=days)
