"""Orders Schemas"""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_serializer,
    model_validator,
)

from app.core.pii_masking import mask_email, mask_name, mask_phone
from app.domains.orders.models import OrderStatus as OrderStatusEnum
from app.domains.orders.models import PaymentStatus as PaymentStatusEnum


class OrderItem(BaseModel):
    """A line of an order, in either of the two shapes really stored.

    The webhook processors (Shopify, MercadoLibre, Hotmart, Woo, Etsy) write
    {"name", "qty", "price", "sku"}; the manual create path writes
    {"quantity", "unit_price", "total_price"}. This model required the second
    shape only, so a single imported order made GET /orders fail validation and
    return 500 for the whole list. Accept both and normalise.
    """

    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: str = ""
    sku: str | None = None
    quantity: int = Field(default=1, validation_alias=AliasChoices("quantity", "qty"))
    unit_price: float = Field(
        default=0.0, validation_alias=AliasChoices("unit_price", "price")
    )
    total_price: float | None = None

    @model_validator(mode="after")
    def fill_total(self) -> "OrderItem":
        if self.total_price is None:
            self.total_price = round(self.unit_price * self.quantity, 2)
        return self


class OrderBase(BaseModel):
    order_number: str | None = None
    items: list[OrderItem] = Field(default_factory=list)
    total_amount: float
    subtotal: float | None = None
    tax_amount: float | None = None
    discount_amount: float | None = None
    shipping_cost: float | None = None
    currency: str = "ARS"
    # Typed against the real enums: as plain strings, any typo reached Postgres
    # and came back as a raw 500 ("invalid input value for enum orderstatus"),
    # instead of the 422 a client can actually act on.
    status: OrderStatusEnum = OrderStatusEnum.PENDING
    payment_method: str | None = None
    payment_status: PaymentStatusEnum = PaymentStatusEnum.PENDING
    shipping_address: dict[str, Any] = Field(default_factory=dict)
    shipping_provider: str | None = None
    tracking_number: str | None = None
    notes: str | None = None
    customer_name: str | None = None
    customer_email: str | None = None
    customer_phone: str | None = None
    external_id: str | None = None
    external_platform: str | None = None
    extra_data: dict[str, Any] = Field(default_factory=dict)


class OrderCreate(OrderBase):
    business_id: UUID
    conversation_id: UUID | None = None
    deal_id: UUID | None = None


class OrderUpdate(BaseModel):
    status: str | None = None
    payment_status: str | None = None
    paid_at: datetime | None = None
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None
    tracking_number: str | None = None
    shipping_provider: str | None = None
    notes: str | None = None
    extra_data: dict[str, Any] | None = None
    is_active: bool | None = None


class OrderResponse(OrderBase):
    id: UUID
    business_id: UUID
    conversation_id: UUID | None = None
    deal_id: UUID | None = None
    source_channel: str | None = None
    source_campaign: str | None = None
    source_workflow_id: UUID | None = None
    source_agent_id: UUID | None = None
    first_touch_channel: str | None = None
    last_touch_channel: str | None = None
    attribution_model: str
    paid_at: datetime | None = None
    shipped_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_serializer("customer_name")
    def mask_customer_name(self, value: str | None) -> str | None:
        return mask_name(value)

    @field_serializer("customer_email")
    def mask_customer_email(self, value: str | None) -> str | None:
        return mask_email(value)

    @field_serializer("customer_phone")
    def mask_customer_phone(self, value: str | None) -> str | None:
        return mask_phone(value)


class RevenueSummary(BaseModel):
    period_days: int
    total_revenue: float
    total_orders: int
    avg_order_value: float
    paid_orders: int
    pending_orders: int
    refunded_amount: float
    revenue_by_channel: dict[str, float]
    revenue_by_platform: dict[str, float]
    orders_by_status: dict[str, int]
    revenue_trend: list[dict[str, Any]]


class AttributionSummary(BaseModel):
    total_revenue: float
    total_orders: int
    # By channel
    by_channel: list[dict[str, Any]]
    # By workflow
    by_workflow: list[dict[str, Any]]
    # By agent
    by_agent: list[dict[str, Any]]
    # First touch vs last touch
    first_touch_revenue: dict[str, float]
    last_touch_revenue: dict[str, float]
