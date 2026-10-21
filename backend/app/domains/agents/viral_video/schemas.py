"""Viral Video Agent Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class VideoGenerationJobBase(BaseModel):
    business_id: UUID
    prompt: str
    platform: str = "tiktok"
    duration: int = 15


class VideoGenerationJobCreate(VideoGenerationJobBase):
    pass


class VideoGenerationJobResponse(VideoGenerationJobBase):
    id: UUID
    status: str = "pending"
    provider_used: str | None = None
    video_url: str | None = None
    thumbnail_url: str | None = None
    script: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class VideoScriptBase(BaseModel):
    job_id: UUID
    business_id: UUID
    hook: str
    body: str
    cta: str
    duration: int
    visual_direction: str | None = None


class VideoScriptResponse(VideoScriptBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ViralVideoGenerateRequest(BaseModel):
    business_id: UUID
    topic: str
    platform: str = "tiktok"
    duration: int = 15
