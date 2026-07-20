"""Simulation / Training Engine — Models

Models for sales simulation scenarios, runs, and leaderboards.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class SimulationScenario(Base):
    """Predefined or custom simulation scenarios for training agents."""
    __tablename__ = "simulation_scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String(20), nullable=False, default="beginner")
    objective = Column(String(100), nullable=False, default="close_sale")
    customer_persona = Column(JSONB, default=dict)
    agent_type = Column(String(50), nullable=False)
    success_criteria = Column(JSONB, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class SimulationRun(Base):
    """Individual execution of a simulation scenario."""
    __tablename__ = "simulation_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("simulation_scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_config = Column(JSONB, default=dict)
    status = Column(String(20), nullable=False, default="running")
    messages = Column(JSONB, default=list)
    score = Column(Integer, nullable=True)
    outcome = Column(String(50), nullable=True)
    skills_tested = Column(JSONB, default=dict)
    feedback = Column(Text, nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SimulationLeaderboard(Base):
    """Aggregated simulation performance per user and agent type."""
    __tablename__ = "simulation_leaderboards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_type = Column(String(50), nullable=False)
    total_runs = Column(Integer, default=0)
    avg_score = Column(Float, default=0.0)
    best_score = Column(Integer, default=0)
    success_rate = Column(Float, default=0.0)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
