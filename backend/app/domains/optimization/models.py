"""Optimization Models."""

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Numeric, Integer, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class OptimizationExperiment(Base):
    """An A/B or multi-variant experiment."""
    __tablename__ = "optimization_experiments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    hypothesis = Column(Text, nullable=False)
    target_metric = Column(String(50), nullable=False)  # response_rate, conversion_rate, close_rate, revenue

    variant_a_name = Column(String(100), default="Control", nullable=False)
    variant_a_config = Column(JSONB, default=dict, nullable=False)
    variant_b_name = Column(String(100), default="Treatment", nullable=False)
    variant_b_config = Column(JSONB, default=dict, nullable=False)

    status = Column(String(20), default="running", nullable=False)  # running, completed, cancelled
    sample_size_target = Column(Integer, default=100, nullable=False)
    confidence_threshold = Column(Numeric(4, 3), default=0.95, nullable=False)

    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    winner_variant = Column(String(10), nullable=True)  # a, b, tie

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class OptimizationResult(Base):
    """Results of an experiment."""
    __tablename__ = "optimization_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    experiment_id = Column(UUID(as_uuid=True), ForeignKey("optimization_experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    variant_a_conversions = Column(Integer, default=0, nullable=False)
    variant_a_total = Column(Integer, default=0, nullable=False)
    variant_a_rate = Column(Numeric(5, 4), default=0, nullable=False)

    variant_b_conversions = Column(Integer, default=0, nullable=False)
    variant_b_total = Column(Integer, default=0, nullable=False)
    variant_b_rate = Column(Numeric(5, 4), default=0, nullable=False)

    improvement_percent = Column(Numeric(7, 2), default=0, nullable=False)
    is_statistically_significant = Column(Boolean, default=False, nullable=False)
    p_value = Column(Numeric(6, 5), nullable=True)

    applied_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
