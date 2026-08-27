"""Procurement domain schemas."""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class VendorCreate(BaseModel):
    """Create vendor."""
    name: str = Field(..., min_length=1, max_length=255)
    category: str = Field(..., min_length=1, max_length=100)
    contact_email: str = Field(..., min_length=1, max_length=255)
    contact_phone: str | None = Field(None, max_length=20)


class VendorScoreUpdate(BaseModel):
    """Update vendor scores."""
    quality_score: Decimal = Field(..., ge=0, le=100)
    cost_score: Decimal = Field(..., ge=0, le=100)
    delivery_score: Decimal = Field(..., ge=0, le=100)


class VendorOut(BaseModel):
    """Vendor response."""
    id: UUID
    business_id: UUID
    name: str
    category: str
    contact_email: str
    contact_phone: str | None
    quality_score: Decimal
    cost_score: Decimal
    delivery_score: Decimal
    overall_score: Decimal
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class RFQCreate(BaseModel):
    """Create RFQ."""
    vendor_id: UUID | None = None
    description: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    unit: str = Field(..., min_length=1, max_length=20)
    expected_delivery_date: date


class RFQAccept(BaseModel):
    """Accept RFQ response."""
    quote_amount_aed: Decimal = Field(..., ge=0)


class RFQOut(BaseModel):
    """RFQ response."""
    id: UUID
    business_id: UUID
    rfq_number: str
    vendor_id: UUID | None
    description: str
    quantity: int
    unit: str
    expected_delivery_date: date
    status: str
    quote_amount_aed: Decimal | None
    sent_at: datetime
    response_received_at: datetime | None

    class Config:
        from_attributes = True


class PurchaseOrderCreate(BaseModel):
    """Create purchase order."""
    vendor_id: UUID
    rfq_id: UUID | None = None
    description: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    unit_price_aed: Decimal = Field(..., ge=0)
    expected_delivery_date: date


class PurchaseOrderUpdate(BaseModel):
    """Update PO status."""
    status: str = Field(..., pattern="^(issued|received|invoiced|paid)$")
    actual_delivery_date: date | None = None
    invoice_number: str | None = Field(None, max_length=50)
    invoice_amount_aed: Decimal | None = Field(None, ge=0)


class PurchaseOrderOut(BaseModel):
    """PO response."""
    id: UUID
    business_id: UUID
    po_number: str
    vendor_id: UUID | None
    rfq_id: UUID | None
    description: str
    quantity: int
    unit_price_aed: Decimal
    total_amount_aed: Decimal
    status: str
    expected_delivery_date: date
    actual_delivery_date: date | None
    invoice_number: str | None
    invoice_amount_aed: Decimal | None
    paid_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True
