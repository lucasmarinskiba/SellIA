"""Invoicing domain models."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Numeric, String, Text, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Invoice(Base):
    """Invoice record.

    Table is named `customer_invoices`, not `invoices` — the shared Base
    already has two other domains claiming that name (app.core.database
    .payment_models.Invoice and app.domains.subscriptions.models.Invoice),
    both with real Alembic migrations and production data. Whichever module
    imports first wins the name and the other two are silently dropped by
    main.py's _try_include (see its warning log). This domain has no
    migration/prod data yet, so it took the rename rather than risk a
    collision with either legacy table.
    """
    __tablename__ = "customer_invoices"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    customer_id: Mapped[UUID | None] = mapped_column(ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    invoice_number: Mapped[str] = mapped_column(String(50), unique=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, sent, viewed, paid, overdue, cancelled
    amount_aed: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    tax_aed: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=0)
    total_aed: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    due_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    viewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_method: Mapped[str | None] = mapped_column(String(50), nullable=True)  # bank_transfer, card, cash, etc.
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    items: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InvoiceTemplate(Base):
    """Invoice template for businesses."""
    __tablename__ = "invoice_templates"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    template_html: Mapped[str] = mapped_column(Text)
    is_default: Mapped[bool] = mapped_column(default=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Payment(Base):
    """Payment record for invoices.

    Table is named `customer_invoice_payments`, not `payments` — that name
    collides with app.core.database.payment_models.Payment. See Invoice's
    docstring above for the same rationale.
    """
    __tablename__ = "customer_invoice_payments"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    invoice_id: Mapped[UUID] = mapped_column(ForeignKey("customer_invoices.id", ondelete="CASCADE"))
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    amount_aed: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    method: Mapped[str] = mapped_column(String(50))  # bank_transfer, card, cash, etc.
    reference: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, completed, failed
    paid_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


INVOICING_TABLES = [Invoice.__table__, InvoiceTemplate.__table__, Payment.__table__]
