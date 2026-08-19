"""Staff task management models — task dispatch + completion tracking."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class TaskPriority(str, Enum):
    """Task urgency level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, Enum):
    """Task lifecycle."""
    ASSIGNED = "assigned"
    ACKNOWLEDGED = "acknowledged"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"


class TaskType(str, Enum):
    """Types of location tasks."""
    DEMO_SETUP = "demo_setup"  # Set up demo for incoming visitor
    VISITOR_TOUR = "visitor_tour"  # Conduct facility tour
    PRODUCT_DEMO = "product_demo"  # Demo specific product
    FOLLOW_UP_CALL = "follow_up_call"  # Call visitor after visit
    INVENTORY_CHECK = "inventory_check"  # Stock take
    FACILITY_PREP = "facility_prep"  # Clean/prep location
    STAFF_TRAINING = "staff_training"  # Train staff member
    CUSTOMER_SUPPORT = "customer_support"  # Handle customer issue


class StaffTask(Base):
    """Task assigned to staff member at location."""
    __tablename__ = "staff_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Assignment
    assigned_to_staff_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    assigned_by_staff_id = Column(UUID(as_uuid=True), nullable=True)  # Manager who assigned
    assigned_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Task details
    task_type = Column(SQLEnum(TaskType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)

    # Timing
    due_date = Column(DateTime(timezone=True), nullable=False)
    estimated_duration_minutes = Column(Integer, default=15)

    # Status tracking
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.ASSIGNED)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Completion
    completion_notes = Column(String(1000), nullable=True)
    completion_evidence = Column(JSONB, default=dict)  # Photo URL, audio note, checklist items, etc.

    # Context
    related_checkin_id = Column(UUID(as_uuid=True), nullable=True)  # Visitor who triggered task
    related_product_id = Column(String(255), nullable=True)  # Product for demo
    related_contact_id = Column(String(255), nullable=True)  # CRM contact for follow-up

    # Metadata
    tags = Column(JSONB, default=list)  # ["urgent", "vip", "visitor_request"]
    metadata = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index("idx_staff_status", "assigned_to_staff_id", "status"),
        Index("idx_location_due", "location_id", "due_date"),
        Index("idx_business_status", "business_id", "status"),
    )


class TaskNotification(Base):
    """Track notifications sent for task assignments."""
    __tablename__ = "task_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("staff_tasks.id", ondelete="CASCADE"), nullable=False, index=True)
    staff_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Notification details
    notification_type = Column(String(50), nullable=False)  # push, sms, email, in_app
    sent_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    read_at = Column(DateTime(timezone=True), nullable=True)
    delivery_status = Column(String(50), default="sent")  # sent, failed, bounced

    # Channels used
    device_id = Column(String(255), nullable=True)  # For push notifications
    external_notification_id = Column(String(255), nullable=True)  # Provider's ID

    metadata = Column(JSONB, default=dict)

    __table_args__ = (
        Index("idx_staff_read", "staff_id", "read_at"),
    )


class TaskTemplate(Base):
    """Reusable task templates for common workflows."""
    __tablename__ = "task_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Template
    task_type = Column(SQLEnum(TaskType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(String(1000), nullable=True)
    default_priority = Column(SQLEnum(TaskPriority), default=TaskPriority.MEDIUM)
    estimated_duration_minutes = Column(Integer, default=15)

    # When to trigger
    trigger_event = Column(String(100), nullable=True)  # "visitor_checkin", "order_received", "nps_negative"
    trigger_product_category = Column(String(100), nullable=True)  # Only for this product type

    # Checklist
    checklist_items = Column(JSONB, default=list)  # ["step 1", "step 2", ...]

    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_active", "business_id", "is_active"),
    )


class ShiftReadinessReport(Base):
    """Summary of tasks assigned vs completed per staff shift."""
    __tablename__ = "shift_readiness_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    staff_checkin_id = Column(UUID(as_uuid=True), ForeignKey("staff_checkins.id", ondelete="CASCADE"), nullable=True)
    staff_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # Shift period
    shift_start = Column(DateTime(timezone=True), nullable=False)
    shift_end = Column(DateTime(timezone=True), nullable=True)

    # Task counts
    total_tasks_assigned = Column(Integer, default=0)
    tasks_completed = Column(Integer, default=0)
    tasks_acknowledged = Column(Integer, default=0)
    tasks_overdue = Column(Integer, default=0)
    tasks_cancelled = Column(Integer, default=0)

    # Performance
    completion_rate = Column(Integer, default=0)  # 0-100 %
    avg_completion_time_minutes = Column(Integer, nullable=True)
    tasks_completed_on_time = Column(Integer, default=0)

    # Notes
    summary_notes = Column(String(1000), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index("idx_staff_shift", "staff_id", "shift_start"),
    )
