"""Music Agent Schemas"""

from datetime import datetime
from uuid import UUID

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
    provider_used: str | None = None
    file_url: str | None = None
    file_format: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MusicTrackBase(BaseModel):
    business_id: UUID
    track_name: str
    genre: str
    mood: str | None = None
    tempo: int | None = None
    duration: int
    file_url: str
    usage_rights: str | None = "commercial"


class MusicTrackCreate(MusicTrackBase):
    job_id: UUID | None = None


class MusicTrackResponse(MusicTrackBase):
    id: UUID
    job_id: UUID | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MusicGenerateRequest(BaseModel):
    business_id: UUID
    prompt: str
    genre: str = "corporate"
    duration: int = 30
