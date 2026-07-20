"""CRM Builder Models"""

import uuid
import enum
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class CRMBuildStatus(str, enum.Enum):
    PENDING = "pending"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class CRMBuildJob(Base):
    """Trabajo de generación de sistema CRM."""
    __tablename__ = "crm_build_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    crm_name = Column(String(255), nullable=False)
    modules = Column(JSONB, default=list, nullable=False)
    status = Column(Enum(CRMBuildStatus), default=CRMBuildStatus.PENDING, nullable=False, index=True)
    code_url = Column(String(1000), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CRMModule(Base):
    """Módulo individual dentro de un trabajo de CRM."""
    __tablename__ = "crm_modules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("crm_build_jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    module_name = Column(String(100), nullable=False)  # contacts, deals, pipeline, tasks, calendar, reservations, automations
    config = Column(JSONB, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
