"""Phase 31 Psychology Sales models."""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Float, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.app.database import Base


class DiscoveryResponse(Base):
    """Discovery question responses."""

    __tablename__ = "discovery_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    # Question & response
    question = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    question_category = Column(String(50))  # rapport, problem, impact, status_quo, desired, authority

    # Analysis
    sentiment = Column(String(50))  # positive, neutral, negative
    urgency_level = Column(Integer)  # 1-10: how urgent is problem
    pain_points = Column(JSONB)  # ["losing $50k/mo", "team burnout"]
    needs_identified = Column(JSONB)  # ["cost reduction", "faster implementation"]

    asked_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_deal_category", "deal_id", "question_category"),
        Index("idx_urgency", "urgency_level"),
    )


class NeedNarrative(Base):
    """Need creation narratives."""

    __tablename__ = "need_narratives"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    narrative = Column(Text, nullable=False)
    financial_impact_calculated = Column(Float)  # Annual impact in dollars
    pain_points = Column(JSONB)  # Pain points identified

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_deal_impact", "deal_id", "financial_impact_calculated"),
    )


class ObjectionHandling(Base):
    """Objection tracking and responses."""

    __tablename__ = "objection_handling"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    # Objection details
    objection_text = Column(Text, nullable=False)
    objection_type = Column(String(50))  # price, time, need, authority
    objection_source = Column(String(50))  # prospect, rep_concern, stakeholder

    # Response
    response_generated = Column(Text)  # AI-generated response
    response_delivered = Column(Text)  # What rep actually said

    # Outcome
    prospect_response = Column(Text)  # What prospect said after objection handle
    resolved = Column(Boolean, default=False)
    resolution_type = Column(String(50))  # overcome, postponed, lost

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_deal_type", "deal_id", "objection_type"),
        Index("idx_resolved", "resolved"),
    )


class CloseAttempt(Base):
    """Close sequence tracking."""

    __tablename__ = "close_attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    # Close details
    close_step = Column(Integer, nullable=False)  # 1-5
    commitment_asked = Column(Text, nullable=False)
    psychology_principle = Column(String(255))

    # Response
    prospect_response = Column(Text)
    response_sentiment = Column(String(50))  # positive, neutral, negative

    # Outcome
    committed = Column(Boolean, default=False)
    commitment_type = Column(String(50))  # small_yes, medium_yes, full_yes, objection

    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_deal_step", "deal_id", "close_step"),
        Index("idx_committed", "committed"),
    )


class SalesConversation(Base):
    """Full sales conversation tracking."""

    __tablename__ = "sales_conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    deal_id = Column(String(255), ForeignKey("deals.id", ondelete="CASCADE"), nullable=False)

    # Conversation flow
    conversation_json = Column(JSONB)  # Full transcript with sentiment
    sentiment_progression = Column(JSONB)  # [{"turn": 1, "sentiment": "neutral"}, ...]

    # Framework usage
    discovery_questions_asked = Column(Integer, default=0)
    need_narrative_used = Column(Boolean, default=False)
    urgency_triggers_used = Column(JSONB)  # ["supply_scarcity", "price_increase"]
    objections_handled = Column(Integer, default=0)
    closes_attempted = Column(Integer, default=0)

    # Outcome
    deal_won = Column(Boolean, default=False)
    deal_value = Column(Float)
    sales_cycle_days = Column(Integer)

    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at = Column(DateTime)

    __table_args__ = (
        Index("idx_deal_won", "deal_id", "deal_won"),
        Index("idx_closed_at", "closed_at"),
    )


class SalesRepPerformance(Base):
    """Track rep performance using psychology framework."""

    __tablename__ = "sales_rep_performance_psychology"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    rep_id = Column(String(255), nullable=False)

    # Discovery effectiveness
    discovery_questions_per_call = Column(Float)
    percent_prospects_opening_up = Column(Float)  # % who share real pain

    # Need creation
    narratives_deployed = Column(Integer, default=0)
    avg_financial_impact_quantified = Column(Float)

    # Urgency
    urgency_triggers_per_deal = Column(Float)

    # Closing
    close_attempts_per_deal = Column(Float)
    close_rate = Column(Float)  # % of closes that succeed
    average_closes_to_win = Column(Float)  # How many steps before "yes"

    # Overall
    sales_cycle_avg_days = Column(Integer)
    aov = Column(Float)  # Average deal value

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("idx_rep_id", "rep_id"),
        Index("idx_close_rate", "close_rate"),
    )
