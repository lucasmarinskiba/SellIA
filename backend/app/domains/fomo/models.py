"""
FOMO Engine Models

Creates urgency, scarcity, and social proof to drive conversions.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class FOMOCampaign(Base):
    """A FOMO campaign: countdown, limited spots, flash sale, etc."""
    __tablename__ = "fomo_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    campaign_type = Column(String(50), nullable=False)  # countdown | limited_spots | flash_sale | social_proof | progress

    # Content
    headline = Column(String(255), nullable=False)
    subheadline = Column(Text, nullable=True)
    cta_text = Column(String(100), default="Comprar ahora", nullable=False)
    cta_url = Column(String(500), nullable=True)

    # Urgency config
    ends_at = Column(DateTime(timezone=True), nullable=True)
    total_spots = Column(Integer, nullable=True)
    spots_taken = Column(Integer, default=0, nullable=False)

    # Visual
    accent_color = Column(String(20), default="#F97316", nullable=False)
    emoji = Column(String(10), nullable=True)
    is_dismissible = Column(Boolean, default=True, nullable=False)

    # Targeting
    target_plan_ids = Column(JSONB, default=list, nullable=False)
    target_user_ids = Column(JSONB, default=list, nullable=False)
    show_on_pages = Column(JSONB, default=list, nullable=False)  # ["/dashboard", "/pricing"]

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class SocialProofEvent(Base):
    """Real-time social proof events: 'Juan acaba de comprar...'"""
    __tablename__ = "social_proof_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False)  # purchase | signup | review | milestone
    user_display_name = Column(String(100), nullable=False)
    user_avatar_url = Column(String(500), nullable=True)
    action_text = Column(String(255), nullable=False)  # "compró el Plan Pro", "cerró su primera venta"
    item_name = Column(String(255), nullable=True)
    location = Column(String(100), nullable=True)  # "Buenos Aires, AR"
    time_ago_text = Column(String(50), nullable=True)  # "hace 2 minutos"

    # Display
    is_shown = Column(Boolean, default=False, nullable=False)
    shown_count = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
