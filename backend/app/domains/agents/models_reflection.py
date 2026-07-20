"""Reflection and Chain-of-Thought Models"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class AgentReflection(Base):
    """Self-reflection analysis recorded after a conversation ends."""

    __tablename__ = "agent_reflections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    agent_type = Column(String(50), nullable=False)
    what_went_well = Column(Text, nullable=True)
    what_could_improve = Column(Text, nullable=True)
    customer_insights = Column(Text, nullable=True)
    future_recommendations = Column(Text, nullable=True)
    score = Column(Integer, nullable=True)  # self-assessment 0-100
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class ChainOfThoughtLog(Base):
    """Chain-of-thought reasoning steps logged for complex AI responses."""

    __tablename__ = "chain_of_thought_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    thought_steps = Column(JSONB, default=list)  # [{step_number, thought, action, observation}, ...]
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
