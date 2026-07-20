"""Finance Models — Sales Invoices, Payment Reminders, AR Snapshots, Tax Config."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Numeric, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base
from app.core.encrypted_types import EncryptedString


class SalesInvoice(Base):
    __tablename__ = "sales_invoices"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)

    invoice_number = Column(String(100), nullable=False, unique=True, index=True)
    status = Column(String(50), default="draft", nullable=False)  # draft, sent, paid, overdue, cancelled
    amount = Column(Numeric(14, 2), nullable=False)
    tax_amount = Column(Numeric(14, 2), default=0, nullable=False)
    total_amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), default="ARS", nullable=False)

    due_date = Column(DateTime(timezone=True), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    paid_amount = Column(Numeric(14, 2), default=0, nullable=False)

    customer_name = Column(EncryptedString, nullable=True)  # encrypted at rest
    customer_email = Column(EncryptedString, nullable=True)  # encrypted at rest
    customer_phone = Column(EncryptedString, nullable=True)  # encrypted at rest

    items = Column(JSONB, default=list, nullable=False)
    extra_data = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_sales_invoices_business_status", "business_id", "status"),
    )


class PaymentReminder(Base):
    __tablename__ = "payment_reminders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    invoice_id = Column(UUID(as_uuid=True), ForeignKey("sales_invoices.id", ondelete="SET NULL"), nullable=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)

    reminder_level = Column(Integer, default=1, nullable=False)  # 1=gentle, 2=firm, 3=final_notice
    status = Column(String(50), default="pending", nullable=False)  # pending, sent, responded, escalated
    scheduled_at = Column(DateTime(timezone=True), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    message_content = Column(Text, nullable=True)

    channel_platform = Column(String(50), default="whatsapp", nullable=False)
    response_received = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_payment_reminders_business_status", "business_id", "status"),
    )


class AccountsReceivableSnapshot(Base):
    __tablename__ = "accounts_receivable_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    snapshot_date = Column(DateTime(timezone=True), nullable=False)
    total_outstanding = Column(Numeric(14, 2), default=0, nullable=False)
    total_overdue = Column(Numeric(14, 2), default=0, nullable=False)
    invoice_count = Column(Integer, default=0, nullable=False)
    overdue_count = Column(Integer, default=0, nullable=False)

    customer_breakdown = Column(JSONB, default=list, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_ar_snapshots_business_date", "business_id", "snapshot_date"),
    )


class TaxConfig(Base):
    __tablename__ = "tax_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    country_code = Column(String(2), default="AR", nullable=False)
    tax_name = Column(String(100), default="IVA", nullable=False)
    tax_rate = Column(Numeric(5, 2), default=21.0, nullable=False)
    tax_id_number = Column(EncryptedString, nullable=True)  # encrypted at rest
    is_tax_exempt = Column(Boolean, default=False, nullable=False)

    extra_data = Column(JSONB, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class FinanceAutopilotConfig(Base):
    __tablename__ = "finance_autopilot_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    is_active = Column(Boolean, default=False, nullable=False)
    is_paused = Column(Boolean, default=False, nullable=False)
    paused_reason = Column(Text, nullable=True)

    auto_deliver_invoices = Column(Boolean, default=True, nullable=False)
    auto_run_dunning = Column(Boolean, default=True, nullable=False)
    auto_reconcile_payments = Column(Boolean, default=True, nullable=False)
    auto_generate_tax_reports = Column(Boolean, default=False, nullable=False)

    dunning_channel = Column(String(50), default="whatsapp", nullable=False)
    max_dunning_level = Column(Integer, default=4, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
