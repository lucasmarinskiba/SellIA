"""Webhook & event streaming models."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Index, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class EventType(str, Enum):
    """Event types for webhooks."""
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_PAID = "order.paid"
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_UPDATED = "customer.updated"
    JOURNEY_STAGE_CHANGED = "journey.stage_changed"
    FRAUD_DETECTED = "fraud.detected"
    CHURN_ALERT = "churn.alert"
    LOCATION_VISIT = "location.visit"
    FEEDBACK_SUBMITTED = "feedback.submitted"


class WebhookEndpoint(Base):
    """Webhook endpoint configuration."""
    __tablename__ = "webhook_endpoints"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Endpoint
    url = Column(String(500), nullable=False)
    description = Column(String(500), nullable=True)

    # Events
    subscribed_events = Column(JSONB, default=list)  # List of EventType values
    secret_key = Column(String(255), nullable=False)  # For HMAC signing

    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    last_verified_at = Column(DateTime(timezone.utc), nullable=True)

    # Performance
    success_count = Column(Integer, default=0)
    failure_count = Column(Integer, default=0)
    avg_response_time_ms = Column(Integer, default=0)
    last_fired_at = Column(DateTime(timezone.utc), nullable=True)

    # Retry config
    max_retries = Column(Integer, default=3)
    retry_delay_seconds = Column(Integer, default=60)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_active", "business_id", "is_active"),
    )


class WebhookEvent(Base):
    """Webhook event record."""
    __tablename__ = "webhook_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    endpoint_id = Column(UUID(as_uuid=True), ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False)

    # Event
    event_type = Column(String(50), nullable=False)
    event_data = Column(JSONB, nullable=False)  # Event payload

    # Delivery
    delivery_status = Column(String(20), default="pending")  # pending, sent, failed, delivered
    delivery_attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime(timezone.utc), nullable=True)
    response_status_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)

    # Signature
    signature_hmac = Column(String(255), nullable=False)  # HMAC-SHA256 signature

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc), index=True)

    endpoint = relationship("WebhookEndpoint", foreign_keys=[endpoint_id])

    __table_args__ = (
        Index("idx_business_status", "business_id", "delivery_status"),
        Index("idx_endpoint_date", "endpoint_id", "created_at"),
    )


class WebhookDeliveryLog(Base):
    """Webhook delivery attempt log."""
    __tablename__ = "webhook_delivery_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    webhook_event_id = Column(UUID(as_uuid=True), ForeignKey("webhook_events.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Attempt
    attempt_number = Column(Integer, default=1)
    status_code = Column(Integer, nullable=True)
    response_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Metadata
    user_agent = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_event_date", "webhook_event_id", "created_at"),
    )


class EventQueue(Base):
    """Event streaming queue."""
    __tablename__ = "event_queue"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Event
    event_type = Column(String(50), nullable=False)
    event_source = Column(String(100), nullable=False)  # api, system, external
    event_data = Column(JSONB, nullable=False)

    # Processing
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone.utc), nullable=True)
    processing_error = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("idx_business_processed", "business_id", "is_processed"),
        Index("idx_type_processed", "event_type", "is_processed"),
    )
