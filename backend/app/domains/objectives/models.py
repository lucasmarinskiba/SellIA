"""Objectives & KPIs Models

Tracks business goals, departments, KPIs, and key results
for the virtual company architecture.
"""

import uuid
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Numeric, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class ObjectiveStatus(str, enum.Enum):
    ACTIVE = "active"
    ACHIEVED = "achieved"
    AT_RISK = "at_risk"
    MISSED = "missed"
    PAUSED = "paused"


class ObjectivePeriod(str, enum.Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class Department(Base):
    """A department in the virtual company (Sales, Marketing, Support, etc.)"""
    __tablename__ = "departments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(100), nullable=False)
    slug = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    head_agent_personality_id = Column(UUID(as_uuid=True), ForeignKey("agent_personalities.id", ondelete="SET NULL"), nullable=True)
    color = Column(String(20), default="#3B82F6")
    icon = Column(String(50), default="briefcase")

    config = Column(JSONB, default=dict, nullable=False)  # {"auto_adjust": true, "alert_threshold": 0.8}
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class BusinessObjective(Base):
    """A business objective (OKR style) linked to a department."""
    __tablename__ = "business_objectives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    period = Column(Enum(ObjectivePeriod), default=ObjectivePeriod.MONTHLY, nullable=False)
    status = Column(Enum(ObjectiveStatus), default=ObjectiveStatus.ACTIVE, nullable=False, index=True)

    # Target values
    target_value = Column(Numeric(14, 2), nullable=False)  # ej: 100000.00
    current_value = Column(Numeric(14, 2), default=0, nullable=False)
    unit = Column(String(50), default="ARS", nullable=False)  # ARS, USD, count, percent

    # Date range
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)

    # Link to workflow/agent that drives this objective
    linked_workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="SET NULL"), nullable=True)
    linked_channel_platform = Column(String(50), nullable=True)  # "whatsapp", "facebook_ads"

    # Alert config
    alert_threshold_percent = Column(Numeric(5, 2), default=80, nullable=False)  # Alert if below 80%
    alert_channels = Column(JSONB, default=list, nullable=False)  # ["whatsapp", "email"]

    extra_data = Column(JSONB, default=dict, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_objectives_business_status', 'business_id', 'status'),
    )


class KPI(Base):
    """A Key Performance Indicator tracked for a department or business."""
    __tablename__ = "kpis"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(UUID(as_uuid=True), ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    objective_id = Column(UUID(as_uuid=True), ForeignKey("business_objectives.id", ondelete="SET NULL"), nullable=True, index=True)

    name = Column(String(200), nullable=False)
    slug = Column(String(50), nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Metric config
    metric_type = Column(String(50), nullable=False)  # revenue, leads, conversions, nps, churn, ltv, etc.
    aggregation = Column(String(20), default="sum", nullable=False)  # sum, count, avg, max, min
    target_value = Column(Numeric(14, 2), nullable=True)
    current_value = Column(Numeric(14, 2), default=0, nullable=False)
    unit = Column(String(50), default="count", nullable=False)

    # Period
    period = Column(Enum(ObjectivePeriod), default=ObjectivePeriod.MONTHLY, nullable=False)
    period_start = Column(DateTime(timezone=True), nullable=True)
    period_end = Column(DateTime(timezone=True), nullable=True)

    # Data source
    data_source = Column(String(100), nullable=False)  # orders, conversations, workflows, lead_scores, etc.
    data_source_filter = Column(JSONB, default=dict, nullable=False)  # {"platform": "whatsapp", "status": "paid"}

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_kpis_business_slug_period', 'business_id', 'slug', 'period'),
    )


class KeyResult(Base):
    """A key result/milestone within a business objective."""
    __tablename__ = "key_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    objective_id = Column(UUID(as_uuid=True), ForeignKey("business_objectives.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    target_value = Column(Numeric(14, 2), nullable=False)
    current_value = Column(Numeric(14, 2), default=0, nullable=False)
    unit = Column(String(50), default="count", nullable=False)

    weight = Column(Numeric(3, 2), default=1.0, nullable=False)  # Importance weight (0.0 - 1.0)
    due_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(Enum(ObjectiveStatus), default=ObjectiveStatus.ACTIVE, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
