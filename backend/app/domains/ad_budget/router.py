"""Ad-budget autopilot API — /api/v1/businesses/{business_id}/ad-budget/*"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.ad_budget.schemas import (
    ChannelCreate,
    ChannelResponse,
    ChannelUpdate,
    ConfigResponse,
    ConfigUpdate,
    ReallocationResponse,
    RunCycleRequest,
)
from app.domains.ad_budget.service import AdBudgetService
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/ad-budget", tags=["Ad Budget Autopilot"])


@router.get("/config", response_model=ConfigResponse)
async def get_config(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await AdBudgetService(db).get_or_create_config(business_id)


@router.patch("/config", response_model=ConfigResponse)
async def update_config(
    business_id: UUID,
    body: ConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await AdBudgetService(db).update_config(business_id, **body.model_dump(exclude_unset=True))


@router.get("/channels", response_model=list[ChannelResponse])
async def list_channels(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await AdBudgetService(db).list_channels(business_id)


@router.post("/channels", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    business_id: UUID,
    body: ChannelCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await AdBudgetService(db).create_channel(business_id, **body.model_dump(exclude_none=True))


@router.patch("/channels/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    business_id: UUID,
    channel_id: UUID,
    body: ChannelUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await AdBudgetService(db).update_channel(
            business_id, channel_id, **body.model_dump(exclude_unset=True)
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    business_id: UUID,
    channel_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        await AdBudgetService(db).delete_channel(business_id, channel_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/dashboard")
async def dashboard(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await AdBudgetService(db).dashboard(business_id)


@router.post("/run")
async def run_cycle(
    business_id: UUID,
    body: RunCycleRequest = RunCycleRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await AdBudgetService(db).run_cycle(
        business_id, force=body.force, auto_apply=body.auto_apply
    )


@router.get("/reallocations", response_model=list[ReallocationResponse])
async def list_reallocations(
    business_id: UUID,
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await AdBudgetService(db).history(business_id, limit=limit)


@router.post("/reallocations/{realloc_id}/apply", response_model=ReallocationResponse)
async def apply_reallocation(
    business_id: UUID,
    realloc_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await AdBudgetService(db).apply_reallocation(
            business_id, realloc_id, user_id=getattr(current_user, "id", None)
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/reallocations/{realloc_id}/reject", response_model=ReallocationResponse)
async def reject_reallocation(
    business_id: UUID,
    realloc_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await AdBudgetService(db).reject_reallocation(business_id, realloc_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
