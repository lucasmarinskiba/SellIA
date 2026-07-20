"""Music Agent Schemas"""

from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class MusicGenerationJobBase(BaseModel):
    business_id: UUID
    prompt: str
    genre: str = "corporate"
    duration: int = 30


class MusicGenerationJobCreate(MusicGenerationJobBase):
    pass


class MusicGenerationJobResponse(MusicGenerationJobBase):
    id: UUID
    status: str = "pending"
    provider_used: Optional[str] = None
    file_url: Optional[str] = None
    file_format: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MusicTrackBase(BaseModel):
    business_id: UUID
    track_name: str
    genre: str
    mood: Optional[str] = None
    tempo: Optional[int] = None
    duration: int
    file_url: str
    usage_rights: Optional[str] = "commercial"


class MusicTrackCreate(MusicTrackBase):
    job_id: Optional[UUID] = None


class MusicTrackResponse(MusicTrackBase):
    id: UUID
    job_id: Optional[UUID] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MusicGenerateRequest(BaseModel):
    business_id: UUID
    prompt: str
    genre: str = "corporate"
    duration: int = 30
