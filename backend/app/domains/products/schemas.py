from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID
from decimal import Decimal

# ============================================================
# PRODUCT SCHEMAS
# ============================================================

class ProductVariantAttrCreate(BaseModel):
    name: str
    sku: Optional[str] = None
    price: Optional[Decimal] = None
    inventory_count: int = 0
    attributes: Dict[str, Any] = Field(default_factory=dict)


class ProductVariantResponse(BaseModel):
    id: UUID
    name: str
    sku: Optional[str]
    price: Optional[Decimal]
    inventory_count: int
    attributes: Dict[str, Any]
    is_available: bool

    class Config:
        from_attributes = True


class ProductCreateRequest(BaseModel):
    name: str
    slug: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: Decimal
    compare_at_price: Optional[Decimal] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    weight: Optional[Decimal] = None
    inventory_count: int = 0
    track_inventory: bool = True
    featured_image_url: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    status: str = 'DRAFT'
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ProductUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    short_description: Optional[str] = None
    price: Optional[Decimal] = None
    compare_at_price: Optional[Decimal] = None
    inventory_count: Optional[int] = None
    featured_image_url: Optional[str] = None
    images: Optional[List[str]] = None
    status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ProductResponse(BaseModel):
    id: UUID
    website_id: UUID
    name: str
    slug: str
    description: Optional[str]
    short_description: Optional[str]
    price: Decimal
    compare_at_price: Optional[Decimal]
    sku: Optional[str]
    inventory_count: int
    featured_image_url: Optional[str]
    images: List[str]
    status: str
    variants: List[ProductVariantResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============================================================
# CART SCHEMAS
# ============================================================

class CartItemRequest(BaseModel):
    product_id: UUID
    variant_id: Optional[UUID] = None
    quantity: int = 1


class CartItemResponse(BaseModel):
    id: UUID
    product_id: UUID
    product_name: Optional[str]
    variant_id: Optional[UUID]
    variant_name: Optional[str]
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    class Config:
        from_attributes = True


class ShoppingCartResponse(BaseModel):
    id: UUID
    website_id: UUID
    status: str
    items: List[CartItemResponse] = Field(default_factory=list)
    subtotal: Decimal
    tax: Decimal
    shipping: Decimal
    discount: Decimal
    total: Decimal
    coupon_code: Optional[str]
    customer_email: Optional[str]
    customer_phone: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CartCheckoutRequest(BaseModel):
    customer_email: str
    customer_phone: Optional[str] = None
    shipping_address: Dict[str, Any]
    billing_address: Optional[Dict[str, Any]] = None
    coupon_code: Optional[str] = None
    notes: Optional[str] = None


# ============================================================
# ORDER SCHEMAS
# ============================================================

class OrderItemResponse(BaseModel):
    id: UUID
    product_name: str
    variant_name: Optional[str]
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
    customer_phone: Optional[str]
    items: List[OrderItemResponse] = Field(default_factory=list)
    payment_method: Optional[str]
    created_at: datetime
    updated_at: datetime
    paid_at: Optional[datetime]
    shipped_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    per_page: int


# ============================================================
# CATEGORY SCHEMAS
# ============================================================

class ProductCategoryCreateRequest(BaseModel):
    name: str
    slug: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_id: Optional[UUID] = None
    display_order: int = 0


class ProductCategoryResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    description: Optional[str]
    image_url: Optional[str]
    display_order: int

    class Config:
        from_attributes = True
