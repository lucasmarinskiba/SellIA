"""Causal Reasoning Engine Models"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Integer, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class ObjectionPattern(Base):
    """Aggregated objection patterns across conversations for a business."""

    __tablename__ = "objection_patterns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    pattern_name = Column(String(100), nullable=False)
    objection_text = Column(String(200), nullable=False)
    root_cause = Column(Text, nullable=True)
    frequency_count = Column(Integer, nullable=False, default=0)
    frequency_percent = Column(Float, nullable=False, default=0.0)
    overcome_count = Column(Integer, nullable=False, default=0)
    overcome_rate = Column(Float, nullable=False, default=0.0)
    affected_segments = Column(JSONB, default=list)
    recommended_response = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class CausalAnalysis(Base):
    """Root-cause analysis for failed or stalled deals."""

    __tablename__ = "causal_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    deal_outcome = Column(String(50), nullable=False)  # 'lost', 'stalled', 'objection_unresolved'
    surface_reason = Column(Text, nullable=True)
    root_cause = Column(Text, nullable=True)
    contributing_factors = Column(JSONB, default=list)
    recommended_fix = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
