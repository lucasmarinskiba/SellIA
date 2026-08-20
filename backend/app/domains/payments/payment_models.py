"""Payment domain models."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Index, Boolean, Text, Numeric, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class PaymentMethod(str, Enum):
    """Payment methods."""
    MERCADOPAGO = "mercadopago"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    BANK_TRANSFER = "bank_transfer"
    CASH = "cash"
    INSTALLMENTS = "installments"


class TransactionStatus(str, Enum):
    """Transaction statuses."""
    PENDING = "pending"
    PROCESSING = "processing"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIAL_REFUND = "partial_refund"
    DISPUTED = "disputed"
    CHARGEBACK = "chargeback"


class RefundStatus(str, Enum):
    """Refund statuses."""
    REQUESTED = "requested"
    APPROVED = "approved"
    PROCESSING = "processing"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Transaction(Base):
    """Payment transaction."""
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Customer & Order
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    order_id = Column(UUID(as_uuid=True), nullable=True, index=True)  # FK to orders table
    location_id = Column(UUID(as_uuid=True), nullable=True)  # Which location (if multi-location)

    # Payment details
    amount = Column(Numeric(12, 2), nullable=False)  # Transaction amount
    currency = Column(String(3), default="USD")  # ISO 4217 code (USD, ARS, BRL, etc)
    method = Column(String(50), nullable=False)  # PaymentMethod value
    status = Column(String(20), default=TransactionStatus.PENDING)  # TransactionStatus value

    # MercadoPago integration
    mercadopago_payment_id = Column(String(255), nullable=True, unique=True, index=True)
    mercadopago_preference_id = Column(String(255), nullable=True)
    mercadopago_merchant_order_id = Column(String(255), nullable=True)
    mercadopago_status = Column(String(50), nullable=True)

    # Installments (cuotas)
    installments = Column(Integer, default=1)  # Number of installments
    installment_amount = Column(Numeric(12, 2), nullable=True)  # Amount per installment

    # Metadata
    description = Column(String(500), nullable=True)
    reference_id = Column(String(255), nullable=True, index=True)  # Internal reference
    transaction_metadata = Column(JSONB, nullable=True)  # Extra data (e.g., item breakdown, promo codes)

    # Fees & Settlement
    gateway_fee = Column(Numeric(12, 2), default=0)  # Fees charged by payment gateway
    net_amount = Column(Numeric(12, 2), nullable=True)  # Amount after fees
    settlement_date = Column(DateTime(timezone.utc), nullable=True)  # When settled
    settled = Column(Boolean, default=False)

    # Webhook tracking
    webhook_notification_received = Column(Boolean, default=False)
    webhook_notification_date = Column(DateTime(timezone.utc), nullable=True)

    # Timing
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    approved_at = Column(DateTime(timezone.utc), nullable=True)
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_status", "business_id", "status"),
        Index("idx_customer_status", "customer_id", "status"),
        Index("idx_mp_payment_id", "mercadopago_payment_id"),
        Index("idx_reference_id", "reference_id"),
    )


class Refund(Base):
    """Refund record."""
    __tablename__ = "refunds"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Refund details
    amount = Column(Numeric(12, 2), nullable=False)  # Refund amount (full or partial)
    status = Column(String(20), default=RefundStatus.REQUESTED)  # RefundStatus value
    reason = Column(String(500), nullable=True)  # Why refund?

    # MercadoPago refund
    mercadopago_refund_id = Column(String(255), nullable=True, unique=True)

    # Processing
    requested_by = Column(UUID(as_uuid=True), nullable=True)  # User who requested
    approved_by = Column(UUID(as_uuid=True), nullable=True)  # Admin who approved
    processed_at = Column(DateTime(timezone.utc), nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_transaction_id", "transaction_id"),
        Index("idx_business_refund", "business_id", "status"),
    )


class Settlement(Base):
    """Payment settlement (payout to bank account)."""
    __tablename__ = "settlements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    location_id = Column(UUID(as_uuid=True), nullable=True)  # If settling per location

    # Settlement period
    period_start = Column(DateTime(timezone.utc), nullable=False)
    period_end = Column(DateTime(timezone.utc), nullable=False)

    # Totals
    gross_amount = Column(Numeric(12, 2), nullable=False)  # Total transactions
    total_fees = Column(Numeric(12, 2), default=0)  # Total fees
    refunds_amount = Column(Numeric(12, 2), default=0)  # Total refunds
    net_amount = Column(Numeric(12, 2), nullable=False)  # Amount to pay out

    # Status
    status = Column(String(20), default="pending")  # pending, processing, completed, failed

    # Bank details
    bank_account_id = Column(UUID(as_uuid=True), nullable=True)
    payout_date = Column(DateTime(timezone.utc), nullable=True)
    payout_reference = Column(String(255), nullable=True)  # Bank transfer reference

    # Metadata
    transaction_count = Column(Integer, default=0)  # Number of transactions
    settlement_metadata = Column(JSONB, nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_settlement", "business_id", "status"),
        Index("idx_period", "period_start", "period_end"),
    )


class PaymentReconciliation(Base):
    """Reconciliation record (match orders ↔ payments)."""
    __tablename__ = "payment_reconciliations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Order & Transaction
    order_id = Column(UUID(as_uuid=True), nullable=True)
    transaction_id = Column(UUID(as_uuid=True), ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)

    # Reconciliation result
    status = Column(String(20), default="pending")  # pending, matched, mismatched, partial
    matched = Column(Boolean, default=False)
    match_confidence = Column(Integer, default=0)  # 0-100 confidence score

    # Amounts
    order_amount = Column(Numeric(12, 2), nullable=True)
    transaction_amount = Column(Numeric(12, 2), nullable=True)
    discrepancy = Column(Numeric(12, 2), nullable=True)  # Difference if mismatched

    # Reconciliation logic
    match_reason = Column(String(255), nullable=True)  # How matched (exact, fuzzy, manual)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    reconciled_at = Column(DateTime(timezone.utc), nullable=True)

    __table_args__ = (
        Index("idx_business_reconciliation", "business_id", "status"),
        Index("idx_order_id", "order_id"),
        Index("idx_transaction_id", "transaction_id"),
    )


class PaymentMetrics(Base):
    """Payment metrics for analytics."""
    __tablename__ = "payment_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Volume
    total_transactions = Column(Integer, default=0)
    total_revenue = Column(Numeric(15, 2), default=0)
    avg_transaction_value = Column(Numeric(12, 2), default=0)

    # Performance
    success_rate = Column(Integer, default=0)  # Percentage 0-100
    failed_transactions = Column(Integer, default=0)
    refund_rate = Column(Integer, default=0)  # Percentage of refunded

    # Payment methods breakdown
    method_breakdown = Column(JSONB, nullable=True)  # {mercadopago: 50000, cash: 30000}

    # Settlement
    total_settled = Column(Numeric(15, 2), default=0)
    pending_settlement = Column(Numeric(15, 2), default=0)
    total_fees = Column(Numeric(12, 2), default=0)

    # Last 7 days
    transactions_7d = Column(Integer, default=0)
    revenue_7d = Column(Numeric(15, 2), default=0)

    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_metrics", "business_id"),
    )
