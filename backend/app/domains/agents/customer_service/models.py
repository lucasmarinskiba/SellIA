"""Customer Service Auto-Agent Models"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Boolean, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class ServiceBotConfig(Base):
    """Configuration for a customer service bot per business."""
    __tablename__ = "service_bot_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False, default="SellIA Support")
    greeting_message = Column(Text, nullable=False, default="¡Hola! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?")
    fallback_message = Column(Text, nullable=False, default="No estoy seguro de entender. ¿Te gustaría que te conecte con un agente humano?")
    escalation_threshold = Column(Numeric(3, 2), nullable=False, default=0.75)  # 0.0 - 1.0
    hours_active = Column(JSONB, nullable=False, default=dict)  # e.g. {"mon": {"start": "09:00", "end": "18:00"}}
    channels = Column(JSONB, nullable=False, default=list)  # ["whatsapp", "email", "webchat"]
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ServiceInteraction(Base):
    """Log of customer service interactions handled by the bot."""
    __tablename__ = "service_interactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    bot_config_id = Column(
        UUID(as_uuid=True),
        ForeignKey("service_bot_configs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    channel = Column(String(20), nullable=False)  # whatsapp | email | dm | webchat
    customer_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    messages = Column(JSONB, nullable=False, default=list)  # [{"role": "user|bot", "content": "...", "created_at": "..."}]
    resolved = Column(Boolean, nullable=False, default=False)
    escalated = Column(Boolean, nullable=False, default=False)
    escalation_reason = Column(Text, nullable=True)
    satisfaction_score = Column(Numeric(3, 2), nullable=True)  # 0.0 - 1.0
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("ix_service_interactions_created", "created_at"),
    )
