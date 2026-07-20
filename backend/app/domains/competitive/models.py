"""
Competitive Intelligence Models
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class CompetitiveBattlecard(Base):
    """Stores competitive battlecards per user."""
    __tablename__ = "competitive_battlecards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    competitor_name = Column(String(255), nullable=False)
    competitor_url = Column(String(500), nullable=True)

    our_strengths = Column(JSONB, nullable=False, server_default="[]")
    our_weaknesses = Column(JSONB, nullable=False, server_default="[]")
    their_strengths = Column(JSONB, nullable=False, server_default="[]")
    their_weaknesses = Column(JSONB, nullable=False, server_default="[]")

    price_comparison = Column(Text, nullable=True)
    feature_comparison = Column(JSONB, nullable=False, server_default="{}")
    market_share_estimate = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class CompetitiveMonitor(Base):
    """24/7 competitor monitoring tracker."""
    __tablename__ = "competitive_monitors"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    competitor_name = Column(String(200), nullable=False)
    competitor_url = Column(Text, nullable=False)
    products_to_track = Column(JSONB, default=list)
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)
    last_snapshot = Column(JSONB, default=dict)
    status = Column(String(20), default="active")

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
