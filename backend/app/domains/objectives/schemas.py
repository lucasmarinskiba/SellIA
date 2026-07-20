"""Objectives & KPIs Pydantic Schemas."""

from pydantic import BaseModel, Field, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, Any


class DepartmentBase(BaseModel):
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=50)
    description: Optional[str] = None
    color: str = "#3B82F6"
    icon: str = "briefcase"


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentResponse(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    head_agent_personality_id: Optional[UUID] = None
    config: dict[str, Any]
    is_active: bool
    created_at: datetime


class BusinessObjectiveBase(BaseModel):
    name: str = Field(..., max_length=200)
    description: Optional[str] = None
    period: str = "monthly"
    target_value: float
    unit: str = "ARS"
    start_date: datetime
    end_date: datetime
    alert_threshold_percent: float = 80.0
    alert_channels: list[str] = []
    department_id: Optional[UUID] = None
    linked_workflow_id: Optional[UUID] = None
    linked_channel_platform: Optional[str] = None


class BusinessObjectiveCreate(BusinessObjectiveBase):
    pass


class BusinessObjectiveResponse(BusinessObjectiveBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    status: str
    current_value: float
    extra_data: dict[str, Any]
    is_active: bool
    created_at: datetime


class KPIBase(BaseModel):
    name: str = Field(..., max_length=200)
    slug: str = Field(..., max_length=50)
    description: Optional[str] = None
    metric_type: str
    data_source: str
    data_source_filter: dict[str, Any] = {}
    aggregation: str = "sum"
    target_value: Optional[float] = None
    unit: str = "count"
    period: str = "monthly"
    department_id: Optional[UUID] = None
    objective_id: Optional[UUID] = None


class KPICreate(KPIBase):
    pass


class KPIResponse(KPIBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    business_id: UUID
    current_value: float
    period_start: Optional[datetime] = None
    period_end: Optional[datetime] = None
    is_active: bool
    created_at: datetime
