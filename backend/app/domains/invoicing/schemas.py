"""Invoicing domain schemas."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class InvoiceItemIn(BaseModel):
    """Invoice line item."""
    description: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    unit_price_aed: Decimal = Field(..., ge=0)


class InvoiceCreate(BaseModel):
    """Create invoice."""
    customer_id: UUID | None = None
    amount_aed: Decimal = Field(..., ge=0)
    tax_aed: Decimal = Field(default=0, ge=0)
    due_date: datetime
    items: list[InvoiceItemIn] = Field(default_factory=list)
    notes: str | None = None


class InvoiceUpdate(BaseModel):
    """Update invoice."""
    status: str | None = Field(None, pattern="^(draft|sent|viewed|paid|overdue|cancelled)$")
    due_date: datetime | None = None
    notes: str | None = None


class InvoiceSend(BaseModel):
    """Send invoice."""
    email: str = Field(..., min_length=1)


class InvoiceOut(BaseModel):
    """Invoice response."""
    id: UUID
    business_id: UUID
    customer_id: UUID | None
    invoice_number: str
    status: str
    amount_aed: Decimal
    tax_aed: Decimal
    total_aed: Decimal
    due_date: datetime
    sent_at: datetime | None
    viewed_at: datetime | None
    paid_at: datetime | None
    payment_method: str | None
    notes: str | None
    items: dict | None
    created_at: datetime

    class Config:
        from_attributes = True


class PaymentCreate(BaseModel):
    """Record payment."""
    amount_aed: Decimal = Field(..., ge=0)
    method: str = Field(..., min_length=1)
    reference: str | None = None


class PaymentOut(BaseModel):
    """Payment response."""
    id: UUID
    invoice_id: UUID
    business_id: UUID
    amount_aed: Decimal
    method: str
    reference: str | None
    status: str
    paid_at: datetime

    class Config:
        from_attributes = True


class InvoiceTemplateCreate(BaseModel):
    """Create invoice template."""
    name: str = Field(..., min_length=1, max_length=255)
    template_html: str = Field(..., min_length=1)
    is_default: bool = False


class InvoiceTemplateOut(BaseModel):
    """Invoice template response."""
    id: UUID
    business_id: UUID
    name: str
    template_html: str
    is_default: bool
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class InvoiceStatsResponse(BaseModel):
    """Invoice statistics."""
    total_invoices: int
    total_revenue_aed: float
    paid_revenue_aed: float
    pending_revenue_aed: float
    overdue_count: int
    avg_payment_days: float
