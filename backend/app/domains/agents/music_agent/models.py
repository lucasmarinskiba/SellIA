"""Music Agent Models"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class MusicGenerationJob(Base):
    """A music generation job handled by the AI agent."""

    __tablename__ = "music_generation_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    genre = Column(String(50), nullable=False, default="corporate")
    duration = Column(Integer, nullable=False, default=30)
    status = Column(String(20), nullable=False, default="pending")
    provider_used = Column(String(50), nullable=True)
    file_url = Column(String(500), nullable=True)
    file_format = Column(String(10), nullable=True, default="mp3")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class MusicTrack(Base):
    """A generated music track available for use."""

    __tablename__ = "music_tracks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    job_id = Column(
        UUID(as_uuid=True),
        ForeignKey("music_generation_jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
    track_name = Column(String(255), nullable=False)
    genre = Column(String(50), nullable=False)
    mood = Column(String(50), nullable=True)
    tempo = Column(Integer, nullable=True)
    duration = Column(Integer, nullable=False)
    file_url = Column(String(500), nullable=False)
    usage_rights = Column(String(50), nullable=True, default="commercial")
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
