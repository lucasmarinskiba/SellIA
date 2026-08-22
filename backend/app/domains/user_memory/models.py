"""User Memory Models — Persistent user profile & preferences"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Boolean, Float, JSON, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB, TSVECTOR
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserMemory(Base):
    """Memoria persistente por usuario — preferencias, historial, contexto aprendido"""
    __tablename__ = "user_memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Preferencias del usuario
    preferred_language = Column(String(10), default="es", nullable=False)  # idioma preferido
    preferred_tone = Column(String(50), default="professional", nullable=False)  # professional, casual, aggressive, etc.
    industry_focus = Column(String(100), nullable=True)  # ej: "ecommerce", "saas", "services"
    business_stage = Column(String(50), nullable=True)  # early_stage, growth, mature, scaling

    # Contexto aprendido del usuario
    primary_business_type = Column(String(100), nullable=True)  # tipo de negocio principal
    target_audience_summary = Column(Text, nullable=True)  # resumen de audiencia objetivo
    key_challenges = Column(JSONB, default=list)  # ["sales_conversion", "lead_generation", ...]
    key_interests = Column(JSONB, default=list)  # ["marketing_automation", "seo", "social_media", ...]
    technologies_used = Column(JSONB, default=list)  # ["shopify", "instagram", "zapier", ...]

    # Comportamiento & historial
    total_conversations = Column(Integer, default=0)
    total_messages = Column(Integer, default=0)
    favorite_agents = Column(JSONB, default=list)  # [{agent_id, count, last_used}, ...]
    frequently_asked_topics = Column(JSONB, default=list)  # topics más consultados
    user_actions_taken = Column(JSONB, default=list)  # historial de acciones ejecutadas

    # Preferencias de notificación & comunicación
    email_notifications_enabled = Column(Boolean, default=True)
    notification_frequency = Column(String(50), default="daily")  # immediate, daily, weekly
    preferred_contact_time = Column(String(100), nullable=True)  # e.g., "09:00-17:00 UTC-3"

    # Insights & scoring
    engagement_score = Column(Float, default=0.0)  # 0-1, qué tan activo es
    satisfaction_score = Column(Float, default=0.0)  # 0-1, feedback implícito
    churn_risk_score = Column(Float, default=0.0)  # 0-1, riesgo de abandono
    lifetime_value_estimate = Column(String(50), default="low")  # low, medium, high, premium

    # Feature flags & beta access
    feature_flags = Column(JSONB, default=dict)  # {feature_name: enabled}
    beta_programs = Column(JSONB, default=list)  # ["ai_agents_beta", "automation_v2", ...]

    # Contexto de sesión actual
    last_active_business_id = Column(UUID(as_uuid=True), nullable=True)
    last_active_conversation_id = Column(UUID(as_uuid=True), nullable=True)
    last_active_agent_id = Column(UUID(as_uuid=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    last_activity_at = Column(DateTime(timezone=True), nullable=True)


class UserMemoryEvent(Base):
    """Evento individual que actualiza la memoria del usuario"""
    __tablename__ = "user_memory_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(String(50), nullable=False, index=True)  # message_sent, action_taken, feedback_given, etc.
    event_data = Column(JSONB, default=dict)  # {agent_id, topic, sentiment, action_result, ...}

    # Contexto
    conversation_id = Column(UUID(as_uuid=True), nullable=True)
    business_id = Column(UUID(as_uuid=True), nullable=True)
    agent_id = Column(UUID(as_uuid=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)


class UserPreference(Base):
    """Preferencias granulares por usuario"""
    __tablename__ = "user_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    preference_key = Column(String(100), nullable=False, index=True)  # e.g., "agent_hormozi_tone"
    preference_value = Column(JSONB, default=dict)  # flexible structure

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint('user_id', 'preference_key', name='uq_user_preferences_user_id_preference_key'),
    )
