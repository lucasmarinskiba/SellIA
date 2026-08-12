"""Voice Sales + Playbook models for Phase 29."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.app.database import Base


class VoiceCall(Base):
    """Voice call records."""

    __tablename__ = "voice_calls"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    prospect_id = Column(String(255), nullable=False)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    call_sid = Column(String(255), unique=True)  # Twilio call ID
    script_used = Column(Text)

    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime)
    duration_seconds = Column(Integer)

    status = Column(String(50), default="initiated")  # initiated, in_progress, completed
    outcome = Column(String(50))  # meeting_booked, qualified, unqualified

    transcript = Column(Text)

    __table_args__ = (
        Index("idx_prospect", "prospect_id"),
        Index("idx_deal", "deal_id"),
        Index("idx_started_at", "started_at"),
    )


class CallTranscript(Base):
    """Call transcript turn-by-turn."""

    __tablename__ = "call_transcripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("voice_calls.id", ondelete="CASCADE"), nullable=False)

    speaker = Column(String(50), nullable=False)  # prospect, ai
    text = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_call_timestamp", "call_id", "timestamp"),
    )


class VoiceCallMetrics(Base):
    """Call analytics and metrics."""

    __tablename__ = "voice_call_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    call_id = Column(UUID(as_uuid=True), ForeignKey("voice_calls.id", ondelete="CASCADE"), nullable=False)

    objections_raised = Column(Integer, default=0)
    objections_handled = Column(Integer, default=0)
    questions_asked = Column(Integer, default=0)
    time_to_qualification_seconds = Column(Integer)

    __table_args__ = (
        Index("idx_call_metrics", "call_id"),
    )


class SalesPlaybook(Base):
    """Extracted sales playbooks."""

    __tablename__ = "sales_playbooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    industry = Column(String(255))
    deal_stage = Column(String(50))

    win_rate = Column(Float)  # % of calls that book meeting
    usage_count = Column(Integer, default=0)

    steps = Column(JSONB)  # [{step: 1, name: "Opening", script: "..."}]
    extracted_from_calls = Column(Integer)  # How many calls analyzed

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_industry_stage", "industry", "deal_stage"),
        Index("idx_win_rate", "win_rate"),
    )


class PlaybookExecution(Base):
    """Track playbook usage during calls."""

    __tablename__ = "playbook_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    playbook_id = Column(UUID(as_uuid=True), ForeignKey("sales_playbooks.id"), nullable=False)
    call_id = Column(UUID(as_uuid=True), ForeignKey("voice_calls.id"), nullable=False)

    step_number = Column(Integer)
    rep_deviation = Column(Float)  # How much rep deviated from script (0-1)

    __table_args__ = (
        Index("idx_playbook_call", "playbook_id", "call_id"),
    )


class SalesRepPerformance(Base):
    """Track individual rep performance."""

    __tablename__ = "sales_rep_performance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    rep_id = Column(String(255), nullable=False)

    # Call metrics
    total_calls = Column(Integer, default=0)
    meeting_booking_rate = Column(Float)  # % of calls that book
    average_call_duration = Column(Integer)  # seconds
    average_objections_handled = Column(Float)

    # Playbook adoption
    playbooks_used = Column(Integer, default=0)
    win_rate_with_playbooks = Column(Float)
    win_rate_without_playbooks = Column(Float)

    # Coaching
    calls_with_recommendations = Column(Integer, default=0)
    recommendations_accepted = Column(Integer, default=0)

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_rep_id", "rep_id"),
    )


class AICallScript(Base):
    """AI-generated call scripts."""

    __tablename__ = "ai_call_scripts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    script_template = Column(Text)  # Base script
    personalization_level = Column(String(50))  # high, medium, low
    generated_at = Column(DateTime, default=datetime.utcnow)

    used_in_calls = Column(Integer, default=0)
    call_success_rate = Column(Float)  # % of calls using this script that succeeded

    __table_args__ = (
        Index("idx_deal_id", "deal_id"),
    )


class MeetingBooking(Base):
    """Meetings booked by AI voice agent."""

    __tablename__ = "meeting_bookings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    prospect_id = Column(String(255), nullable=False)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    call_id = Column(UUID(as_uuid=True), ForeignKey("voice_calls.id"), nullable=False)

    scheduled_for = Column(DateTime, nullable=False)
    ai_booked = Column(Boolean, default=True)

    confirmed_at = Column(DateTime)
    attended = Column(Boolean)

    booked_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_deal_scheduled", "deal_id", "scheduled_for"),
        Index("idx_prospect", "prospect_id"),
    )
