"""Autopilot Engine Models

AutopilotConfig, AutopilotActionLog, AutopilotDailyReport.
"""

import uuid
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Boolean, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class AutopilotActionStatus(str, enum.Enum):
    EXECUTED = "executed"
    PENDING_APPROVAL = "pending_approval"
    ESCALATED = "escalated"
    REJECTED = "rejected"
    FAILED = "failed"


class AutopilotActionType(str, enum.Enum):
    QUALIFY_LEAD = "qualify_lead"
    MOVE_DEAL = "move_deal"
    SEND_FOLLOWUP = "send_followup"
    CLOSE_DEAL = "close_deal"
    CREATE_ORDER = "create_order"
    REQUEST_REVIEW = "request_review"
    ACTIVATE_RECOVERY_WORKFLOW = "activate_recovery_workflow"
    ESCALATE_TO_HUMAN = "escalate_to_human"
    SEND_PROPOSAL = "send_proposal"
    ASSIGN_AGENT = "assign_agent"
    START_SEQUENCE = "start_sequence"
    CREATE_DEAL = "create_deal"
    UPDATE_LEAD_SCORE = "update_lead_score"
    APPLY_RECOMMENDATION = "apply_recommendation"


class AutopilotConfig(Base):
    """Per-business configuration for what the autopilot can do autonomously."""
    __tablename__ = "autopilot_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Toggles for autonomous actions (default: False = require approval)
    auto_qualify_leads = Column(Boolean, default=False, nullable=False)
    auto_move_deals = Column(Boolean, default=False, nullable=False)
    auto_send_followups = Column(Boolean, default=False, nullable=False)
    auto_close_deals = Column(Boolean, default=False, nullable=False)
    auto_create_orders = Column(Boolean, default=False, nullable=False)
    auto_request_reviews = Column(Boolean, default=False, nullable=False)
    auto_activate_recovery_workflows = Column(Boolean, default=False, nullable=False)
    auto_escalate_to_human = Column(Boolean, default=True, nullable=False)  # default True for safety

    # Thresholds and limits
    approval_threshold_amount = Column(Numeric(14, 2), default=5000, nullable=False)  # Orders above this require approval
    max_daily_auto_messages = Column(Integer, default=50, nullable=False)
    max_daily_auto_closes = Column(Integer, default=10, nullable=False)
    max_daily_auto_orders = Column(Integer, default=10, nullable=False)

    # Human escalation config
    human_escalation_channels = Column(JSONB, default=list, nullable=False)  # ["email", "whatsapp", "in_app"]
    escalation_email = Column(String(255), nullable=True)
    escalation_whatsapp = Column(String(100), nullable=True)

    # Master toggle
    is_active = Column(Boolean, default=False, nullable=False)  # Opt-in: autopilot OFF by default
    is_paused = Column(Boolean, default=False, nullable=False)  # Emergency pause
    paused_reason = Column(Text, nullable=True)
    paused_at = Column(DateTime(timezone=True), nullable=True)

    # AI explanation settings
    require_ai_explanation = Column(Boolean, default=True, nullable=False)  # Always explain why
    explanation_language = Column(String(10), default="es", nullable=False)  # es, en, pt

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_autopilot_configs_business_active", "business_id", "is_active"),
    )


class AutopilotActionLog(Base):
    """Audit log of every decision the autopilot makes."""
    __tablename__ = "autopilot_action_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    action_type = Column(Enum(AutopilotActionType), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)  # "deal", "conversation", "order", "workflow", "recommendation"
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)

    # AI-generated explanation
    reason = Column(Text, nullable=False)  # Why the system decided this
    ai_explanation = Column(Text, nullable=True)  # Detailed AI reasoning
    confidence_score = Column(Integer, default=0, nullable=False)  # 0-100 AI confidence

    # Context snapshot
    context_data = Column(JSONB, default=dict, nullable=False)  # Relevant data at decision time

    status = Column(Enum(AutopilotActionStatus), default=AutopilotActionStatus.EXECUTED, nullable=False, index=True)
    error_message = Column(Text, nullable=True)

    # For pending/escalated actions
    requires_approval = Column(Boolean, default=False, nullable=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)
    rejected_reason = Column(Text, nullable=True)

    # Revenue impact
    revenue_impact = Column(Numeric(14, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    executed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_autopilot_logs_business_status", "business_id", "status"),
        Index("ix_autopilot_logs_business_created", "business_id", "created_at"),
        Index("ix_autopilot_logs_entity", "entity_type", "entity_id"),
    )


class AutopilotDailyReport(Base):
    """Summary of what the autopilot did in a day."""
    __tablename__ = "autopilot_daily_reports"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    report_date = Column(DateTime(timezone=True), nullable=False, index=True)

    # Actions summary
    leads_contacted = Column(Integer, default=0, nullable=False)
    deals_moved = Column(Integer, default=0, nullable=False)
    deals_closed = Column(Integer, default=0, nullable=False)
    orders_created = Column(Integer, default=0, nullable=False)
    messages_sent = Column(Integer, default=0, nullable=False)
    sequences_started = Column(Integer, default=0, nullable=False)
    workflows_activated = Column(Integer, default=0, nullable=False)

    # Revenue
    revenue_generated = Column(Numeric(14, 2), default=0, nullable=False)
    deals_value_closed = Column(Numeric(14, 2), default=0, nullable=False)

    # Escalations and pending
    actions_escalated = Column(Integer, default=0, nullable=False)
    actions_pending_approval = Column(Integer, default=0, nullable=False)
    actions_rejected = Column(Integer, default=0, nullable=False)

    # AI-generated summary
    ai_summary = Column(Text, nullable=True)  # "Hoy contactaste 12 leads, cerraste 3 deals..."
    highlights = Column(JSONB, default=list, nullable=False)  # [{"type": "deal_closed", "description": "..."}]

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_autopilot_reports_business_date", "business_id", "report_date", unique=True),
    )
