"""A/B Testing models for prompt experiments.

Tracks prompt variants, experiment results, and statistical significance.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Float, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class PromptExperiment(Base):
    """An A/B test comparing two prompt variants for a given agent type."""

    __tablename__ = "prompt_experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id"),
        nullable=True,
        index=True,
    )
    name = Column(String(200), nullable=False)
    agent_type = Column(String(50), nullable=False, index=True)
    metric = Column(String(20), nullable=False)  # 'conversion', 'engagement', 'satisfaction', 'revenue'
    variant_a_name = Column(String(100), nullable=False)
    variant_a_prompt = Column(Text, nullable=False)
    variant_b_name = Column(String(100), nullable=False)
    variant_b_prompt = Column(Text, nullable=False)
    status = Column(
        String(20),
        default="draft",
        nullable=False,
    )  # 'draft', 'running', 'paused', 'completed', 'auto_promoted'
    confidence_threshold = Column(Float, default=0.95, nullable=False)
    min_samples = Column(Integer, default=100, nullable=False)
    winner_variant = Column(String(1), nullable=True)  # 'a', 'b', 'tie'
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class PromptExperimentResult(Base):
    """Individual result recorded for a conversation under an experiment."""

    __tablename__ = "prompt_experiment_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("prompt_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    variant = Column(String(1), nullable=False)  # 'a' or 'b'
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    outcome = Column(String(50), nullable=True)
    revenue = Column(Numeric(10, 2), nullable=True)
    engagement_score = Column(Float, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
