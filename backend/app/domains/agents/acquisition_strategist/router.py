"""Acquisition Strategist Router"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.acquisition_strategist import service as acq_service
from app.domains.agents.acquisition_strategist.schemas import (
    AcquisitionStrategyCreate,
    AcquisitionStrategyOut,
)

router = APIRouter(prefix="/acquisition-strategist", tags=["acquisition-strategist"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/strategies", response_model=AcquisitionStrategyOut, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    data: AcquisitionStrategyCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Diseña una nueva estrategia de adquisición de clientes."""
    from sqlalchemy import select
    from app.domains.businesses.models import Business
    result = await db.execute(
        select(Business).where(Business.user_id == current_user.id).limit(1)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    strategy = await acq_service.design_acquisition_strategy(
        db=db,
        business_id=business.id,
        strategy_name=data.strategy_name,
        goals=data.goals,
        budget=data.budget,
    )
    return strategy


@router.get("/strategies", response_model=list[AcquisitionStrategyOut])
async def list_strategies(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Lista las estrategias de adquisición del negocio."""
    from sqlalchemy import select
    from app.domains.businesses.models import Business
    result = await db.execute(
        select(Business).where(Business.user_id == current_user.id).limit(1)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    return await acq_service.list_strategies(db, business.id)


@router.get("/strategies/{strategy_id}", response_model=AcquisitionStrategyOut)
async def get_strategy(
    strategy_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Obtiene una estrategia de adquisición por ID."""
    strategy = await acq_service.get_strategy(db, strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="Estrategia no encontrada")
    return strategy
