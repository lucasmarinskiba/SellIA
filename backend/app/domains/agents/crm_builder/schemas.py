"""CRM Builder Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CRMModuleBase(BaseModel):
    module_name: str
    config: dict[str, Any] = Field(default_factory=dict)


class CRMModuleCreate(CRMModuleBase):
    pass


class CRMModuleResponse(CRMModuleBase):
    id: UUID
    job_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CRMBuildJobCreate(BaseModel):
    business_id: UUID
    crm_name: str
    modules: list[CRMModuleCreate] = Field(default_factory=list)


class CRMBuildJobUpdate(BaseModel):
    status: str | None = None
    code_url: str | None = None


class CRMBuildJobResponse(BaseModel):
    id: UUID
    business_id: UUID
    crm_name: str
    modules: list[dict[str, Any]] = Field(default_factory=list)
    status: str
    code_url: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CRMBuildJobDetailResponse(CRMBuildJobResponse):
    modules_detail: list[CRMModuleResponse] = Field(default_factory=list)
