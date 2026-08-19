import uuid
from datetime import datetime, timezone
from enum import Enum

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Float, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship

from app.core.database import Base


class EventType(str, Enum):
    PAGE_VIEW = "page_view"
    CONVERSION = "conversion"
    FORM_SUBMIT = "form_submit"
    BUTTON_CLICK = "button_click"
    SCROLL = "scroll"
    TIME_ON_PAGE = "time_on_page"


class AnalyticsEvent(Base):
    __tablename__ = "analytics_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    website_id = Column(UUID(as_uuid=True), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)

    event_type = Column(SQLEnum(EventType), nullable=False, index=True)
    event_name = Column(String(255), nullable=True)

    page_url = Column(String(500), nullable=False, index=True)
    page_title = Column(String(255), nullable=True)

    session_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=True)

    user_agent = Column(String(500), nullable=True)
    ip_address = Column(INET, nullable=True)
    country_code = Column(String(2), nullable=True)
    device_type = Column(String(50), nullable=True)
    browser = Column(String(100), nullable=True)

    event_metadata = Column("metadata", JSONB, default=dict, nullable=False)
    duration_ms = Column(Integer, nullable=True)
    scroll_depth = Column(Float, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    website = relationship("Website", foreign_keys=[website_id])

    __table_args__ = (
        Index('idx_analytics_website_date', 'website_id', 'created_at'),
        Index('idx_analytics_event_date', 'event_type', 'created_at'),
    )


class Conversion(Base):
    __tablename__ = "conversions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    website_id = Column(UUID(as_uuid=True), ForeignKey("websites.id", ondelete="CASCADE"), nullable=False, index=True)

    conversion_type = Column(String(100), nullable=False)
    conversion_value = Column(Float, nullable=True)

    session_id = Column(String(255), nullable=True)
    user_id = Column(String(255), nullable=True)

    source_page = Column(String(500), nullable=True)

    event_metadata = Column("metadata", JSONB, default=dict, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    website = relationship("Website", foreign_keys=[website_id])

    __table_args__ = (
        Index('idx_conversion_website_date', 'website_id', 'created_at'),
    )
