"""Services Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ========== Service Catalog Item Extra Data ==========


class ServiceItemConfig(BaseModel):
    modalities: list[str] = Field(default_factory=list)
    solution_types: list[str] = Field(default_factory=list)
    duration_minutes: int = 60
    buffer_minutes: int = 15
    requires_prep: bool = False
    materials_needed: list[str] = Field(default_factory=list)
    prerequisites: list[str] = Field(default_factory=list)
    service_area_km: float | None = None
    travel_included: bool = False
    online_meeting_link: str | None = None
    cancellation_policy_hours: int = 24
    reschedule_policy_hours: int = 12


# ========== Service Delivery Schemas ==========


class ServiceDeliveryCreate(BaseModel):
    order_id: UUID
    catalog_item_id: UUID | None = None
    conversation_id: UUID | None = None
    scheduled_at: datetime | None = None
    modality: str | None = None
    solution_type: str | None = None
    location_address: dict[str, Any] | None = None
    meeting_url: str | None = None
    estimated_duration_minutes: int | None = None


class ServiceDeliveryUpdate(BaseModel):
    scheduled_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    modality: str | None = None
    solution_type: str | None = None
    status: str | None = None
    location_address: dict[str, Any] | None = None
    meeting_url: str | None = None
    provider_notes: str | None = None
    client_feedback: str | None = None
    client_rating: int | None = None
    materials_used: list[dict[str, Any]] | None = None
    diagnosis: dict[str, Any] | None = None
    follow_up_required: bool | None = None
    follow_up_notes: str | None = None
    actual_duration_minutes: int | None = None
    is_active: bool | None = None


class ServiceDeliveryResponse(BaseModel):
    id: UUID
    business_id: UUID
    order_id: UUID
    catalog_item_id: UUID | None
    conversation_id: UUID | None
    scheduled_at: datetime | None
    started_at: datetime | None
    completed_at: datetime | None
    cancelled_at: datetime | None
    modality: str | None
    solution_type: str | None
    status: str
    location_address: dict[str, Any]
    meeting_url: str | None
    provider_notes: str | None
    client_feedback: str | None
    client_rating: int | None
    materials_used: list[dict[str, Any]]
    diagnosis: dict[str, Any]
    follow_up_required: bool
    follow_up_notes: str | None
    reminders_sent: list[dict[str, Any]]
    estimated_duration_minutes: int | None
    actual_duration_minutes: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ========== Appointment Schemas ==========


class AppointmentCreate(BaseModel):
    service_delivery_id: UUID | None = None
    order_id: UUID | None = None
    conversation_id: UUID | None = None
    client_name: str | None = None
    client_email: str | None = None
    client_phone: str | None = None
    start_time: datetime
    end_time: datetime
    timezone: str = "America/Argentina/Buenos_Aires"
    modality: str | None = None
    solution_type: str | None = None
    service_name: str | None = None
    location_address: dict[str, Any] | None = None
    meeting_url: str | None = None
    preparation_notes: str | None = None


class AppointmentUpdate(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None
    timezone: str | None = None
    modality: str | None = None
    solution_type: str | None = None
    service_name: str | None = None
    location_address: dict[str, Any] | None = None
    meeting_url: str | None = None
    status: str | None = None
    provider_notes: str | None = None
    preparation_notes: str | None = None
    is_active: bool | None = None


class AppointmentResponse(BaseModel):
    id: UUID
    business_id: UUID
    service_delivery_id: UUID | None
    order_id: UUID | None
    conversation_id: UUID | None
    client_name: str | None
    client_email: str | None
    client_phone: str | None
    start_time: datetime
    end_time: datetime
    timezone: str
    modality: str | None
    solution_type: str | None
    service_name: str | None
    location_address: dict[str, Any]
    meeting_url: str | None
    status: str
    reminder_sent_at: datetime | None
    confirmation_sent_at: datetime | None
    confirmation_received_at: datetime | None
    feedback_sent_at: datetime | None
    feedback_received_at: datetime | None
    provider_notes: str | None
    preparation_notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AppointmentListResponse(BaseModel):
    items: list[AppointmentResponse]
    total: int


class CalendarQuery(BaseModel):
    from_date: datetime
    to_date: datetime


class AppointmentActionResponse(BaseModel):
    success: bool
    message: str
    appointment: AppointmentResponse | None = None


class ServiceDeliveryActionResponse(BaseModel):
    success: bool
    message: str
    service_delivery: ServiceDeliveryResponse | None = None
