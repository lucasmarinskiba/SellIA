from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.kpi_architect.service import KPIArchitectService

router = APIRouter(prefix="/kpi-architect", tags=["kpi-architect"])


@router.post("/dashboards", status_code=status.HTTP_201_CREATED)
async def generate_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = KPIArchitectService(db)
    try:
        dashboard = await service.generate_dashboard(current_user.business_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "id": dashboard.id,
        "business_id": dashboard.business_id,
        "dashboard_name": dashboard.dashboard_name,
        "refresh_interval": dashboard.refresh_interval,
        "is_default": dashboard.is_default,
        "widgets": dashboard.widgets,
        "created_at": dashboard.created_at,
    }


@router.get("/dashboards")
async def list_dashboards(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = KPIArchitectService(db)
    result = await service.list_dashboards(
        business_id=current_user.business_id,
        limit=limit,
        offset=offset,
    )
    return {
        "total": result["total"],
        "dashboards": [
            {
                "id": d.id,
                "dashboard_name": d.dashboard_name,
                "is_default": d.is_default,
                "refresh_interval": d.refresh_interval,
                "created_at": d.created_at,
            }
            for d in result["dashboards"]
        ],
    }


@router.get("/dashboards/{dashboard_id}")
async def get_dashboard(
    dashboard_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = KPIArchitectService(db)
    config = await service.get_dashboard_config(dashboard_id, current_user.business_id)
    if not config:
        raise HTTPException(status_code=404, detail="Dashboard not found")
    return config


@router.get("/dashboards/{dashboard_id}/data")
async def get_dashboard_data(
    dashboard_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = KPIArchitectService(db)
    try:
        data = await service.get_dashboard_data(dashboard_id, current_user.business_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return data


@router.get("/dashboards/{dashboard_id}/alerts")
async def get_alerts(
    dashboard_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = KPIArchitectService(db)
    try:
        alerts = await service.check_alerts(dashboard_id, current_user.business_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"alerts": alerts}
