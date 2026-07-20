"""Services Schemas"""

from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ========== Service Catalog Item Extra Data ==========

class ServiceItemConfig(BaseModel):
    modalities: List[str] = Field(default_factory=list)
    solution_types: List[str] = Field(default_factory=list)
    duration_minutes: int = 60
    buffer_minutes: int = 15
    requires_prep: bool = False
    materials_needed: List[str] = Field(default_factory=list)
    prerequisites: List[str] = Field(default_factory=list)
    service_area_km: Optional[float] = None
    travel_included: bool = False
    online_meeting_link: Optional[str] = None
    cancellation_policy_hours: int = 24
    reschedule_policy_hours: int = 12


# ========== Service Delivery Schemas ==========

class ServiceDeliveryCreate(BaseModel):
    order_id: UUID
    catalog_item_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    scheduled_at: Optional[datetime] = None
    modality: Optional[str] = None
    solution_type: Optional[str] = None
    location_address: Optional[Dict[str, Any]] = None
    meeting_url: Optional[str] = None
    estimated_duration_minutes: Optional[int] = None


class ServiceDeliveryUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    modality: Optional[str] = None
    solution_type: Optional[str] = None
    status: Optional[str] = None
    location_address: Optional[Dict[str, Any]] = None
    meeting_url: Optional[str] = None
    provider_notes: Optional[str] = None
    client_feedback: Optional[str] = None
    client_rating: Optional[int] = None
    materials_used: Optional[List[Dict[str, Any]]] = None
    diagnosis: Optional[Dict[str, Any]] = None
    follow_up_required: Optional[bool] = None
    follow_up_notes: Optional[str] = None
    actual_duration_minutes: Optional[int] = None
    is_active: Optional[bool] = None


class ServiceDeliveryResponse(BaseModel):
    id: UUID
    business_id: UUID
    order_id: UUID
    catalog_item_id: Optional[UUID]
    conversation_id: Optional[UUID]
    scheduled_at: Optional[datetime]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    modality: Optional[str]
    solution_type: Optional[str]
    status: str
    location_address: Dict[str, Any]
    meeting_url: Optional[str]
    provider_notes: Optional[str]
    client_feedback: Optional[str]
    client_rating: Optional[int]
    materials_used: List[Dict[str, Any]]
    diagnosis: Dict[str, Any]
    follow_up_required: bool
    follow_up_notes: Optional[str]
    reminders_sent: List[Dict[str, Any]]
    estimated_duration_minutes: Optional[int]
    actual_duration_minutes: Optional[int]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ========== Appointment Schemas ==========

class AppointmentCreate(BaseModel):
    service_delivery_id: Optional[UUID] = None
    order_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    client_name: Optional[str] = None
    client_email: Optional[str] = None
    client_phone: Optional[str] = None
    start_time: datetime
    end_time: datetime
    timezone: str = "America/Argentina/Buenos_Aires"
    modality: Optional[str] = None
    solution_type: Optional[str] = None
    service_name: Optional[str] = None
    location_address: Optional[Dict[str, Any]] = None
    meeting_url: Optional[str] = None
    preparation_notes: Optional[str] = None


class AppointmentUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timezone: Optional[str] = None
    modality: Optional[str] = None
    solution_type: Optional[str] = None
    service_name: Optional[str] = None
    location_address: Optional[Dict[str, Any]] = None
    meeting_url: Optional[str] = None
    status: Optional[str] = None
    provider_notes: Optional[str] = None
    preparation_notes: Optional[str] = None
    is_active: Optional[bool] = None


class AppointmentResponse(BaseModel):
    id: UUID
    business_id: UUID
    service_delivery_id: Optional[UUID]
    order_id: Optional[UUID]
    conversation_id: Optional[UUID]
    client_name: Optional[str]
    client_email: Optional[str]
    client_phone: Optional[str]
    start_time: datetime
    end_time: datetime
    timezone: str
    modality: Optional[str]
    solution_type: Optional[str]
    service_name: Optional[str]
    location_address: Dict[str, Any]
    meeting_url: Optional[str]
    status: str
    reminder_sent_at: Optional[datetime]
    confirmation_sent_at: Optional[datetime]
    confirmation_received_at: Optional[datetime]
    feedback_sent_at: Optional[datetime]
    feedback_received_at: Optional[datetime]
    provider_notes: Optional[str]
    preparation_notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AppointmentListResponse(BaseModel):
    items: List[AppointmentResponse]
    total: int


class CalendarQuery(BaseModel):
    from_date: datetime
    to_date: datetime


class AppointmentActionResponse(BaseModel):
    success: bool
    message: str
    appointment: Optional[AppointmentResponse] = None


class ServiceDeliveryActionResponse(BaseModel):
    success: bool
    message: str
    service_delivery: Optional[ServiceDeliveryResponse] = None
