import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class DiagnosticRun(Base):
    """Registro de ejecuciones de diagnóstico automático."""
    __tablename__ = "diagnostic_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    diagnostic_type = Column(String(50), nullable=False, index=True)
    # agent_offline | no_leads | billing_issue | channel_disconnect | slow_ai
    status = Column(String(20), nullable=False, default="running")
    # running | completed | failed
    findings = Column(JSONB, nullable=True, default=list)
    recommendations = Column(JSONB, nullable=True, default=list)
    severity = Column(String(20), nullable=False, default="info")
    # info | warning | critical
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime(timezone=True), nullable=True)
