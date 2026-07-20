import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, DateTime, Text, Float, Boolean, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class SyntheticCheck(Base):
    """Configuración de checks sintéticos."""
    __tablename__ = "synthetic_checks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, index=True)
    check_type = Column(String(50), nullable=False)  # http | tcp | ssl | ai_latency
    target_url = Column(String(500), nullable=True)
    expected_status = Column(Integer, nullable=True)
    expected_keyword = Column(String(255), nullable=True)
    interval_seconds = Column(Integer, default=300, nullable=False)
    timeout_seconds = Column(Integer, default=10, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    alert_severity = Column(String(20), default="warning", nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SyntheticResult(Base):
    """Resultado individual de un check sintético."""
    __tablename__ = "synthetic_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    check_id = Column(UUID(as_uuid=True), ForeignKey("synthetic_checks.id", ondelete="CASCADE"), nullable=False, index=True)
    success = Column(Boolean, nullable=False)
    response_time_ms = Column(Float, nullable=True)
    status_code = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    checked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SystemHealthSnapshot(Base):
    """Snapshot agregado de salud del sistema."""
    __tablename__ = "system_health_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    overall_status = Column(String(20), nullable=False)  # healthy | degraded | down
    checks_total = Column(Integer, nullable=False)
    checks_passed = Column(Integer, nullable=False)
    avg_response_time_ms = Column(Float, nullable=True)
    details = Column(JSONB, nullable=True)
    snapshot_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
