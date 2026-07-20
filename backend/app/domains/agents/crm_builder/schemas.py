"""CRM Builder Schemas"""

from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class CRMModuleBase(BaseModel):
    module_name: str
    config: Dict[str, Any] = Field(default_factory=dict)


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
    modules: List[CRMModuleCreate] = Field(default_factory=list)


class CRMBuildJobUpdate(BaseModel):
    status: Optional[str] = None
    code_url: Optional[str] = None


class CRMBuildJobResponse(BaseModel):
    id: UUID
    business_id: UUID
    crm_name: str
    modules: List[Dict[str, Any]] = Field(default_factory=list)
    status: str
    code_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CRMBuildJobDetailResponse(CRMBuildJobResponse):
    modules_detail: List[CRMModuleResponse] = Field(default_factory=list)
