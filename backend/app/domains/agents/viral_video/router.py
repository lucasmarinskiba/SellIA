"""Viral Video Agent API Router"""

import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.viral_video.schemas import (
    ViralVideoGenerateRequest,
    VideoGenerationJobResponse,
    VideoScriptResponse,
)
from app.domains.agents.viral_video.service import ViralVideoService, STORAGE_DIR

router = APIRouter(prefix="/agents/viral-video", tags=["viral-video"])


@router.post("/generate", response_model=VideoGenerationJobResponse, status_code=status.HTTP_201_CREATED)
async def generate_video(
    req: ViralVideoGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ViralVideoService(db)
    job = await service.generate_viral_video(
        business_id=req.business_id,
        topic=req.topic,
        platform=req.platform,
        duration=req.duration,
    )
    return job


@router.get("/videos", response_model=list[VideoGenerationJobResponse])
async def list_videos(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ViralVideoService(db)
    return await service.list_videos(business_id)


@router.get("/videos/{job_id}", response_model=VideoGenerationJobResponse)
async def get_video(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ViralVideoService(db)
    job = await service.get_video(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Video no encontrado")
    return job


@router.get("/videos/{job_id}/script", response_model=VideoScriptResponse)
async def get_video_script(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ViralVideoService(db)
    script = await service.get_script(job_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script no encontrado")
    return script


@router.get("/videos/{job_id}/download")
async def download_video(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ViralVideoService(db)
    job = await service.get_video(job_id)
    if not job or not job.video_url:
        raise HTTPException(status_code=404, detail="Video o archivo no encontrado")

    file_name = os.path.basename(job.video_url)
    file_path = STORAGE_DIR / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")

    return FileResponse(
        path=str(file_path),
        media_type="video/mp4",
        filename=file_name,
    )
