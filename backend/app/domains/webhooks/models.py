"""
Webhooks System

Manage outbound webhook subscriptions and delivery tracking.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Boolean, DateTime, Integer, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class WebhookSubscription(Base):
    """A user's webhook subscription."""
    __tablename__ = "webhook_subscriptions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    events = Column(JSONB, default=list, nullable=False)
    secret = Column(String(255), nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class WebhookDelivery(Base):
    """Record of a webhook delivery attempt."""
    __tablename__ = "webhook_deliveries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subscription_id = Column(UUID(as_uuid=True), ForeignKey("webhook_subscriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(100), nullable=False)
    payload = Column(JSONB, default=dict, nullable=False)
    response_status = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    delivered_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    retry_count = Column(Integer, default=0, nullable=False)
    success = Column(Boolean, default=False, nullable=False)
