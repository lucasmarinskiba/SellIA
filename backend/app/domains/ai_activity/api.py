"""AI Activity API — per-user account summary + recent AI action feed."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from . import service

router = APIRouter(prefix="/ai-activity", tags=["AI Activity"])


@router.get("/summary")
async def account_summary(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Registration + questionnaire + AI-activity completeness for the current user."""
    return await service.get_account_summary(db, user)


@router.get("/account-kpis")
async def account_kpis(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Real KPIs for the current account only (canales, conversaciones,
    respuestas de la IA, acciones registradas). Unlike GET /brain/kpis, which
    aggregates an unowned global `leads` table, nothing here can belong to
    another account."""
    return await service.get_account_kpis(db, user)


@router.get("")
async def recent_actions(
    limit: int = Query(default=50, ge=1, le=200),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Recent real AI/automation actions taken for the current user's account(s)."""
    return {"actions": await service.list_recent_actions(db, user.id, limit)}
