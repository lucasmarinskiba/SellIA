"""Proactive Outreach Engine Models

OutreachOpportunity and OutreachRule for autonomous customer outreach.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Numeric, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class OutreachOpportunity(Base):
    """A detected outreach opportunity for a customer."""

    __tablename__ = "outreach_opportunities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    opportunity_type = Column(
        String(50),
        nullable=False,
        index=True,
    )  # 'cart_abandonment', 're_engagement', 'product_recommendation', 'anniversary', 'birthday', 'price_drop', 'back_in_stock', 'churn_risk'
    priority = Column(
        String(20),
        nullable=False,
        default="medium",
    )  # 'low', 'medium', 'high', 'urgent'
    trigger_data = Column(JSONB, default=dict, nullable=False)
    suggested_message = Column(Text, nullable=True)
    suggested_channel = Column(String(20), nullable=False, default="whatsapp")  # 'whatsapp', 'email', 'sms', 'dm'
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )  # 'pending', 'sent', 'converted', 'ignored', 'dismissed'
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    outcome = Column(String(50), nullable=True)
    revenue_generated = Column(Numeric(14, 2), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_outreach_opportunities_business_status", "business_id", "status"),
        Index("ix_outreach_opportunities_business_type", "business_id", "opportunity_type"),
    )


class OutreachRule(Base):
    """Configurable rule for generating outreach opportunities."""

    __tablename__ = "outreach_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    rule_name = Column(String(100), nullable=False)
    rule_type = Column(
        String(50),
        nullable=False,
        index=True,
    )  # same types as opportunity
    conditions = Column(JSONB, default=dict, nullable=False)  # e.g., {"cart_abandoned_hours": 24, "min_cart_value": 50}
    message_template = Column(Text, nullable=False)
    channel = Column(String(20), nullable=False, default="whatsapp")  # 'whatsapp', 'email', 'sms', 'dm'
    is_active = Column(Boolean, default=True, nullable=False)

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        Index("ix_outreach_rules_business_active", "business_id", "is_active"),
    )
