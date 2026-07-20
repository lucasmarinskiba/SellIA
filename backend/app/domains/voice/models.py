"""Voice Agent Models"""

import uuid
from datetime import datetime, timezone, time

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Numeric, Boolean, Time
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class VoiceCall(Base):
    """A voice call (inbound or outbound) handled by the AI agent."""

    __tablename__ = "voice_calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
    )
    phone_number = Column(String(50), nullable=False)
    direction = Column(String(20), nullable=False)  # inbound, outbound
    status = Column(String(20), nullable=False, default="ringing")  # ringing, in_progress, completed, failed, voicemail
    recording_url = Column(String(500), nullable=True)
    recording_duration = Column(Integer, nullable=True)  # seconds
    transcript = Column(Text, nullable=True)
    transcript_segments = Column(JSONB, nullable=True)  # [{start, end, text, speaker}]
    ai_summary = Column(Text, nullable=True)
    outcome = Column(String(50), nullable=True)  # sale, lead, appointment, callback, no_answer, hangup
    cost_usd = Column(Numeric(10, 6), default=0)
    extra_data = Column(JSONB, default=dict, nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )


class VoiceConfig(Base):
    """Configuration for voice AI per business."""

    __tablename__ = "voice_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), nullable=False, index=True, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    voice_id = Column(String(100), nullable=False)  # ElevenLabs voice ID or OpenAI voice
    tts_provider = Column(String(20), nullable=False)  # elevenlabs, openai, google
    stt_provider = Column(String(20), nullable=False)  # openai_whisper, google, deepgram
    language = Column(String(10), default="es", nullable=False)
    greeting_message = Column(Text, nullable=False)
    max_call_duration = Column(Integer, default=600, nullable=False)  # seconds
    allowed_hours_start = Column(Time, default=time(9, 0), nullable=False)
    allowed_hours_end = Column(Time, default=time(18, 0), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
