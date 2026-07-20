"""Auto-Responder Pilot Agent Router"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.auto_responder import service as ar_service
from app.domains.agents.auto_responder.schemas import (
    AutoResponderRuleCreate,
    AutoResponderRuleUpdate,
    AutoResponderRuleOut,
    AutoResponderStatsOut,
    AutoResponseLogOut,
)

router = APIRouter(prefix="/auto-responder", tags=["auto-responder"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/rules", response_model=AutoResponderRuleOut, status_code=status.HTTP_201_CREATED)
async def create_rule(
    data: AutoResponderRuleCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new auto-responder rule."""
    rule = await ar_service.create_rule(db, data.business_id, data.model_dump())
    return rule


@router.get("/rules", response_model=list[AutoResponderRuleOut])
async def list_rules(
    business_id: UUID,
    active_only: bool = Query(True),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """List auto-responder rules for a business."""
    return await ar_service.list_rules(db, business_id, active_only)


@router.patch("/rules/{rule_id}", response_model=AutoResponderRuleOut)
async def update_rule(
    rule_id: UUID,
    data: AutoResponderRuleUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update an auto-responder rule."""
    try:
        rule = await ar_service.update_rule(db, rule_id, data.model_dump(exclude_unset=True))
        return rule
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.delete("/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete an auto-responder rule."""
    deleted = await ar_service.delete_rule(db, rule_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Regla no encontrada")
    return None


@router.get("/stats", response_model=AutoResponderStatsOut)
async def get_stats(
    business_id: UUID,
    days: int = Query(7, ge=1, le=90),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """Get auto-responder statistics."""
    stats = await ar_service.get_response_stats(db, business_id, days)
    return AutoResponderStatsOut(**stats)


@router.get("/logs", response_model=list[AutoResponseLogOut])
async def list_logs(
    business_id: UUID,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
    current_user: Annotated[User, Depends(get_current_user)] = None,
):
    """List auto-response logs."""
    return await ar_service.list_logs(db, business_id, limit, offset)
