"""Brand Visual Agent Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BrandKitJobBase(BaseModel):
    business_id: UUID
    brand_name: str
    industry: str


class BrandKitJobCreate(BrandKitJobBase):
    style_preferences: dict[str, Any] | None = None


class BrandKitJobResponse(BrandKitJobBase):
    id: UUID
    colors: list[dict[str, Any]] | None = None
    fonts: list[dict[str, Any]] | None = None
    logo_url: str | None = None
    assets: dict[str, Any] | None = None
    status: str = "pending"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BrandAssetBase(BaseModel):
    job_id: UUID
    business_id: UUID
    asset_type: str
    file_url: str
    config: dict[str, Any] | None = None


class BrandAssetResponse(BrandAssetBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BrandKitGenerateRequest(BaseModel):
    business_id: UUID
    brand_name: str
    industry: str
    style_preferences: dict[str, Any] | None = None
