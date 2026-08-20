"""Notifications & alerts models."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Index, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class NotificationChannel(str, Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    IN_APP = "in_app"
    SLACK = "slack"


class AlertType(str, Enum):
    """Alert trigger types."""
    DEAL_CLOSING = "deal_closing"
    CHURN_RISK = "churn_risk"
    LOW_INVENTORY = "low_inventory"
    REVENUE_MILESTONE = "revenue_milestone"
    FAILED_TRANSACTION = "failed_transaction"
    FRAUD_ALERT = "fraud_alert"
    SYSTEM_HEALTH = "system_health"
    CUSTOM = "custom"


class AlertPriority(str, Enum):
    """Alert priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationPreference(Base):
    """User notification preferences."""
    __tablename__ = "notification_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Channel preferences
    email_enabled = Column(Boolean, default=True)
    sms_enabled = Column(Boolean, default=True)
    whatsapp_enabled = Column(Boolean, default=True)
    in_app_enabled = Column(Boolean, default=True)
    slack_enabled = Column(Boolean, default=False)

    # Alert type subscriptions
    deal_closing = Column(Boolean, default=True)
    churn_risk = Column(Boolean, default=True)
    low_inventory = Column(Boolean, default=True)
    revenue_milestone = Column(Boolean, default=True)
    failed_transaction = Column(Boolean, default=True)
    fraud_alert = Column(Boolean, default=True)
    system_health = Column(Boolean, default=False)

    # Quiet hours
    quiet_hours_start = Column(String(5), nullable=True)  # "22:00"
    quiet_hours_end = Column(String(5), nullable=True)    # "08:00"
    quiet_weekends = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_user_business", "user_id", "business_id"),
    )


class AlertRule(Base):
    """Alert rule configuration."""
    __tablename__ = "alert_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Rule definition
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    alert_type = Column(String(50), nullable=False)  # AlertType value
    priority = Column(String(20), default=AlertPriority.MEDIUM.value)

    # Trigger conditions
    condition_json = Column(JSONB, nullable=False)  # e.g., {"threshold": 5000, "operator": ">="}
    enabled = Column(Boolean, default=True)

    # Notification channels
    channels = Column(JSONB, default=list)  # List of NotificationChannel values

    # Escalation
    escalate_after_minutes = Column(Integer, nullable=True)  # Escalate if not resolved
    escalation_to_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Frequency limits
    max_alerts_per_day = Column(Integer, default=10)
    last_triggered_at = Column(DateTime(timezone.utc), nullable=True)
    triggered_count_today = Column(Integer, default=0)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_enabled", "business_id", "enabled"),
        Index("idx_alert_type", "alert_type"),
    )


class NotificationLog(Base):
    """Notification delivery log."""
    __tablename__ = "notification_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    alert_rule_id = Column(UUID(as_uuid=True), ForeignKey("alert_rules.id", ondelete="SET NULL"), nullable=True)

    # Alert metadata
    alert_type = Column(String(50), nullable=False)
    alert_title = Column(String(255), nullable=False)
    alert_message = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False)

    # Delivery details
    channel = Column(String(50), nullable=False)  # NotificationChannel value
    recipient = Column(String(255), nullable=False)  # email/phone/user_id
    delivery_status = Column(String(20), default="pending")  # pending, sent, failed, read
    delivery_attempts = Column(Integer, default=0)
    last_attempt_at = Column(DateTime(timezone.utc), nullable=True)
    error_message = Column(Text, nullable=True)

    # Engagement
    read_at = Column(DateTime(timezone.utc), nullable=True)
    action_taken = Column(String(100), nullable=True)  # e.g., "viewed_deal", "contacted_customer"

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc), index=True)

    __table_args__ = (
        Index("idx_user_status", "user_id", "delivery_status"),
        Index("idx_alert_type_date", "alert_type", "created_at"),
        Index("idx_unread", "user_id", "read_at"),
    )


class AlertTemplate(Base):
    """Reusable alert message templates."""
    __tablename__ = "alert_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Template metadata
    name = Column(String(255), nullable=False)
    alert_type = Column(String(50), nullable=False)
    description = Column(String(500), nullable=True)

    # Templates for different channels
    email_subject = Column(String(255), nullable=False)
    email_body = Column(Text, nullable=False)
    sms_text = Column(String(160), nullable=False)
    whatsapp_text = Column(Text, nullable=False)
    in_app_title = Column(String(255), nullable=False)
    in_app_body = Column(Text, nullable=False)

    # Template variables documentation
    variables = Column(JSONB, nullable=True)  # {"customer_name": "string", "amount": "currency"}

    # System / user-defined
    is_system = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_type", "business_id", "alert_type"),
    )


class NotificationMetrics(Base):
    """Notification delivery metrics."""
    __tablename__ = "notification_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Delivery stats
    total_notifications = Column(Integer, default=0)
    successful_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    pending_count = Column(Integer, default=0)
    read_count = Column(Integer, default=0)

    # Channel breakdown
    email_count = Column(Integer, default=0)
    sms_count = Column(Integer, default=0)
    whatsapp_count = Column(Integer, default=0)
    in_app_count = Column(Integer, default=0)
    slack_count = Column(Integer, default=0)

    # Performance metrics
    avg_delivery_time_ms = Column(Integer, default=0)
    read_rate_pct = Column(Integer, default=0)  # percentage
    click_through_rate_pct = Column(Integer, default=0)

    # Alert type breakdown
    alert_type_breakdown = Column(JSONB, nullable=True)  # {"deal_closing": 45, "churn_risk": 12, ...}

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_date", "business_id", "created_at"),
    )
