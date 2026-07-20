"""Shipments Schemas"""

from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


# ========== Address Schema ==========

class Address(BaseModel):
    name: str
    company: Optional[str] = None
    street: str
    city: str
    state: str
    zip: str
    country: str = "AR"
    phone: Optional[str] = None
    email: Optional[str] = None


# ========== Package Schema ==========

class PackageItem(BaseModel):
    name: str
    qty: int = 1
    sku: Optional[str] = None


class Package(BaseModel):
    weight_kg: float = Field(..., gt=0)
    length_cm: Optional[float] = None
    width_cm: Optional[float] = None
    height_cm: Optional[float] = None
    items: List[PackageItem] = Field(default_factory=list)
    description: Optional[str] = None


# ========== Shipment Config Schemas ==========

class ShipmentConfigCreate(BaseModel):
    carrier: str
    label: Optional[str] = None
    credentials: Dict[str, Any] = Field(default_factory=dict)
    is_test_mode: bool = False
    is_active: bool = True
    default_service_type: Optional[str] = None
    default_from_address: Optional[Address] = None


class ShipmentConfigUpdate(BaseModel):
    label: Optional[str] = None
    credentials: Optional[Dict[str, Any]] = None
    is_test_mode: Optional[bool] = None
    is_active: Optional[bool] = None
    default_service_type: Optional[str] = None
    default_from_address: Optional[Address] = None


class ShipmentConfigResponse(BaseModel):
    id: UUID
    business_id: UUID
    carrier: str
    label: Optional[str]
    is_test_mode: bool
    is_active: bool
    default_service_type: Optional[str]
    default_from_address: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ========== Shipment Tracking Event Schemas ==========

class ShipmentTrackingEventResponse(BaseModel):
    id: UUID
    shipment_id: UUID
    event_code: Optional[str]
    event_description: str
    location: Optional[str]
    carrier_status: Optional[str]
    event_at: datetime
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ========== Shipment Schemas ==========

class ShipmentCreate(BaseModel):
    order_id: UUID
    config_id: Optional[UUID] = None
    carrier: str
    service_type: Optional[str] = "standard"
    from_address: Optional[Address] = None
    to_address: Optional[Address] = None
    package: Package
    shipping_cost: Optional[float] = None
    insurance_amount: Optional[float] = None
    declared_value: Optional[float] = None
    estimated_delivery_date: Optional[datetime] = None
    notes: Optional[str] = None
    auto_generate_label: bool = False
    notify_customer: bool = False
    notification_channel: Optional[str] = None


class ShipmentUpdate(BaseModel):
    tracking_number: Optional[str] = None
    tracking_url: Optional[str] = None
    status: Optional[str] = None
    label_url: Optional[str] = None
    label_data: Optional[str] = None
    shipping_cost: Optional[float] = None
    estimated_delivery_date: Optional[datetime] = None
    actual_delivery_date: Optional[datetime] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ShipmentResponse(BaseModel):
    id: UUID
    business_id: UUID
    order_id: UUID
    config_id: Optional[UUID]
    carrier: str
    service_type: str
    status: str
    tracking_number: Optional[str]
    tracking_url: Optional[str]
    label_url: Optional[str]
    from_address: Dict[str, Any]
    to_address: Dict[str, Any]
    package: Dict[str, Any]
    shipping_cost: Optional[float]
    insurance_amount: Optional[float]
    declared_value: Optional[float]
    estimated_delivery_date: Optional[datetime]
    actual_delivery_date: Optional[datetime]
    picked_up_at: Optional[datetime]
    customer_notified_at: Optional[datetime]
    notification_channel: Optional[str]
    notes: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ShipmentDetailResponse(ShipmentResponse):
    tracking_events: List[ShipmentTrackingEventResponse] = Field(default_factory=list)


class ShipmentListResponse(BaseModel):
    items: List[ShipmentResponse]
    total: int


# ========== Carrier Info ==========

class CarrierInfo(BaseModel):
    id: str
    name: str
    label: str
    country: str
    service_types: List[str]
    features: List[str]  # label_generation, tracking, pickup, insurance, international
    icon: Optional[str] = None


class RefreshTrackingResponse(BaseModel):
    success: bool
    new_events_count: int
    current_status: str
    message: str


class NotifyCustomerResponse(BaseModel):
    success: bool
    channel: Optional[str]
    message: str
