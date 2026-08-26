from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID
from datetime import datetime
from typing import Any

from app.domains.businesses.models import BusinessType


class BusinessBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: BusinessType
    description: str | None = None


class BusinessCreate(BusinessBase):
    config: dict[str, Any] | None = None


class BusinessUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    type: BusinessType | None = None
    description: str | None = None
    config: dict[str, Any] | None = None


class BusinessResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    name: str
    description: str | None
    type: BusinessType = BusinessType.SERVICES
