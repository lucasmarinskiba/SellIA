"""Workflow automation models."""

import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Index, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class TriggerType(str, Enum):
    """Workflow trigger types."""
    ORDER_CREATED = "order.created"
    ORDER_PAID = "order.paid"
    ORDER_FULFILLED = "order.fulfilled"
    CUSTOMER_CREATED = "customer.created"
    CUSTOMER_ADDED_SEGMENT = "customer.added_to_segment"
    CHURN_RISK_DETECTED = "churn_risk.detected"
    ENGAGEMENT_LOW = "engagement.low"
    DEAL_WON = "deal.won"
    DEAL_LOST = "deal.lost"
    EMAIL_OPENED = "email.opened"
    EMAIL_CLICKED = "email.clicked"
    CONTACT_CREATED = "contact.created"
    CUSTOM_WEBHOOK = "custom.webhook"


class ActionType(str, Enum):
    """Workflow action types."""
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    SEND_WHATSAPP = "send_whatsapp"
    ADD_TO_SEGMENT = "add_to_segment"
    REMOVE_FROM_SEGMENT = "remove_from_segment"
    CREATE_TASK = "create_task"
    UPDATE_CUSTOM_FIELD = "update_custom_field"
    ADD_TAG = "add_tag"
    REMOVE_TAG = "remove_tag"
    CREATE_DEAL = "create_deal"
    UPDATE_DEAL = "update_deal"
    TRIGGER_WEBHOOK = "trigger_webhook"
    LOG_EVENT = "log_event"


class ConditionOperator(str, Enum):
    """Condition comparison operators."""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    DATE_BEFORE = "date_before"
    DATE_AFTER = "date_after"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"


class Workflow(Base):
    """Workflow definition.

    Table renamed to trigger_workflows (was: workflows) — that name
    collides with app/db/models.py's legacy Workflow (email-sequence
    automation), a completely different, already-live feature under the
    same table name across a different declarative Base. Since two
    unrelated models declared the same __tablename__, only one schema
    ever governed the physical table (the legacy one, which is what
    actually exists in the live DB) — this model's own columns
    (trigger_type, trigger_config, business_id, is_active, etc.) were
    silently never created, so every call through WorkflowEngine
    (wired live at /api/v1/workflows/*) crashed. See
    memory: login_schema_drift_fixed / model_db_drift_audit.
    """
    __tablename__ = "trigger_workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Metadata
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)

    # Trigger
    trigger_type = Column(String(50), nullable=False)  # TriggerType value
    trigger_config = Column(JSONB, nullable=False)  # Trigger-specific config

    # Status
    is_active = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)

    # Execution limits
    max_executions_per_day = Column(Integer, default=0)  # 0 = unlimited
    max_executions_per_customer = Column(Integer, default=0)

    # Statistics
    total_executions = Column(Integer, default=0)
    total_failures = Column(Integer, default=0)
    last_executed_at = Column(DateTime(timezone.utc), nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_active", "business_id", "is_active"),
        Index("idx_trigger_type", "trigger_type"),
    )


class WorkflowCondition(Base):
    """Workflow condition/rule."""
    __tablename__ = "workflow_conditions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("trigger_workflows.id", ondelete="CASCADE"), nullable=False, index=True)

    # Condition definition
    field_name = Column(String(100), nullable=False)  # e.g., "rfm_score", "churn_risk"
    operator = Column(String(50), nullable=False)  # ConditionOperator value
    value = Column(String(255), nullable=True)  # Value to compare against
    value_type = Column(String(20), default="string")  # string, number, date, list

    # Logic
    logic_operator = Column(String(10), default="AND")  # AND, OR

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_workflow_condition", "workflow_id"),
    )


class WorkflowAction(Base):
    """Workflow action to execute."""
    __tablename__ = "workflow_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("trigger_workflows.id", ondelete="CASCADE"), nullable=False, index=True)

    # Action definition
    action_type = Column(String(50), nullable=False)  # ActionType value
    action_config = Column(JSONB, nullable=False)  # Action-specific config
    # e.g., for send_email: {"template_id": "...", "subject": "...", "body": "..."}
    # for add_to_segment: {"segment_id": "...", "segment_name": "..."}

    # Sequencing
    order = Column(Integer, default=0)  # Execution order
    run_after_delay = Column(Integer, default=0)  # Delay in minutes before running

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_workflow_action", "workflow_id", "order"),
    )


class WorkflowExecution(Base):
    """Workflow execution audit log."""
    __tablename__ = "trigger_workflow_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("trigger_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Trigger
    customer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    trigger_type = Column(String(50), nullable=False)
    trigger_data = Column(JSONB, nullable=True)  # Data that triggered workflow

    # Execution
    execution_status = Column(String(20), default="success")  # success, failed, skipped
    error_message = Column(Text, nullable=True)

    # Actions executed
    actions_executed = Column(Integer, default=0)
    actions_failed = Column(Integer, default=0)
    execution_log = Column(JSONB, nullable=True)  # Detailed action logs

    # Timing
    started_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone.utc), nullable=True)
    execution_time_ms = Column(Integer, nullable=True)

    __table_args__ = (
        Index("idx_workflow_execution", "workflow_id", "started_at"),
        Index("idx_customer_execution", "customer_id", "started_at"),
    )


class WorkflowMetrics(Base):
    """Workflow performance metrics."""
    __tablename__ = "workflow_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("trigger_workflows.id", ondelete="CASCADE"), nullable=False, index=True, unique=True)

    # Execution stats
    total_executions = Column(Integer, default=0)
    successful_executions = Column(Integer, default=0)
    failed_executions = Column(Integer, default=0)
    skipped_executions = Column(Integer, default=0)

    # Performance
    avg_execution_time_ms = Column(Integer, default=0)
    max_execution_time_ms = Column(Integer, default=0)
    min_execution_time_ms = Column(Integer, default=0)

    # Actions
    total_actions_executed = Column(Integer, default=0)
    action_breakdown = Column(JSONB, nullable=True)  # {action_type: count}

    # Errors
    error_count = Column(Integer, default=0)
    error_types = Column(JSONB, nullable=True)  # {error_type: count}

    # Last 7 days
    executions_7d = Column(Integer, default=0)
    success_rate_7d = Column(Integer, default=0)  # percentage

    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_business_workflow", "business_id", "workflow_id"),
    )
