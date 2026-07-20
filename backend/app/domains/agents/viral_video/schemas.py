"""Viral Video Agent Schemas"""

from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
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
    provider_used: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    script: Optional[Dict[str, Any]] = None
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
    visual_direction: Optional[str] = None


class VideoScriptResponse(VideoScriptBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ViralVideoGenerateRequest(BaseModel):
    business_id: UUID
    topic: str
    platform: str = "tiktok"
    duration: int = 15
