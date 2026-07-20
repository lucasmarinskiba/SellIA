import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Integer, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class ResourceRequest(Base):
    """Solicitud de provisionamiento de un recurso (Service Broker)."""
    __tablename__ = "resource_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_type = Column(String(50), nullable=False, index=True)
    # ssl_certificate | s3_bucket | dns_record | etc.
    name = Column(String(255), nullable=False)
    # nombre descriptivo del recurso (ej: "sellia-prod-cert")
    parameters = Column(JSONB, nullable=True, default=dict)
    # parámetros específicos del recurso
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    # pending | processing | completed | failed | cancelled
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    provider_reference = Column(String(255), nullable=True)
    # ID o ARN del recurso en el proveedor cloud (ej: ARN de certificado ACM)

    jobs = relationship("ResourceJob", back_populates="request", cascade="all, delete-orphan")
    events = relationship("ResourceEvent", back_populates="request", cascade="all, delete-orphan")


class ResourceJob(Base):
    """Trabajo individual (sub-tarea) dentro de una solicitud de provisionamiento."""
    __tablename__ = "resource_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resource_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_type = Column(String(50), nullable=False)
    # validate | create | verify | rollback
    status = Column(String(20), nullable=False, default="pending")
    # pending | running | completed | failed
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text, nullable=True)
    result = Column(JSONB, nullable=True, default=dict)

    request = relationship("ResourceRequest", back_populates="jobs")


class ResourceEvent(Base):
    """Evento de auditoría del ciclo de vida de un recurso."""
    __tablename__ = "resource_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    request_id = Column(
        UUID(as_uuid=True),
        ForeignKey("resource_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    event_type = Column(String(50), nullable=False)
    # created | started | step_completed | failed | completed | cancelled
    message = Column(Text, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=True, default=dict)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    request = relationship("ResourceRequest", back_populates="events")
