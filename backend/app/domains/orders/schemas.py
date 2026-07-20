"""Orders Schemas"""

from uuid import UUID
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, field_serializer
from app.core.pii_masking import mask_email, mask_phone, mask_name


class OrderItem(BaseModel):
    name: str
    sku: Optional[str] = None
    quantity: int = 1
    unit_price: float
    total_price: float


class OrderBase(BaseModel):
    order_number: Optional[str] = None
    items: List[OrderItem] = Field(default_factory=list)
    total_amount: float
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    discount_amount: Optional[float] = None
    shipping_cost: Optional[float] = None
    currency: str = "ARS"
    status: str = "pending"
    payment_method: Optional[str] = None
    payment_status: str = "pending"
    shipping_address: Dict[str, Any] = Field(default_factory=dict)
    shipping_provider: Optional[str] = None
    tracking_number: Optional[str] = None
    notes: Optional[str] = None
    customer_name: Optional[str] = None
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    external_id: Optional[str] = None
    external_platform: Optional[str] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)


class OrderCreate(OrderBase):
    business_id: UUID
    conversation_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    payment_status: Optional[str] = None
    paid_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    tracking_number: Optional[str] = None
    shipping_provider: Optional[str] = None
    notes: Optional[str] = None
    extra_data: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class OrderResponse(OrderBase):
    id: UUID
    business_id: UUID
    conversation_id: Optional[UUID] = None
    deal_id: Optional[UUID] = None
    source_channel: Optional[str] = None
    source_campaign: Optional[str] = None
    source_workflow_id: Optional[UUID] = None
    source_agent_id: Optional[UUID] = None
    first_touch_channel: Optional[str] = None
    last_touch_channel: Optional[str] = None
    attribution_model: str
    paid_at: Optional[datetime] = None
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("customer_name")
    def mask_customer_name(self, value: Optional[str]) -> Optional[str]:
        return mask_name(value)

    @field_serializer("customer_email")
    def mask_customer_email(self, value: Optional[str]) -> Optional[str]:
        return mask_email(value)

    @field_serializer("customer_phone")
    def mask_customer_phone(self, value: Optional[str]) -> Optional[str]:
        return mask_phone(value)


class RevenueSummary(BaseModel):
    period_days: int
    total_revenue: float
    total_orders: int
    avg_order_value: float
    paid_orders: int
    pending_orders: int
    refunded_amount: float
    revenue_by_channel: Dict[str, float]
    revenue_by_platform: Dict[str, float]
    orders_by_status: Dict[str, int]
    revenue_trend: List[Dict[str, Any]]


class AttributionSummary(BaseModel):
    total_revenue: float
    total_orders: int
    # By channel
    by_channel: List[Dict[str, Any]]
    # By workflow
    by_workflow: List[Dict[str, Any]]
    # By agent
    by_agent: List[Dict[str, Any]]
    # First touch vs last touch
    first_touch_revenue: Dict[str, float]
    last_touch_revenue: Dict[str, float]
