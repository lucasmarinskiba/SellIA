"""Brand Visual Agent Schemas"""

from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class BrandKitJobBase(BaseModel):
    business_id: UUID
    brand_name: str
    industry: str


class BrandKitJobCreate(BrandKitJobBase):
    style_preferences: Optional[Dict[str, Any]] = None


class BrandKitJobResponse(BrandKitJobBase):
    id: UUID
    colors: Optional[List[Dict[str, Any]]] = None
    fonts: Optional[List[Dict[str, Any]]] = None
    logo_url: Optional[str] = None
    assets: Optional[Dict[str, Any]] = None
    status: str = "pending"
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BrandAssetBase(BaseModel):
    job_id: UUID
    business_id: UUID
    asset_type: str
    file_url: str
    config: Optional[Dict[str, Any]] = None


class BrandAssetResponse(BrandAssetBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BrandKitGenerateRequest(BaseModel):
    business_id: UUID
    brand_name: str
    industry: str
    style_preferences: Optional[Dict[str, Any]] = None
