import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class PitchDeck(Base):
    __tablename__ = "pitch_decks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(
        UUID(as_uuid=True),
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(255), nullable=False)
    slides = Column(JSONB, default=list, nullable=False)
    metrics = Column(JSONB, default=dict, nullable=False)
    status = Column(String(50), default="draft", nullable=False)
    pdf_url = Column(String(500), nullable=True)
    html_url = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class PitchSlide(Base):
    __tablename__ = "pitch_slides"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deck_id = Column(
        UUID(as_uuid=True),
        ForeignKey("pitch_decks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    slide_number = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    chart_data = Column(JSONB, default=dict, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
