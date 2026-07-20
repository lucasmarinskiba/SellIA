"""Swarm Memory - Persistent storage for multi-agent swarm sessions."""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class SwarmSession(Base):
    """A multi-agent swarm collaboration session."""
    __tablename__ = "swarm_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task = Column(Text, nullable=False)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("agent_conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    agents_involved = Column(JSONB, default=list)  # list of agent slugs
    shared_context = Column(JSONB, default=dict)
    round_count = Column(Integer, default=0)
    consensus_reached = Column(Boolean, default=False)
    final_response = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("SwarmMessage", back_populates="session", cascade="all, delete-orphan", lazy="selectin")


class SwarmMessage(Base):
    """Individual message within a swarm session."""
    __tablename__ = "swarm_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("swarm_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(100), nullable=False)  # agent slug
    role = Column(String(50), nullable=False)  # researcher, copywriter, closer, etc.
    content = Column(Text, nullable=False)
    message_type = Column(String(50), nullable=False)  # idea, critique, agreement, action, final
    round = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    session = relationship("SwarmSession", back_populates="messages")
