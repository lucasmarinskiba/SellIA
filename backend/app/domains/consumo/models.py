"""
Consumo Models

Tracks AI API costs per user/tenant, onboarding progress, and churn signals.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, Float, Integer, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class AICallLog(Base):
    """Log of every AI API call with cost attribution."""
    __tablename__ = "ai_call_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True, index=True)

    provider = Column(String(50), nullable=False, index=True)  # openai | anthropic | kimi | ollama
    model = Column(String(100), nullable=False)
    task_type = Column(String(50), nullable=False, index=True)  # chat | content_gen | support | batch

    tokens_input = Column(Integer, nullable=False, default=0)
    tokens_output = Column(Integer, nullable=False, default=0)
    cost_usd = Column(Float, nullable=False, default=0.0)

    latency_ms = Column(Float, nullable=True)
    cache_hit = Column(Boolean, default=False, nullable=False)
    was_batched = Column(Boolean, default=False, nullable=False)

    extra_data = Column(JSONB, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class OnboardingProgress(Base):
    """Tracks where a user is in the onboarding flow."""
    __tablename__ = "onboarding_progress"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Steps completed
    account_created = Column(Boolean, default=True, nullable=False)
    business_created = Column(Boolean, default=False, nullable=False)
    channel_connected = Column(Boolean, default=False, nullable=False)
    agent_configured = Column(Boolean, default=False, nullable=False)
    first_conversation = Column(Boolean, default=False, nullable=False)
    catalog_added = Column(Boolean, default=False, nullable=False)
    automation_created = Column(Boolean, default=False, nullable=False)

    # Timestamps
    step_started_at = Column(DateTime(timezone=True), nullable=True)
    step_completed_at = Column(DateTime(timezone=True), nullable=True)
    help_requested_at = Column(DateTime(timezone=True), nullable=True)
    help_context = Column(Text, nullable=True)

    # AI Guide state
    current_step = Column(String(50), default="account_created", nullable=False)
    stuck_minutes = Column(Integer, default=0, nullable=False)
    ai_interventions_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ChurnRiskSignal(Base):
    """Predictive churn signals detected by the system (internal only)."""
    __tablename__ = "churn_risk_signals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True, index=True)

    risk_score = Column(Float, nullable=False)  # 0.0 - 1.0
    risk_level = Column(String(20), nullable=False)  # low | medium | high | critical

    # Signals that triggered this
    signals = Column(JSONB, nullable=False, default=list)

    # Action taken
    action_taken = Column(String(50), nullable=True)  # email_sent | discount_offered | human_reached_out | none
    action_result = Column(String(50), nullable=True)  # engaged | ignored | churned | recovered

    resolved = Column(Boolean, default=False, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class QualityGateConfig(Base):
    """Per-user quality gate configuration for AI support responses."""
    __tablename__ = "quality_gate_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    enabled = Column(Boolean, default=True, nullable=False)
    min_confidence_threshold = Column(Float, default=0.70, nullable=False)
    auto_escalate_on_low_confidence = Column(Boolean, default=True, nullable=False)
    max_ai_messages_before_human = Column(Integer, default=2, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
