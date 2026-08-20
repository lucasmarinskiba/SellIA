"""Fraud detection models — order + account fraud scoring."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Decimal, Enum as SQLEnum, Index, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class FraudRiskLevel(str, Enum):
    """Fraud risk assessment."""
    LOW = "low"  # 0-15% risk
    MEDIUM = "medium"  # 16-50% risk
    HIGH = "high"  # 51-80% risk
    CRITICAL = "critical"  # 81-100% risk


class FraudReason(str, Enum):
    """Primary fraud indicator."""
    VELOCITY_ABUSE = "velocity_abuse"  # Too many orders in short time
    IMPOSSIBLE_LOCATION = "impossible_location"  # Travel distance impossible
    NEW_ACCOUNT = "new_account"  # Brand new account
    CARD_MISMATCH = "card_mismatch"  # Billing != shipping address
    UNUSUAL_DEVICE = "unusual_device"  # New device/IP
    HIGH_VALUE_FIRST = "high_value_first"  # Large first order
    CHARGEBACK_HISTORY = "chargeback_history"  # Previous chargebacks
    BLACKLIST_HIT = "blacklist_hit"  # Email/IP/card on blacklist
    NEGATIVE_AVS = "negative_avs"  # Address verification failed
    HIGH_RISK_COUNTRY = "high_risk_country"  # High-fraud country
    NONE = "none"  # No fraud indicators


class OrderFraudScore(Base):
    """Per-order fraud risk assessment."""
    __tablename__ = "order_fraud_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(255), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)

    # Risk assessment
    fraud_risk_score = Column(Decimal(5, 2), default=0)  # 0-100
    fraud_risk_level = Column(SQLEnum(FraudRiskLevel), default=FraudRiskLevel.LOW)
    primary_fraud_reason = Column(SQLEnum(FraudReason), default=FraudReason.NONE)

    # Signal weights
    velocity_score = Column(Decimal(5, 2), default=0)  # Orders in last 24h
    location_score = Column(Decimal(5, 2), default=0)  # Impossible distance
    new_account_score = Column(Decimal(5, 2), default=0)  # Days since signup
    address_mismatch_score = Column(Decimal(5, 2), default=0)  # Billing != shipping
    device_risk_score = Column(Decimal(5, 2), default=0)  # New IP/device
    amount_risk_score = Column(Decimal(5, 2), default=0)  # Order value vs history
    chargeback_history_score = Column(Decimal(5, 2), default=0)  # Past chargebacks
    blacklist_match_score = Column(Decimal(5, 2), default=0)  # Blacklist hit

    # Customer context
    customer_order_count = Column(Integer, default=0)
    customer_fraud_history = Column(Integer, default=0)  # Past fraud cases
    avg_order_value = Column(Decimal(10, 2), nullable=True)
    order_value_deviation = Column(Decimal(5, 2), nullable=True)  # Std devs from avg

    # Actions taken
    manual_review_requested = Column(Boolean, default=False)
    order_blocked = Column(Boolean, default=False)
    reason_for_action = Column(String(255), nullable=True)

    # Resolution
    is_confirmed_fraud = Column(Boolean, default=False)
    is_confirmed_legitimate = Column(Boolean, default=False)
    dispute_reported = Column(Boolean, default=False)
    resolution_date = Column(DateTime(timezone.utc), nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer", foreign_keys=[customer_id])

    __table_args__ = (
        Index("idx_business_level", "business_id", "fraud_risk_level"),
        Index("idx_unresolved", "business_id", "is_confirmed_fraud", "is_confirmed_legitimate"),
    )


class AccountFraudScore(Base):
    """Per-customer account fraud risk."""
    __tablename__ = "account_fraud_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Risk assessment
    account_fraud_score = Column(Decimal(5, 2), default=0)  # 0-100
    account_risk_level = Column(SQLEnum(FraudRiskLevel), default=FraudRiskLevel.LOW)

    # Account signals
    days_since_signup = Column(Integer, default=0)
    profile_completeness = Column(Decimal(3, 1), default=0)  # 0-10 (filled fields)
    email_verified = Column(Boolean, default=False)
    phone_verified = Column(Boolean, default=False)

    # Behavioral signals
    failed_login_attempts = Column(Integer, default=0)
    password_changes = Column(Integer, default=0)  # Suspicious if frequent
    address_changes = Column(Integer, default=0)
    payment_method_changes = Column(Integer, default=0)

    # History
    total_orders = Column(Integer, default=0)
    lifetime_spend = Column(Decimal(12, 2), default=0)
    chargeback_count = Column(Integer, default=0)
    fraud_dispute_count = Column(Integer, default=0)
    account_suspension_count = Column(Integer, default=0)

    # Status
    is_flagged = Column(Boolean, default=False)
    account_suspended = Column(Boolean, default=False)
    suspension_reason = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), index=True)

    customer = relationship("Customer", foreign_keys=[customer_id])

    __table_args__ = (
        Index("idx_business_risk_level", "business_id", "account_risk_level"),
        Index("idx_flagged", "business_id", "is_flagged"),
    )


class FraudBlacklist(Base):
    """Blacklisted entities (email, IP, card, phone)."""
    __tablename__ = "fraud_blacklist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Entity
    entity_type = Column(String(20), nullable=False)  # email, ip, card_token, phone
    entity_value = Column(String(255), nullable=False)  # Hashed for cards
    entity_hash = Column(String(64), nullable=False, index=True)  # For dedup

    # Reason
    fraud_reason = Column(String(255), nullable=True)
    fraud_count = Column(Integer, default=1)

    # Status
    is_active = Column(Boolean, default=True)
    listed_date = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone.utc), nullable=True)  # Temporary blacklists

    notes = Column(String(500), nullable=True)

    __table_args__ = (
        Index("idx_business_type_value", "business_id", "entity_type", "entity_hash"),
        Index("idx_active", "business_id", "is_active"),
    )


class FraudMetrics(Base):
    """Aggregate fraud detection metrics."""
    __tablename__ = "fraud_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Date
    date = Column(String(10), nullable=False)  # YYYY-MM-DD

    # Order fraud
    total_orders_reviewed = Column(Integer, default=0)
    orders_flagged_high_risk = Column(Integer, default=0)
    orders_blocked = Column(Integer, default=0)
    confirmed_fraud_orders = Column(Integer, default=0)
    fraud_order_rate = Column(Decimal(5, 2), default=0)  # % of orders

    # Revenue impact
    fraud_revenue_lost = Column(Decimal(12, 2), default=0)  # Chargebacks + stolen value
    blocked_revenue = Column(Decimal(12, 2), default=0)  # Legitimate orders blocked
    chargeback_count = Column(Integer, default=0)
    chargeback_amount = Column(Decimal(12, 2), default=0)

    # Account fraud
    accounts_flagged = Column(Integer, default=0)
    accounts_suspended = Column(Integer, default=0)
    fake_accounts_detected = Column(Integer, default=0)

    # Blacklist
    total_blacklisted = Column(Integer, default=0)
    blacklist_match_rate = Column(Decimal(5, 2), default=0)  # % of flagged orders match

    # Manual review
    manual_reviews_pending = Column(Integer, default=0)
    manual_review_resolution_rate = Column(Decimal(5, 2), default=0)  # % resolved

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", foreign_keys=[business_id])

    __table_args__ = (
        Index("idx_business_date", "business_id", "date"),
    )
