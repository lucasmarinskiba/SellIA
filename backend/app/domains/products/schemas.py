from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

# ============================================================
# PRODUCT SCHEMAS
# ============================================================

class ProductVariantAttrCreate(BaseModel):
    name: str
    sku: str | None = None
    price: Decimal | None = None
    inventory_count: int = 0
    attributes: dict[str, Any] = Field(default_factory=dict)


class ProductVariantResponse(BaseModel):
    id: UUID
    name: str
    sku: str | None
    price: Decimal | None
    inventory_count: int
    attributes: dict[str, Any]
    is_available: bool

    class Config:
        from_attributes = True


class ProductCreateRequest(BaseModel):
    name: str
    slug: str | None = None
    description: str | None = None
    short_description: str | None = None
    price: Decimal
    compare_at_price: Decimal | None = None
    sku: str | None = None
    barcode: str | None = None
    weight: Decimal | None = None
    inventory_count: int = 0
    track_inventory: bool = True
    featured_image_url: str | None = None
    images: list[str] = Field(default_factory=list)
    status: str = 'DRAFT'
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProductUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    short_description: str | None = None
    price: Decimal | None = None
    compare_at_price: Decimal | None = None
    inventory_count: int | None = None
    featured_image_url: str | None = None
    images: list[str] | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


class ProductResponse(BaseModel):
    id: UUID
    website_id: UUID
    name: str
    slug: str
    description: str | None
    short_description: str | None
    price: Decimal
    compare_at_price: Decimal | None
    sku: str | None
    inventory_count: int
    featured_image_url: str | None
    images: list[str]
    status: str
    variants: list[ProductVariantResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# CART SCHEMAS
# ============================================================

class CartItemRequest(BaseModel):
    product_id: UUID
    variant_id: UUID | None = None
    quantity: int = 1


class CartItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: str | None
    variant_id: UUID | None
    variant_name: str | None
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    class Config:
        from_attributes = True


class ShoppingCartResponse(BaseModel):
    id: UUID
    website_id: UUID
    status: str
    items: list[CartItemResponse] = Field(default_factory=list)
    subtotal: Decimal
    tax: Decimal
    shipping: Decimal
    discount: Decimal
    total: Decimal
    coupon_code: str | None
    customer_email: str | None
    customer_phone: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CartCheckoutRequest(BaseModel):
    customer_email: str
    customer_phone: str | None = None
    shipping_address: dict[str, Any]
    billing_address: dict[str, Any] | None = None
    coupon_code: str | None = None
    notes: str | None = None


# ============================================================
# ORDER SCHEMAS
# ============================================================

class OrderItemResponse(BaseModel):
    id: UUID
    product_name: str
    variant_name: str | None
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: UUID
    order_number: str
    status: str
    payment_status: str
    subtotal: Decimal
    tax: Decimal
    shipping_cost: Decimal
    discount: Decimal
    total: Decimal
    customer_email: str
    customer_phone: str | None
    items: list[OrderItemResponse] = Field(default_factory=list)
    payment_method: str | None
    created_at: datetime
    updated_at: datetime
    paid_at: datetime | None
    shipped_at: datetime | None

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    orders: list[OrderResponse]
    total: int
    page: int
    per_page: int


# ============================================================
# CATEGORY SCHEMAS
# ============================================================

class ProductCategoryCreateRequest(BaseModel):
    name: str
    slug: str
    description: str | None = None
    image_url: str | None = None
    parent_id: UUID | None = None
    display_order: int = 0


class ProductCategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: str | None
    image_url: str | None
    display_order: int

    class Config:
        from_attributes = True
