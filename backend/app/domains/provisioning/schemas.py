from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


class ResourceRequestCreate(BaseModel):
    resource_type: str = Field(..., pattern="^(ssl_certificate|s3_bucket|dns_record)$")
    name: str = Field(..., min_length=1, max_length=255)
    parameters: dict[str, Any] = Field(default_factory=dict)


class ResourceRequestUpdate(BaseModel):
    status: str | None = Field(None, pattern="^(pending|processing|completed|failed|cancelled)$")
    error_message: str | None = None
    provider_reference: str | None = None


class ResourceRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    resource_type: str
    name: str
    parameters: dict[str, Any]
    status: str
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    error_message: str | None
    provider_reference: str | None


class ResourceJobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    request_id: UUID
    job_type: str
    status: str
    started_at: datetime | None
    completed_at: datetime | None
    error_message: str | None
    result: dict[str, Any]


class ResourceEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    request_id: UUID
    event_type: str
    message: str | None
    metadata_: dict[str, Any] = Field(alias="metadata")
    created_at: datetime


class ResourceRequestDetailOut(ResourceRequestOut):
    jobs: list[ResourceJobOut] = []
    events: list[ResourceEventOut] = []
