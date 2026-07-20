"""Computer Use Agents — Modelos Extendidos

Modelos adicionales para: templates, scheduled tasks, annotations,
browser profiles, proxy configs, session sharing, y batch operations.
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, JSON, Boolean, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class ComputerUseTemplate(Base):
    """Plantillas predefinidas de tareas de Computer Use."""
    __tablename__ = "computer_use_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    task_description = Column(Text, nullable=False)
    start_url = Column(String(2048), nullable=True)
    tags = Column(JSONB, default=list)
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="computer_use_templates")


class ComputerUseScheduledTask(Base):
    """Tareas programadas de Computer Use (cron)."""
    __tablename__ = "computer_use_scheduled_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True)

    name = Column(String(200), nullable=False)
    task_description = Column(Text, nullable=False)
    start_url = Column(String(2048), nullable=True)
    cron_expression = Column(String(100), nullable=False)  # e.g. "0 9 * * *"
    timezone = Column(String(50), default="America/Argentina/Buenos_Aires")
    provider = Column(String(50), default="auto")
    is_active = Column(Boolean, default=True)
    max_steps = Column(Integer, default=30)

    # Last execution tracking
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    last_session_id = Column(UUID(as_uuid=True), ForeignKey("computer_use_sessions.id", ondelete="SET NULL"), nullable=True)
    total_runs = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    fail_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="computer_use_scheduled_tasks")
    last_session = relationship("ComputerUseSession", foreign_keys=[last_session_id])


class ComputerUseAnnotation(Base):
    """Anotaciones/comentarios en screenshots específicos."""
    __tablename__ = "computer_use_annotations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("computer_use_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    content = Column(Text, nullable=False)
    x_coordinate = Column(Integer, nullable=True)  # Optional: point on screenshot
    y_coordinate = Column(Integer, nullable=True)
    color = Column(String(20), default="#f59e0b")  # Hex color for marker

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    session = relationship("ComputerUseSession", backref="annotations")


class ComputerUseBrowserProfile(Base):
    """Perfiles de navegador con cookies, localStorage, viewport."""
    __tablename__ = "computer_use_browser_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True)

    name = Column(String(200), nullable=False)
    viewport_width = Column(Integer, default=1280)
    viewport_height = Column(Integer, default=720)
    user_agent = Column(Text, nullable=True)
    locale = Column(String(10), default="es-ES")
    timezone_id = Column(String(50), default="America/Argentina/Buenos_Aires")
    cookies = Column(JSONB, default=list)
    local_storage = Column(JSONB, default=dict)
    geolocation = Column(JSONB, nullable=True)  # {"latitude": -34.6, "longitude": -58.4}
    is_default = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="computer_use_browser_profiles")


class ComputerUseProxyConfig(Base):
    """Configuraciones de proxy para sesiones de Computer Use."""
    __tablename__ = "computer_use_proxy_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    proxy_type = Column(Enum("http", "https", "socks5", name="proxy_type"), default="http")
    host = Column(String(255), nullable=False)
    port = Column(Integer, nullable=False)
    username = Column(String(255), nullable=True)
    password_encrypted = Column(Text, nullable=True)  # Fernet encrypted
    rotation_url = Column(String(2048), nullable=True)  # URL para rotar IP
    is_active = Column(Boolean, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    use_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="computer_use_proxy_configs")


class ComputerUseSessionShare(Base):
    """Compartir sesiones entre usuarios con permisos."""
    __tablename__ = "computer_use_session_shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("computer_use_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    shared_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    shared_with_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    shared_with_email = Column(String(255), nullable=True)  # For invite-by-email
    permission = Column(Enum("view", "comment", "control", name="share_permission"), default="view")
    token = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    session = relationship("ComputerUseSession", backref="shares")
    shared_by = relationship("User", foreign_keys=[shared_by_user_id], backref="shared_sessions")
    shared_with = relationship("User", foreign_keys=[shared_with_user_id], backref="received_sessions")

    __table_args__ = (
        UniqueConstraint("session_id", "shared_with_user_id", name="uq_session_share_user"),
    )


class ComputerUseBatchJob(Base):
    """Trabajos batch: misma tarea en múltiples URLs."""
    __tablename__ = "computer_use_batch_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True)

    name = Column(String(200), nullable=False)
    task_description = Column(Text, nullable=False)
    urls = Column(JSONB, default=list)  # Lista de URLs
    provider = Column(String(50), default="auto")
    max_steps_per_url = Column(Integer, default=30)
    concurrency = Column(Integer, default=3)

    status = Column(
        Enum("pending", "running", "completed", "failed", "cancelled", name="batch_status"),
        default="pending",
    )
    completed_count = Column(Integer, default=0)
    failed_count = Column(Integer, default=0)
    total_count = Column(Integer, default=0)
    results_summary = Column(JSONB, default=dict)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", backref="computer_use_batch_jobs")


class ComputerUseSessionTag(Base):
    """Tags para sesiones (many-to-many via association)."""
    __tablename__ = "computer_use_session_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("computer_use_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    tag = Column(String(50), nullable=False, index=True)
    color = Column(String(20), default="#3b82f6")

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    session = relationship("ComputerUseSession", backref="session_tags")

    __table_args__ = (
        UniqueConstraint("session_id", "tag", name="uq_session_tag"),
    )


class ComputerUseSessionNote(Base):
    """Notas generales de una sesión."""
    __tablename__ = "computer_use_session_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("computer_use_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    content = Column(Text, nullable=False)
    is_pinned = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    session = relationship("ComputerUseSession", backref="notes")


class ComputerUseSessionBookmark(Base):
    """Bookmarks/marcadores dentro de una sesión."""
    __tablename__ = "computer_use_session_bookmarks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("computer_use_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    step_number = Column(Integer, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    label = Column(String(200), nullable=False)
    color = Column(String(20), default="#3b82f6")

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    session = relationship("ComputerUseSession", backref="bookmarks")


class ComputerUseWebhook(Base):
    """Webhooks para notificaciones de eventos de sesión."""
    __tablename__ = "computer_use_webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=True)

    name = Column(String(200), nullable=False)
    url = Column(String(2048), nullable=False)
    events = Column(JSONB, default=list)  # ["session.completed", "session.failed"]
    secret = Column(String(255), nullable=True)  # For HMAC signature
    is_active = Column(Boolean, default=True)
    last_triggered_at = Column(DateTime(timezone=True), nullable=True)
    last_status_code = Column(Integer, nullable=True)
    failure_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", backref="computer_use_webhooks")
