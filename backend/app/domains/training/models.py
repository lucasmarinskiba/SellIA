"""Simulation / Training Engine — Models

Tables:
- simulation_scenarios: predefined training scenarios
- simulation_runs: individual simulation executions and results
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Boolean, Index, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class TrainingScenario(Base):
    """A predefined training scenario with customer persona and objective."""
    __tablename__ = "training_scenarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String(20), nullable=False, default="medium")  # easy, medium, hard, expert
    customer_persona = Column(JSONB, default=dict)  # personality, objections, budget, urgency
    objective = Column(String(100), nullable=False, default="close_sale")  # close_sale, set_appointment, gather_info, handle_complaint
    success_criteria = Column(JSONB, default=dict)
    agent_type = Column(String(50), nullable=False, default="general")  # which agent to test
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    runs = relationship("TrainingRun", back_populates="scenario", cascade="all, delete-orphan")


class TrainingRun(Base):
    """A single execution of a simulation scenario."""
    __tablename__ = "training_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scenario_id = Column(UUID(as_uuid=True), ForeignKey("training_scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agent_configs.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(20), nullable=False, default="running")  # running, completed, failed
    messages = Column(JSONB, default=list)  # conversation log [{role, content, turn, timestamp}, ...]
    score = Column(Integer, nullable=True)  # 0-100
    objective_achieved = Column(Boolean, nullable=True)
    time_to_close_seconds = Column(Integer, nullable=True)
    customer_satisfaction = Column(Float, nullable=True)  # 0-5
    skills_tested = Column(JSONB, default=dict)  # {skill: score, ...}
    feedback = Column(Text, nullable=True)  # LLM-generated qualitative feedback
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    scenario = relationship(lambda: TrainingScenario, back_populates="runs")
