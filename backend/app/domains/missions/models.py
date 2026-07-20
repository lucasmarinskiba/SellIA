"""SellIA Missions — Models

Modelos para misiones cross-plataforma de SellIA. Una Mission es un plan
de acción generado por IA que se descompone en MissionSteps ejecutables.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class Mission(Base):
    """Misión cross-plataforma generada por SellIA."""
    __tablename__ = "missions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(
        Enum(
            "launch",
            "seo",
            "ads",
            "recovery",
            "expansion",
            "branding",
            "logistics",
            "automation",
            name="mission_category",
        ),
        nullable=False,
    )
    status = Column(
        Enum("draft", "proposed", "approved", "running", "completed", "failed", "cancelled", name="mission_status"),
        default="draft",
        nullable=False,
    )
    playbook_slug = Column(String(100), nullable=True, index=True)
    target_platforms = Column(JSONB, default=list)  # ["instagram", "tiktok", "shopify"]
    expected_impact = Column(JSONB, default=dict)  # {revenue_estimate, time_estimate, confidence}
    created_by = Column(Enum("ai", "user", name="mission_creator"), default="ai", nullable=False)

    approved_at = Column(DateTime(timezone=True), nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    steps = relationship("MissionStep", back_populates="mission", cascade="all, delete-orphan", order_by="MissionStep.step_number")
    diagnostics = relationship("BusinessDiagnostic", back_populates="mission", cascade="all, delete-orphan")


class MissionStep(Base):
    """Paso individual dentro de una misión."""
    __tablename__ = "mission_steps"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="CASCADE"), nullable=False, index=True)

    step_number = Column(Integer, nullable=False, default=1)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    platform = Column(String(50), nullable=False)  # "instagram", "computer_use", "api"
    action_type = Column(String(50), nullable=False)  # "publish_post", "create_ad", "computer_use_task"
    action_params = Column(JSONB, default=dict)
    status = Column(
        Enum("pending", "running", "completed", "failed", "skipped", "waiting_approval", name="mission_step_status"),
        default="pending",
        nullable=False,
    )
    result = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    requires_approval = Column(Boolean, default=False)
    approved_by_user = Column(Boolean, default=False)
    computer_use_session_id = Column(UUID(as_uuid=True), ForeignKey("computer_use_sessions.id", ondelete="SET NULL"), nullable=True)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relations
    mission = relationship("Mission", back_populates="steps")
    computer_use_session = relationship("ComputerUseSession")


class BusinessDiagnostic(Base):
    """Diagnóstico automático del negocio generado por SellIA."""
    __tablename__ = "business_diagnostics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True, index=True)
    mission_id = Column(UUID(as_uuid=True), ForeignKey("missions.id", ondelete="SET NULL"), nullable=True)

    diagnostic_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    category = Column(
        Enum("sales", "branding", "traffic", "seo", "logistics", "ads", "conversion", "retention", name="diagnostic_category"),
        nullable=False,
    )
    severity = Column(
        Enum("info", "warning", "critical", name="diagnostic_severity"),
        nullable=False,
    )
    finding = Column(Text, nullable=False)
    metric_value = Column(String(100), nullable=True)
    benchmark_value = Column(String(100), nullable=True)
    recommended_mission_slug = Column(String(100), nullable=True)
    context_data = Column(JSONB, default=dict)
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relations
    mission = relationship("Mission", back_populates="diagnostics")
