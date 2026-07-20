"""Music Agent API Router"""

import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.music_agent.schemas import (
    MusicGenerateRequest,
    MusicTrackResponse,
    MusicGenerationJobResponse,
)
from app.domains.agents.music_agent.service import MusicService, STORAGE_DIR

router = APIRouter(prefix="/agents/music-agent", tags=["music-agent"])


@router.post("/generate", response_model=MusicTrackResponse, status_code=status.HTTP_201_CREATED)
async def generate_track(
    req: MusicGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MusicService(db)
    track = await service.generate_music(
        business_id=req.business_id,
        prompt=req.prompt,
        genre=req.genre,
        duration=req.duration,
    )
    return track


@router.get("/tracks", response_model=list[MusicTrackResponse])
async def list_tracks(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MusicService(db)
    return await service.list_tracks(business_id)


@router.get("/tracks/{track_id}", response_model=MusicTrackResponse)
async def get_track(
    track_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MusicService(db)
    track = await service.get_track(track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track no encontrado")
    return track


@router.get("/tracks/{track_id}/download")
async def download_track(
    track_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = MusicService(db)
    track = await service.get_track(track_id)
    if not track or not track.file_url:
        raise HTTPException(status_code=404, detail="Track o archivo no encontrado")

    file_name = os.path.basename(track.file_url)
    file_path = STORAGE_DIR / file_name
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Archivo no encontrado en disco")

    return FileResponse(
        path=str(file_path),
        media_type="audio/mpeg",
        filename=file_name,
    )
