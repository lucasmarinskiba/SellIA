"""Objectives & KPIs API Router."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.objectives.models import Department
from app.domains.objectives.schemas import (
    BusinessObjectiveCreate,
    BusinessObjectiveResponse,
    DepartmentCreate,
    DepartmentResponse,
    KPICreate,
    KPIResponse,
)
from app.domains.objectives.services import ObjectiveService
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/objectives", tags=["Objectives & KPIs"])


@router.post(
    "/departments",
    response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_department(
    business_id: UUID,
    dept_in: DepartmentCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    service = ObjectiveService(db)
    dept = await service.create_department(
        business_id=business_id, **dept_in.model_dump()
    )
    return dept


@router.get("/departments", response_model=list[DepartmentResponse])
async def list_departments(
    business_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    result = await db.execute(
        select(Department).where(
            Department.business_id == business_id, Department.is_active == True
        )
    )
    return result.scalars().all()


@router.post(
    "", response_model=BusinessObjectiveResponse, status_code=status.HTTP_201_CREATED
)
async def create_objective(
    business_id: UUID,
    obj_in: BusinessObjectiveCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    service = ObjectiveService(db)
    obj = await service.create_objective(business_id=business_id, **obj_in.model_dump())
    return obj


@router.get("", response_model=list[BusinessObjectiveResponse])
async def list_objectives(
    business_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    status: str | None = None,
):
    service = ObjectiveService(db)
    return await service.get_objectives_for_business(business_id, status)


@router.post("/kpis", response_model=KPIResponse, status_code=status.HTTP_201_CREATED)
async def create_kpi(
    business_id: UUID,
    kpi_in: KPICreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    service = ObjectiveService(db)
    kpi = await service.create_kpi(business_id=business_id, **kpi_in.model_dump())
    return kpi


@router.get("/kpis", response_model=list[KPIResponse])
async def list_kpis(
    business_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    period: str | None = None,
):
    service = ObjectiveService(db)
    return await service.get_kpis_for_business(business_id, period)
