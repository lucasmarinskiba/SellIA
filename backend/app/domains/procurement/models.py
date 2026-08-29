"""Procurement models."""

import uuid
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Vendor(Base):
    """Supplier vendor with scoring."""
    __tablename__ = "vendors"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    category: Mapped[str] = mapped_column(String(100))  # office_supplies, it_hardware, etc.
    contact_email: Mapped[str] = mapped_column(String(255))
    contact_phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    quality_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)  # 0–100
    cost_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    delivery_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)
    overall_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)  # weighted average
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RFQ(Base):
    """Request for Quotation."""
    __tablename__ = "rfqs"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    rfq_number: Mapped[str] = mapped_column(String(50), unique=True)
    vendor_id: Mapped[UUID] = mapped_column(ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    quantity: Mapped[int] = mapped_column()
    unit: Mapped[str] = mapped_column(String(20))  # pieces, boxes, hours, etc.
    expected_delivery_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="sent")  # sent, received, accepted, rejected
    quote_amount_aed: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    response_received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PurchaseOrder(Base):
    """Purchase Order (PO) tracking."""
    __tablename__ = "purchase_orders"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    po_number: Mapped[str] = mapped_column(String(50), unique=True)
    vendor_id: Mapped[UUID] = mapped_column(ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    rfq_id: Mapped[UUID | None] = mapped_column(ForeignKey("rfqs.id", ondelete="SET NULL"), nullable=True)
    description: Mapped[str] = mapped_column(Text)
    quantity: Mapped[int] = mapped_column()
    unit_price_aed: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total_amount_aed: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    status: Mapped[str] = mapped_column(String(20), default="issued")  # issued, received, invoiced, paid
    expected_delivery_date: Mapped[date] = mapped_column(Date)
    actual_delivery_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    invoice_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    invoice_amount_aed: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


PROCUREMENT_TABLES = [Vendor.__table__, RFQ.__table__, PurchaseOrder.__table__]
