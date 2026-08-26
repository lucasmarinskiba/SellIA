"""Business Context API"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from .service import BusinessContextService
from .schemas import BusinessContextCreate, BusinessContextUpdate, BusinessContextRead
from .models import BusinessContext
from .angles_service import generate_communication_angles

router = APIRouter(prefix="/business-context", tags=["Business Context"])


def get_service(db: AsyncSession = Depends(get_db)) -> BusinessContextService:
    return BusinessContextService(db)


@router.get("", response_model=BusinessContextRead)
async def get_context(
    business_id: Optional[uuid.UUID] = Query(None),
    user: User = Depends(get_current_user),
    service: BusinessContextService = Depends(get_service),
):
    ctx = await service.get_or_create_context(user.id, business_id)
    return BusinessContextRead.model_validate(ctx)


@router.post("", response_model=BusinessContextRead)
async def create_or_update_context(
    data: BusinessContextUpdate,
    business_id: Optional[uuid.UUID] = Query(None),
    user: User = Depends(get_current_user),
    service: BusinessContextService = Depends(get_service),
):
    ctx = await service.get_or_create_context(user.id, business_id)
    updated = await service.update_context(user.id, ctx.id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Contexto no encontrado")
    return BusinessContextRead.model_validate(updated)


@router.get("/detect", response_model=BusinessContextRead)
async def detect_context(
    business_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: BusinessContextService = Depends(get_service),
):
    ctx = await service.detect_context_from_business_data(user.id, business_id)
    return BusinessContextRead.model_validate(ctx)


@router.get("/reach-analysis")
async def reach_analysis(
    context_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: BusinessContextService = Depends(get_service),
):
    return await service.analyze_reach(user.id, context_id)


@router.get("/channel-gaps")
async def channel_gaps(
    context_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: BusinessContextService = Depends(get_service),
):
    return await service.analyze_channel_gaps(user.id, context_id)


@router.get("/recommended-playbooks")
async def recommended_playbooks(
    context_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: BusinessContextService = Depends(get_service),
):
    return await service.generate_recommended_playbooks(user.id, context_id)


@router.post("/{context_id}/generate-angles", response_model=BusinessContextRead)
async def generate_angles(
    context_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    service: BusinessContextService = Depends(get_service),
):
    """Generate winning communication angles + offer summary from Nicho/Oferta."""
    result = await db.execute(
        select(BusinessContext).where(
            BusinessContext.id == context_id, BusinessContext.user_id == user.id
        )
    )
    ctx = result.scalar_one_or_none()
    if not ctx:
        raise HTTPException(status_code=404, detail="Contexto no encontrado")
    await generate_communication_angles(db, ctx)
    return BusinessContextRead.model_validate(ctx)


@router.get("/wizard")
async def wizard_state(
    context_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: BusinessContextService = Depends(get_service),
):
    return await service.get_wizard_state(user.id, context_id)


@router.post("/wizard/step/{step}")
async def save_wizard_step(
    step: int,
    data: BusinessContextUpdate,
    context_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: BusinessContextService = Depends(get_service),
):
    updated = await service.update_context(user.id, context_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Contexto no encontrado")
    return await service.get_wizard_state(user.id, context_id)
