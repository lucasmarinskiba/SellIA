"""App MVP Builder API Router"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.domains.users.models import User
from app.domains.agents.app_builder.service import AppBuilderService
from app.domains.agents.app_builder.schemas import (
    AppBuildJobCreate,
    AppBuildJobResponse,
    AppBuildJobDetailResponse,
    AppBuildPreviewResponse,
)

router = APIRouter(prefix="/app-builder", tags=["app-builder"])


@router.post("/generate", response_model=AppBuildJobResponse, status_code=status.HTTP_201_CREATED)
async def generate_app(
    data: AppBuildJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Inicia la generación de una aplicación MVP completa."""
    svc = AppBuilderService(db)
    job = await svc.generate_app_mvp(
        business_id=data.business_id,
        app_description=data.description,
        features_list=data.features,
    )
    return job


@router.get("/jobs", response_model=list[AppBuildJobResponse])
async def list_jobs(
    business_id: UUID = Query(...),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AppBuilderService(db)
    return await svc.list_jobs(business_id, limit, offset)


@router.get("/jobs/{job_id}", response_model=AppBuildJobDetailResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AppBuilderService(db)
    job = await svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    # Cargar features
    from sqlalchemy import select
    from app.domains.agents.app_builder.models import AppFeature
    result = await db.execute(select(AppFeature).where(AppFeature.job_id == job_id).order_by(AppFeature.priority.desc()))
    features = result.scalars().all()
    base = {
        "id": job.id,
        "business_id": job.business_id,
        "app_name": job.app_name,
        "description": job.description,
        "features": job.features or [],
        "tech_stack": job.tech_stack,
        "status": job.status.value if hasattr(job.status, "value") else str(job.status),
        "code_zip_url": job.code_zip_url,
        "preview_url": job.preview_url,
        "deploy_instructions": job.deploy_instructions,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }
    return {**base, "features_detail": features}


@router.get("/jobs/{job_id}/download")
async def download_zip(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AppBuilderService(db)
    path = await svc.get_app_code(job_id)
    if not path:
        raise HTTPException(status_code=404, detail="ZIP no encontrado")
    return FileResponse(path, media_type="application/zip", filename=path.name)


@router.get("/jobs/{job_id}/preview", response_model=AppBuildPreviewResponse)
async def preview_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    svc = AppBuilderService(db)
    job = await svc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return AppBuildPreviewResponse(
        preview_url=job.preview_url,
        deploy_instructions=job.deploy_instructions,
        status=job.status.value if hasattr(job.status, "value") else str(job.status),
    )
