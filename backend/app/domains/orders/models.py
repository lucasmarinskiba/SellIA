"""Orders & Revenue Models

Tracks sales orders, payments, and revenue attribution.
"""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.core.encrypted_types import EncryptedString
import enum


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Order(Base):
    """A sales order."""
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    deal_id = Column(UUID(as_uuid=True), ForeignKey("deals.id", ondelete="SET NULL"), nullable=True, index=True)

    # Order details
    order_number = Column(String(50), nullable=True, unique=True, index=True)
    items = Column(JSONB, default=list, nullable=False)  # [{"name": "...", "qty": 1, "price": 100, "sku": "..."}]
    total_amount = Column(Numeric(14, 2), nullable=False)
    subtotal = Column(Numeric(14, 2), nullable=True)
    tax_amount = Column(Numeric(14, 2), nullable=True)
    discount_amount = Column(Numeric(14, 2), nullable=True)
    shipping_cost = Column(Numeric(14, 2), nullable=True)
    currency = Column(String(3), default="ARS", nullable=False)

    # Status
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False, index=True)

    # Payment
    payment_method = Column(String(50), nullable=True)  # mercadopago, stripe, cash, transfer
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
    payment_reference = Column(String(255), nullable=True)  # external payment ID
    payment_gateway = Column(String(50), nullable=True)  # mercadopago, stripe, paypal

    # Shipping
    shipping_address = Column(JSONB, default=dict, nullable=False)
    shipping_provider = Column(String(50), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    shipped_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)

    # Revenue Attribution (CRITICAL)
    source_channel = Column(String(50), nullable=True, index=True)
    source_campaign = Column(String(200), nullable=True)
    source_workflow_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    source_agent_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    first_touch_channel = Column(String(50), nullable=True)
    last_touch_channel = Column(String(50), nullable=True)
    attribution_model = Column(String(20), default="last_touch", nullable=False)  # first_touch, last_touch, linear

    # Customer info
    customer_name = Column(EncryptedString, nullable=True)  # encrypted at rest
    customer_email = Column(EncryptedString, nullable=True)  # encrypted at rest
    customer_phone = Column(EncryptedString, nullable=True)  # encrypted at rest

    # External platform
    external_id = Column(String(100), nullable=True)  # MercadoLibre order ID, Shopify order ID
    external_platform = Column(String(50), nullable=True)  # mercadolibre, shopify, hotmart, manual

    # Notes
    notes = Column(Text, nullable=True)
    extra_data = Column(JSONB, default=dict, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class RevenueEvent(Base):
    """Every revenue event with full attribution."""
    __tablename__ = "revenue_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String(50), nullable=False, index=True)  # order_created, payment_received, refund_issued
    amount = Column(Numeric(14, 2), nullable=False)
    currency = Column(String(3), default="ARS", nullable=False)

    # Attribution
    source_channel = Column(String(50), nullable=True, index=True)
    source_workflow_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    source_agent_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    source_campaign = Column(String(200), nullable=True)

    # Touchpoint data
    touchpoint_data = Column(JSONB, default=dict, nullable=False)  # {"first_touch": {...}, "last_touch": {...}, "interactions": [...]}

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class PaymentIntegration(Base):
    """Configuration for payment gateways."""
    __tablename__ = "payment_integrations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    provider = Column(String(50), nullable=False)  # mercadopago, stripe, paypal
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)

    # Encrypted credentials
    credentials_encrypted = Column(Text, nullable=True)
    settings = Column(JSONB, default=dict, nullable=False)  # {"webhook_url": "...", "sandbox": false}

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
