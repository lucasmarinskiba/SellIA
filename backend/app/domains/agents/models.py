"""Agentes IA - Models

Personalidades de agentes especializados basados en expertos de marketing y ventas.
Cada negocio puede configurar y chatear con estos agentes.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class AgentPersonality(Base):
    """Personalidades predefinidas de agentes expertos (Hormozi, Belfort, etc.)"""
    __tablename__ = "agent_personalities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    emoji = Column(String(10), nullable=False, default="🤖")
    tagline = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    expertise = Column(JSONB, default=list)  # list of expertise areas
    color = Column(String(20), default="#FF6B35")
    is_active = Column(Boolean, default=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class AgentConfig(Base):
    """Configuración de un agente para un negocio específico"""
    __tablename__ = "agent_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    personality_id = Column(UUID(as_uuid=True), ForeignKey("agent_personalities.id", ondelete="CASCADE"), nullable=False)
    is_enabled = Column(Boolean, default=True)
    custom_instructions = Column(Text, nullable=True)  # override/add to system prompt
    tone_override = Column(String(50), nullable=True)  # e.g. "more_aggressive", "softer"
    # Voice personality: which expert's voice/mindset to layer over this functional agent
    voice_personality_id = Column(UUID(as_uuid=True), ForeignKey("agent_personalities.id", ondelete="SET NULL"), nullable=True)
    # AI Default Auto-Reply: respond automatically when no chatbot rule or workflow matches
    ai_auto_reply_enabled = Column(Boolean, default=False, nullable=False)
    ai_auto_reply_personality_id = Column(UUID(as_uuid=True), ForeignKey("agent_personalities.id", ondelete="SET NULL"), nullable=True)
    extra_data = Column(JSONB, default=dict)  # flexible config
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    personality = relationship("AgentPersonality", foreign_keys=[personality_id])
    voice_personality = relationship("AgentPersonality", foreign_keys=[voice_personality_id])


class AgentConversation(Base):
    """Conversación entre usuario (dueño del negocio) y un agente experto"""
    __tablename__ = "agent_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    personality_id = Column(UUID(as_uuid=True), ForeignKey("agent_personalities.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=True)
    context_summary = Column(Text, nullable=True)  # running summary for long conversations
    message_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentMessage(Base):
    """Mensaje individual dentro de una conversación con agente"""
    __tablename__ = "agent_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("agent_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user' | 'assistant' | 'system'
    content = Column(Text, nullable=False)
    model_used = Column(String(50), nullable=True)  # e.g. 'gpt-4o'
    tokens_used = Column(Integer, nullable=True)
    extra_data = Column(JSONB, default=dict)  # e.g. {"action_triggered": "..."}
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class SellIAConversation(Base):
    """Conversación persistente con SellIA Assistant (meta-agent)"""
    __tablename__ = "sellia_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=True)
    messages = Column(JSONB, default=list)  # [{role, content, action, created_at}, ...]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
