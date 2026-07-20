"""Computer Use Agents — Models

Modelos para sesiones de automatización visual donde un agente de IA
controla un navegador web y el usuario supervisa en tiempo real.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class ComputerUseSession(Base):
    """Sesión de automatización visual con un agente de IA."""
    __tablename__ = "computer_use_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True)

    task_description = Column(Text, nullable=False)
    status = Column(
        Enum("pending", "running", "paused", "completed", "failed", "stopped", name="computer_use_status"),
        default="pending",
        nullable=False,
    )
    current_url = Column(String(2048), nullable=True)
    result_data = Column(JSONB, default=dict)
    error_message = Column(Text, nullable=True)
    total_steps = Column(Integer, default=0)
    browser_type = Column(String(20), default="chromium")
    profile_id = Column(UUID(as_uuid=True), ForeignKey("computer_use_browser_profiles.id", ondelete="SET NULL"), nullable=True)
    proxy_config_id = Column(UUID(as_uuid=True), ForeignKey("computer_use_proxy_configs.id", ondelete="SET NULL"), nullable=True)
    provider_used = Column(String(50), nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="computer_use_sessions")
    business = relationship("Business", backref="computer_use_sessions")
    steps = relationship("ComputerUseStep", backref="session", cascade="all, delete-orphan", order_by="ComputerUseStep.step_number")
    messages = relationship("ComputerUseMessage", backref="session", cascade="all, delete-orphan", order_by="ComputerUseMessage.created_at")


class ComputerUseStep(Base):
    """Paso individual dentro de una sesión de computer use."""
    __tablename__ = "computer_use_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("computer_use_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    step_number = Column(Integer, nullable=False)
    screenshot_path = Column(String(512), nullable=True)  # ruta relativa en storage
    llm_prompt = Column(Text, nullable=True)
    llm_response = Column(Text, nullable=True)
    action_type = Column(
        Enum(
            "click",
            "double_click",
            "right_click",
            "type",
            "scroll",
            "navigate",
            "wait",
            "screenshot",
            "done",
            "error",
            "pause_requested",
            name="computer_use_action_type",
        ),
        nullable=False,
    )
    action_params = Column(JSONB, default=dict)
    executed_at = Column(DateTime(timezone=True), nullable=True)
    execution_result = Column(Text, nullable=True)  # "success" o mensaje de error
    execution_ms = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class ComputerUseMessage(Base):
    """Mensajes de chat de supervisión durante una sesión."""
    __tablename__ = "computer_use_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("computer_use_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    role = Column(
        Enum("user", "agent", "system", name="computer_use_message_role"),
        nullable=False,
    )
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
