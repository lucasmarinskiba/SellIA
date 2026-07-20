"""Financial Planner Router"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.financial_planner import service as fp_service
from app.domains.agents.financial_planner.schemas import (
    FinancialPlanCreate,
    FinancialPlanOut,
    FinancialPlanExportOut,
)

router = APIRouter(prefix="/financial-planner", tags=["financial-planner"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/plans", response_model=FinancialPlanOut, status_code=status.HTTP_201_CREATED)
async def create_plan(
    data: FinancialPlanCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Crea un plan financiero con proyecciones para 12 meses."""
    from sqlalchemy import select
    from app.domains.businesses.models import Business
    result = await db.execute(
        select(Business).where(Business.user_id == current_user.id).limit(1)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    plan = await fp_service.create_financial_plan(
        db=db,
        business_id=business.id,
        plan_name=data.plan_name,
        historical_data=data.historical_data,
        assumptions=data.assumptions,
    )
    return plan


@router.get("/plans", response_model=list[FinancialPlanOut])
async def list_plans(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Lista los planes financieros del negocio."""
    from sqlalchemy import select
    from app.domains.businesses.models import Business
    result = await db.execute(
        select(Business).where(Business.user_id == current_user.id).limit(1)
    )
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")

    return await fp_service.list_plans(db, business.id)


@router.get("/plans/{plan_id}", response_model=FinancialPlanOut)
async def get_plan(
    plan_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Obtiene un plan financiero por ID."""
    plan = await fp_service.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan


@router.get("/plans/{plan_id}/export")
async def export_plan(
    plan_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    format: str = Query("csv", pattern="^(csv|json)$"),
):
    """Descarga el plan financiero en CSV o JSON."""
    plan = await fp_service.get_plan(db, plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")

    exported = await fp_service.export_plan(plan, format=format)
    if format == "json":
        return PlainTextResponse(
            content=exported["content"],
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={exported['filename']}"},
        )
    return PlainTextResponse(
        content=exported["content"],
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={exported['filename']}"},
    )
