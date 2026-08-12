"""Email Automation models for Phase 28."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.app.database import Base


class SendTimePrediction(Base):
    """Send time optimization predictions."""

    __tablename__ = "send_time_predictions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    person_id = Column(String(255), nullable=False)

    # Predicted optimal time
    recommended_send_time = Column(DateTime, nullable=False)
    predicted_open_probability = Column(Float)  # 0-100

    # Alternatives
    alternative_time_1 = Column(DateTime)
    alternative_time_2 = Column(DateTime)

    # Model
    model_version = Column(String(50))
    prediction_date = Column(DateTime, default=datetime.utcnow, nullable=False)

    # If sent, track actual result
    actual_send_time = Column(DateTime)
    actually_opened = Column(Boolean)

    __table_args__ = (
        Index("idx_person_email", "person_id"),
        Index("idx_recommended_time", "recommended_send_time"),
    )


class EmailOpenTracking(Base):
    """Track email open events."""

    __tablename__ = "email_open_tracking"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email_id = Column(String(255), nullable=False)
    person_id = Column(String(255), nullable=False)

    sent_at = Column(DateTime, nullable=False)
    opened_at = Column(DateTime, nullable=False)
    open_delay_minutes = Column(Integer)

    device_type = Column(String(50))  # mobile, desktop
    email_client = Column(String(50))  # Gmail, Outlook, etc

    __table_args__ = (
        Index("idx_person_sent", "person_id", "sent_at"),
        Index("idx_email", "email_id"),
    )


class ProposalDraft(Base):
    """Generated proposal drafts."""

    __tablename__ = "proposal_drafts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    html_content = Column(Text, nullable=False)
    word_count = Column(Integer)

    # Generation
    generation_method = Column(String(50))  # claude_opus, template
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Usage
    sent_to = Column(String(255))
    sent_at = Column(DateTime)

    # Tracking
    view_count = Column(Integer, default=0)
    last_viewed_at = Column(DateTime)
    days_to_close = Column(Integer)

    __table_args__ = (
        Index("idx_deal", "deal_id"),
        Index("idx_sent_at", "sent_at"),
    )


class ProposalView(Base):
    """Proposal view tracking."""

    __tablename__ = "proposal_views"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    draft_id = Column(UUID(as_uuid=True), ForeignKey("proposal_drafts.id", ondelete="CASCADE"), nullable=False)

    viewed_by = Column(String(255), nullable=False)
    viewed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_seconds = Column(Integer)
    pages_viewed = Column(Integer)

    __table_args__ = (
        Index("idx_draft", "draft_id"),
        Index("idx_viewed_at", "viewed_at"),
    )


class CompetitorMention(Base):
    """Detected competitor mentions."""

    __tablename__ = "competitor_mentions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)
    person_id = Column(String(255), nullable=False)

    competitor_name = Column(String(255), nullable=False)
    source = Column(String(50))  # email, call_transcript, message
    context = Column(Text)

    detected_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    confidence = Column(Float)  # 0-1

    __table_args__ = (
        Index("idx_deal_competitor", "deal_id", "competitor_name"),
        Index("idx_detected_at", "detected_at"),
    )


class CompetitorResponse(Base):
    """Competitor response campaigns."""

    __tablename__ = "competitor_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    mention_id = Column(UUID(as_uuid=True), ForeignKey("competitor_mentions.id", ondelete="CASCADE"), nullable=False)

    response_type = Column(String(50))  # ai_generated, template, manual
    response_text = Column(Text)

    sent_at = Column(DateTime)
    sent_to = Column(String(255))

    __table_args__ = (
        Index("idx_mention", "mention_id"),
        Index("idx_sent_at", "sent_at"),
    )
