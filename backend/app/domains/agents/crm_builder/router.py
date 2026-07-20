"""CRM Builder API Router"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.agents.crm_builder.service import CRMBuilderService
from app.domains.agents.crm_builder.schemas import (
    CRMBuildJobCreate,
    CRMBuildJobResponse,
    CRMBuildJobDetailResponse,
)

router = APIRouter(prefix="/crm-builder", tags=["crm-builder"])


@router.post("/generate", response_model=CRMBuildJobResponse, status_code=status.HTTP_201_CREATED)
async def generate_crm(
    data: CRMBuildJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Inicia la generación de un sistema CRM completo."""
    svc = CRMBuilderService(db)
    job = await svc.generate_crm(
        business_id=data.business_id,
        modules_list=data.modules,
    )
    return job


@router.get("/jobs", response_model=list[CRMBuildJobResponse])
async def list_jobs(
    business_id: UUID = Query(...),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = CRMBuilderService(db)
    return await svc.list_jobs(business_id, limit, offset)


@router.get("/jobs/{job_id}", response_model=CRMBuildJobDetailResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = CRMBuilderService(db)
    job = await svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    from sqlalchemy import select
    from app.domains.agents.crm_builder.models import CRMModule
    result = await db.execute(select(CRMModule).where(CRMModule.job_id == job_id))
    modules = result.scalars().all()
    base = {
        "id": job.id,
        "business_id": job.business_id,
        "crm_name": job.crm_name,
        "modules": job.modules or [],
        "status": job.status.value if hasattr(job.status, "value") else str(job.status),
        "code_url": job.code_url,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }
    return {**base, "modules_detail": modules}


@router.get("/jobs/{job_id}/download")
async def download_zip(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = CRMBuilderService(db)
    path = await svc.get_crm_code(job_id)
    if not path:
        raise HTTPException(status_code=404, detail="ZIP no encontrado")
    return FileResponse(path, media_type="application/zip", filename=path.name)
