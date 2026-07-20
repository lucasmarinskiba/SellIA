"""Viral Video Agent Models"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class VideoGenerationJob(Base):
    """A viral video generation job."""

    __tablename__ = "video_generation_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    platform = Column(String(20), nullable=False, default="tiktok")
    duration = Column(Integer, nullable=False, default=15)
    status = Column(String(20), nullable=False, default="pending")
    provider_used = Column(String(50), nullable=True)
    video_url = Column(String(500), nullable=True)
    thumbnail_url = Column(String(500), nullable=True)
    script = Column(JSONB, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class VideoScript(Base):
    """Script for a viral video."""

    __tablename__ = "video_scripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("video_generation_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    hook = Column(Text, nullable=False)
    body = Column(Text, nullable=False)
    cta = Column(Text, nullable=False)
    duration = Column(Integer, nullable=False)
    visual_direction = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
