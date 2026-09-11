"""Team performance API: the real work, per person."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User

from . import service

router = APIRouter(prefix="/team-performance", tags=["team-performance"])


@router.get("")
async def team_board(
    business_id: Optional[uuid.UUID] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict[str, Any]:
    """What each member of this team really did in the period.

    Replaces the XP ranking, which could only ever show the owner on top: the
    counters behind it are written for the business owner on every order,
    whoever actually closed it.
    """
    from app.domains.businesses.models import Business

    if business_id:
        owned = await db.execute(
            select(Business.id).where(
                Business.id == business_id, Business.user_id == current_user.id
            )
        )
        if not owned.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Negocio no encontrado")
        target = business_id
    else:
        first = await db.execute(
            select(Business.id)
            .where(Business.user_id == current_user.id, Business.is_active.is_(True))
            .order_by(Business.name)
            .limit(1)
        )
        target = first.scalar_one_or_none()
        if not target:
            return {
                "has_data": False,
                "headline": "Creá tu negocio para ver el rendimiento del equipo.",
                "members": [],
                "gaps": [],
                "period_days": days,
            }

    return await service.board(db, target, days=days)
