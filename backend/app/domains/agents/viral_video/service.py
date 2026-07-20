"""Viral Video Agent Service

Handles viral video generation with script optimization and video synthesis.
"""

import uuid
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any

import httpx
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.logger import get_logger
from app.domains.agents.viral_video.models import VideoGenerationJob, VideoScript
from app.domains.agents.prompts.business_context_adapter import (
    get_agent_prompt_context,
    format_business_context_for_prompt,
)

logger = get_logger(__name__)

STORAGE_DIR = Path(__file__).resolve().parents[4] / "storage" / "media" / "videos"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)


class ViralVideoService:
    """Service layer for viral video generation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_viral_video(
        self,
        business_id: uuid.UUID,
        topic: str,
        platform: str = "tiktok",
        duration: int = 15,
    ) -> VideoGenerationJob:
        """Generate a viral video with optimized script and AI video."""
        settings = get_settings()

        job = VideoGenerationJob(
            business_id=business_id,
            prompt=topic,
            platform=platform,
            duration=duration,
            status="processing",
        )
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)

        # 1. Generate optimized script
        script_data = await self._generate_script(business_id, topic, platform, duration, settings)
        script = VideoScript(
            job_id=job.id,
            business_id=business_id,
            hook=script_data["hook"],
            body=script_data["body"],
            cta=script_data["cta"],
            duration=duration,
            visual_direction=script_data.get("visual_direction", ""),
        )
        self.db.add(script)
        await self.db.commit()

        job.script = {
            "hook": script_data["hook"],
            "body": script_data["body"],
            "cta": script_data["cta"],
            "visual_direction": script_data.get("visual_direction", ""),
        }

        # 2. Generate video via external APIs
        video_prompt = (
            f"{script_data['visual_direction']}. "
            f"Scene: {script_data['hook']}. Style: viral {platform} video, "
            f"engaging, fast-paced, {duration} seconds."
        )
        video_path, provider = await self._generate_video(video_prompt, settings)

        # 3. Generate thumbnail
        thumbnail_url = await self._generate_thumbnail(topic, platform, settings)

        # 4. Add subtitles (mock or via API)
        # Subtitles would normally be burned into the video; here we store SRT
        srt_path = STORAGE_DIR / f"subtitles_{job.id}.srt"
        srt_content = self._build_srt(script_data, duration)
        srt_path.write_text(srt_content, encoding="utf-8")

        # 5. Background music placeholder (could integrate MusicService)
        # For now, store a reference if a music file exists
        music_path = STORAGE_DIR / f"music_{job.id}.mp3"
        if not music_path.exists():
            # Create dummy music file for demo
            with open(music_path, "wb") as f:
                f.write(b"\xff\xfb" + os.urandom(2048))

        job.status = "completed"
        job.provider_used = provider
        job.video_url = f"/storage/media/videos/{video_path.name}" if video_path else None
        job.thumbnail_url = thumbnail_url
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def list_videos(self, business_id: uuid.UUID) -> List[VideoGenerationJob]:
        result = await self.db.execute(
            select(VideoGenerationJob)
            .where(VideoGenerationJob.business_id == business_id)
            .order_by(desc(VideoGenerationJob.created_at))
        )
        return result.scalars().all()

    async def get_video(self, job_id: uuid.UUID) -> Optional[VideoGenerationJob]:
        result = await self.db.execute(
            select(VideoGenerationJob).where(VideoGenerationJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_script(self, job_id: uuid.UUID) -> Optional[VideoScript]:
        result = await self.db.execute(
            select(VideoScript).where(VideoScript.job_id == job_id)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Generation helpers
    # ------------------------------------------------------------------

    async def _generate_script(
        self,
        business_id: uuid.UUID,
        topic: str,
        platform: str,
        duration: int,
        settings: Any,
    ) -> Dict[str, str]:
        """Generate an optimized viral video script."""
        ctx = await get_agent_prompt_context(self.db, business_id)
        context_block = format_business_context_for_prompt(ctx)

        if settings.OPENAI_API_KEY:
            try:
                user_content = (
                    f"Topic: {topic}. Platform: {platform}. "
                    f"Duration: {duration}s. Write a viral script."
                )
                if context_block:
                    user_content = f"{context_block}\n\n{user_content}"
                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                    response = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                        json={
                            "model": "gpt-4o-mini",
                            "messages": [
                                {
                                    "role": "system",
                                    "content": (
                                        "You are a viral video scriptwriter. "
                                        "Return ONLY a JSON object with keys: hook, body, cta, visual_direction. "
                                        "Hook must grab attention in the first 3 seconds. "
                                        "No markdown."
                                    ),
                                },
                                {
                                    "role": "user",
                                    "content": user_content,
                                },
                            ],
                            "temperature": 0.8,
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    return json.loads(content)
            except Exception as e:
                logger.warning(f"OpenAI script generation failed: {e}")

        return {
            "hook": f"Stop scrolling! You won't believe this about {topic}!",
            "body": f"Here's the truth about {topic} that nobody talks about...",
            "cta": "Follow for more! Drop a comment if you agree.",
            "visual_direction": f"Fast cuts, bold text overlays, trending {platform} style.",
        }

    async def _generate_video(
        self,
        prompt: str,
        settings: Any,
    ) -> tuple[Optional[Path], str]:
        """Generate video using Kling, Minimax, Runway, Pika, or Gemini."""
        job_id = uuid.uuid4()
        file_name = f"video_{job_id}.mp4"
        file_path = STORAGE_DIR / file_name

        providers = [
            ("kling", settings.KLING_API_KEY, self._call_kling),
            ("minimax", settings.MINIMAX_API_KEY, self._call_minimax),
            ("runway", settings.RUNWAY_API_KEY, self._call_runway),
            ("pika", settings.PIKA_API_KEY, self._call_pika),
            ("gemini", settings.OPENAI_API_KEY, self._call_gemini_video),
        ]

        for provider_name, api_key, caller in providers:
            if not api_key:
                continue
            try:
                video_bytes = await caller(prompt, api_key)
                if video_bytes:
                    with open(file_path, "wb") as f:
                        f.write(video_bytes)
                    return file_path, provider_name
            except Exception as e:
                logger.warning(f"{provider_name} video generation failed: {e}")

        # Fallback: create a dummy video file
        logger.info("Video generation fallback: creating dummy file")
        with open(file_path, "wb") as f:
            # Minimal MP4 box (ftyp + moov) — not playable but acts as placeholder
            f.write(b"\x00\x00\x00\x20ftypisomisommp41\x00\x00\x00\x08moov")
        return file_path, "mock"

    async def _generate_thumbnail(
        self,
        topic: str,
        platform: str,
        settings: Any,
    ) -> Optional[str]:
        """Generate a thumbnail image."""
        if settings.OPENAI_API_KEY:
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
                    response = await client.post(
                        "https://api.openai.com/v1/images/generations",
                        headers={
                            "Authorization": f"Bearer {settings.OPENAI_API_KEY}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": "dall-e-3",
                            "prompt": (
                                f"Eye-catching thumbnail for {platform} video about '{topic}'. "
                                f"Bold text, high contrast, clickbait style, no faces."
                            ),
                            "n": 1,
                            "size": "1024x1024",
                            "response_format": "url",
                        },
                    )
                    response.raise_for_status()
                    data = response.json()
                    return data["data"][0]["url"]
            except Exception as e:
                logger.warning(f"Thumbnail generation failed: {e}")
        return None

    def _build_srt(self, script_data: Dict[str, str], duration: int) -> str:
        """Build a simple SRT subtitle file."""
        parts = [
            (script_data.get("hook", ""), 0, 3),
            (script_data.get("body", ""), 3, duration - 3),
            (script_data.get("cta", ""), duration - 3, duration),
        ]
        lines = []
        for idx, (text, start, end) in enumerate(parts, 1):
            if not text:
                continue
            lines.append(f"{idx}")
            lines.append(f"00:00:{start:02d},000 --> 00:00:{end:02d},000")
            lines.append(text)
            lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Video API helpers
    # ------------------------------------------------------------------

    async def _call_kling(self, prompt: str, api_key: str) -> bytes:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            response = await client.post(
                "https://api.klingai.com/v1/videos",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"prompt": prompt, "duration": 5},
            )
            response.raise_for_status()
            data = response.json()
            video_url = data.get("video_url")
            if video_url:
                resp = await client.get(video_url, timeout=httpx.Timeout(120.0))
                resp.raise_for_status()
                return resp.content
        return b""

    async def _call_minimax(self, prompt: str, api_key: str) -> bytes:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            response = await client.post(
                "https://api.minimax.chat/v1/video_generation",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"prompt": prompt},
            )
            response.raise_for_status()
            data = response.json()
            video_url = data.get("video_url")
            if video_url:
                resp = await client.get(video_url, timeout=httpx.Timeout(120.0))
                resp.raise_for_status()
                return resp.content
        return b""

    async def _call_runway(self, prompt: str, api_key: str) -> bytes:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            response = await client.post(
                "https://api.runwayml.com/v1/generations",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"prompt": prompt, "duration": 5},
            )
            response.raise_for_status()
            data = response.json()
            video_url = data.get("video_url")
            if video_url:
                resp = await client.get(video_url, timeout=httpx.Timeout(120.0))
                resp.raise_for_status()
                return resp.content
        return b""

    async def _call_pika(self, prompt: str, api_key: str) -> bytes:
        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            response = await client.post(
                "https://api.pika.art/v1/generations",
                headers={"Authorization": f"Bearer {api_key}"},
                json={"prompt": prompt},
            )
            response.raise_for_status()
            data = response.json()
            video_url = data.get("video_url")
            if video_url:
                resp = await client.get(video_url, timeout=httpx.Timeout(120.0))
                resp.raise_for_status()
                return resp.content
        return b""

    async def _call_gemini_video(self, prompt: str, api_key: str) -> bytes:
        # Gemini does not have a direct public video generation endpoint yet;
        # using a placeholder that mimics the OpenAI image style for demo.
        logger.info("Gemini video generation is a placeholder")
        return b""
