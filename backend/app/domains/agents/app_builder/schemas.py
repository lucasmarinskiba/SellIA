"""App MVP Builder Schemas"""

from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class AppFeatureBase(BaseModel):
    feature_name: str
    description: Optional[str] = None
    priority: int = 1
    estimated_hours: Optional[int] = None


class AppFeatureCreate(AppFeatureBase):
    pass


class AppFeatureResponse(AppFeatureBase):
    id: UUID
    job_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppBuildJobBase(BaseModel):
    app_name: str
    description: str
    features: List[Dict[str, Any]] = Field(default_factory=list)
    tech_stack: str = "nextjs-fastapi-postgres"


class AppBuildJobCreate(BaseModel):
    business_id: UUID
    app_name: str
    description: str
    features: List[AppFeatureCreate] = Field(default_factory=list)
    tech_stack: str = "nextjs-fastapi-postgres"


class AppBuildJobUpdate(BaseModel):
    status: Optional[str] = None
    code_zip_url: Optional[str] = None
    preview_url: Optional[str] = None
    deploy_instructions: Optional[str] = None


class AppBuildJobResponse(BaseModel):
    id: UUID
    business_id: UUID
    app_name: str
    description: str
    features: List[Dict[str, Any]] = Field(default_factory=list)
    tech_stack: str
    status: str
    code_zip_url: Optional[str] = None
    preview_url: Optional[str] = None
    deploy_instructions: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AppBuildJobDetailResponse(AppBuildJobResponse):
    features_detail: List[AppFeatureResponse] = Field(default_factory=list)


class AppBuildPreviewResponse(BaseModel):
    preview_url: Optional[str] = None
    deploy_instructions: Optional[str] = None
    status: str
