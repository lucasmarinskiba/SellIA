"""App MVP Builder Models"""

import uuid
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class AppBuildStatus(str, enum.Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class AppBuildJob(Base):
    """Trabajo de generación de aplicación MVP."""
    __tablename__ = "app_build_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    app_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    features = Column(JSONB, default=list, nullable=False)
    tech_stack = Column(String(100), default="nextjs-fastapi-postgres", nullable=False)
    status = Column(Enum(AppBuildStatus), default=AppBuildStatus.PENDING, nullable=False, index=True)

    code_zip_url = Column(String(1000), nullable=True)
    preview_url = Column(String(1000), nullable=True)
    deploy_instructions = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class AppFeature(Base):
    """Feature individual dentro de un trabajo de build."""
    __tablename__ = "app_features"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("app_build_jobs.id", ondelete="CASCADE"), nullable=False, index=True)

    feature_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    priority = Column(Integer, default=1, nullable=False)
    estimated_hours = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
