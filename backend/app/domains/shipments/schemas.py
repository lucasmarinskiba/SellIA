"""Shipments Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ========== Address Schema ==========


class Address(BaseModel):
    name: str
    company: str | None = None
    street: str
    city: str
    state: str
    zip: str
    country: str = "AR"
    phone: str | None = None
    email: str | None = None


# ========== Package Schema ==========


class PackageItem(BaseModel):
    name: str
    qty: int = 1
    sku: str | None = None


class Package(BaseModel):
    weight_kg: float = Field(..., gt=0)
    length_cm: float | None = None
    width_cm: float | None = None
    height_cm: float | None = None
    items: list[PackageItem] = Field(default_factory=list)
    description: str | None = None


# ========== Shipment Config Schemas ==========


class ShipmentConfigCreate(BaseModel):
    carrier: str
    label: str | None = None
    credentials: dict[str, Any] = Field(default_factory=dict)
    is_test_mode: bool = False
    is_active: bool = True
    default_service_type: str | None = None
    default_from_address: Address | None = None


class ShipmentConfigUpdate(BaseModel):
    label: str | None = None
    credentials: dict[str, Any] | None = None
    is_test_mode: bool | None = None
    is_active: bool | None = None
    default_service_type: str | None = None
    default_from_address: Address | None = None


class ShipmentConfigResponse(BaseModel):
    id: UUID
    business_id: UUID
    carrier: str
    label: str | None
    is_test_mode: bool
    is_active: bool
    default_service_type: str | None
    default_from_address: dict[str, Any] | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ========== Shipment Tracking Event Schemas ==========


class ShipmentTrackingEventResponse(BaseModel):
    id: UUID
    shipment_id: UUID
    event_code: str | None
    event_description: str
    location: str | None
    carrier_status: str | None
    event_at: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ========== Shipment Schemas ==========


class ShipmentCreate(BaseModel):
    order_id: UUID
    config_id: UUID | None = None
    carrier: str
    service_type: str | None = "standard"
    from_address: Address | None = None
    to_address: Address | None = None
    package: Package
    shipping_cost: float | None = None
    insurance_amount: float | None = None
    declared_value: float | None = None
    estimated_delivery_date: datetime | None = None
    notes: str | None = None
    auto_generate_label: bool = False
    notify_customer: bool = False
    notification_channel: str | None = None


class ShipmentUpdate(BaseModel):
    tracking_number: str | None = None
    tracking_url: str | None = None
    status: str | None = None
    label_url: str | None = None
    label_data: str | None = None
    shipping_cost: float | None = None
    estimated_delivery_date: datetime | None = None
    actual_delivery_date: datetime | None = None
    notes: str | None = None
    is_active: bool | None = None


class ShipmentResponse(BaseModel):
    id: UUID
    business_id: UUID
    order_id: UUID
    config_id: UUID | None
    carrier: str
    service_type: str
    status: str
    tracking_number: str | None
    tracking_url: str | None
    label_url: str | None
    from_address: dict[str, Any]
    to_address: dict[str, Any]
    package: dict[str, Any]
    shipping_cost: float | None
    insurance_amount: float | None
    declared_value: float | None
    estimated_delivery_date: datetime | None
    actual_delivery_date: datetime | None
    picked_up_at: datetime | None
    customer_notified_at: datetime | None
    notification_channel: str | None
    notes: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ShipmentDetailResponse(ShipmentResponse):
    tracking_events: list[ShipmentTrackingEventResponse] = Field(default_factory=list)


class ShipmentListResponse(BaseModel):
    items: list[ShipmentResponse]
    total: int


# ========== Carrier Info ==========


class CarrierInfo(BaseModel):
    id: str
    name: str
    label: str
    country: str
    service_types: list[str]
    features: list[str]  # label_generation, tracking, pickup, insurance, international
    icon: str | None = None


class RefreshTrackingResponse(BaseModel):
    success: bool
    new_events_count: int
    current_status: str
    message: str


class NotifyCustomerResponse(BaseModel):
    success: bool
    channel: str | None
    message: str
