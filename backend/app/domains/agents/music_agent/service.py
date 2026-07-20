"""Music Agent Service

Handles music generation via Suno / Mureka APIs.
"""

import uuid
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

import httpx
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logger import get_logger
from app.domains.agents.music_agent.models import MusicGenerationJob, MusicTrack

logger = get_logger(__name__)

STORAGE_DIR = Path(__file__).resolve().parents[4] / "storage" / "media" / "music"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class MusicService:
    """Service layer for music generation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_music(
        self,
        business_id: uuid.UUID,
        prompt: str,
        genre: str = "corporate",
        duration: int = 30,
    ) -> MusicTrack:
        """Generate a music track using Suno (primary) or Mureka (fallback)."""
        settings = get_settings()

        job = MusicGenerationJob(
            business_id=business_id,
            prompt=prompt,
            genre=genre,
            duration=duration,
            status="processing",
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        file_name = f"music_{job.id}.mp3"
        file_path = STORAGE_DIR / file_name

        audio_bytes = b""
        provider = None

        # Primary: Suno API
        if settings.SUNO_API_KEY:
            try:
                audio_bytes = await self._call_suno(prompt, genre, duration)
                provider = "suno"
            except Exception as e:
                logger.warning(f"Suno generation failed: {e}")

        # Fallback: Mureka API
        if not audio_bytes and settings.MUREKA_API_KEY:
            try:
                audio_bytes = await self._call_mureka(prompt, genre, duration)
                provider = "mureka"
            except Exception as e:
                logger.warning(f"Mureka generation failed: {e}")

        # Development fallback: create a small dummy file
        if not audio_bytes:
            logger.info("Music generation fallback: creating dummy file")
            audio_bytes = b"\xff\xfb" + os.urandom(1024)  # minimal mp3-ish header
            provider = "mock"

        with open(file_path, "wb") as f:
            f.write(audio_bytes)

        file_url = f"/storage/media/music/{file_name}"

        job.status = "completed"
        job.provider_used = provider
        job.file_url = str(file_url)
        job.file_format = "mp3"
        await self.db.commit()
        await self.db.refresh(job)

        track = MusicTrack(
            business_id=business_id,
            job_id=job.id,
            track_name=f"{genre.title()} Track — {prompt[:40]}",
            genre=genre,
            mood="energetic" if "energetic" in prompt.lower() else "neutral",
            tempo=120,
            duration=duration,
            file_url=str(file_url),
            usage_rights="commercial",
        )
        self.db.add(track)
        await self.db.commit()
        await self.db.refresh(track)
        return track

    async def list_tracks(self, business_id: uuid.UUID) -> List[MusicTrack]:
        """List generated music tracks for a business."""
        result = await self.db.execute(
            select(MusicTrack)
            .where(MusicTrack.business_id == business_id)
            .order_by(desc(MusicTrack.created_at))
        )
        return result.scalars().all()

    async def get_track(self, track_id: uuid.UUID) -> Optional[MusicTrack]:
        result = await self.db.execute(
            select(MusicTrack).where(MusicTrack.id == track_id)
        )
        return result.scalar_one_or_none()

    async def get_job(self, job_id: uuid.UUID) -> Optional[MusicGenerationJob]:
        result = await self.db.execute(
            select(MusicGenerationJob).where(MusicGenerationJob.id == job_id)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # External API helpers
    # ------------------------------------------------------------------

    async def _call_suno(self, prompt: str, genre: str, duration: int) -> bytes:
        settings = get_settings()
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            response = await client.post(
                "https://api.suno.ai/v1/generate",
                headers={"Authorization": f"Bearer {settings.SUNO_API_KEY}"},
                json={
                    "prompt": prompt,
                    "genre": genre,
                    "duration": duration,
                },
            )
            response.raise_for_status()
            data = response.json()
            audio_url = data.get("audio_url")
            if audio_url:
                audio_resp = await client.get(audio_url, timeout=httpx.Timeout(120.0))
                audio_resp.raise_for_status()
                return audio_resp.content
        return b""

    async def _call_mureka(self, prompt: str, genre: str, duration: int) -> bytes:
        settings = get_settings()
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            response = await client.post(
                "https://api.mureka.ai/v1/music/generate",
                headers={"Authorization": f"Bearer {settings.MUREKA_API_KEY}"},
                json={
                    "prompt": prompt,
                    "genre": genre,
                    "duration": duration,
                },
            )
            response.raise_for_status()
            data = response.json()
            audio_url = data.get("audio_url")
            if audio_url:
                audio_resp = await client.get(audio_url, timeout=httpx.Timeout(120.0))
                audio_resp.raise_for_status()
                return audio_resp.content
        return b""
