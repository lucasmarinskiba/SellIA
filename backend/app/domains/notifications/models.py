"""Notification Delivery Models."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class NotificationChannel(str):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    PUSH = "push"
    IN_APP = "in_app"


class NotificationPriority(str):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class NotificationStatus(str):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class NotificationDelivery(Base):
    """Track every notification sent to owners/agents."""
    __tablename__ = "notification_deliveries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    channel = Column(String(20), nullable=False, index=True)
    priority = Column(String(20), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False)  # handoff, briefing, deal_closed, alert, etc.

    subject = Column(String(255), nullable=True)
    message = Column(Text, nullable=False)
    message_short = Column(String(500), nullable=True)  # For WhatsApp/SMS

    status = Column(String(20), default="pending", nullable=False, index=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)

    context_data = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_notifications_user_status", "user_id", "status"),
        Index("ix_notifications_business_type", "business_id", "notification_type"),
    )
