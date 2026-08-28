"""
FOMO Engine Models - Star Player Implementation
Creates urgency, scarcity, and social proof to drive conversions.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Boolean, Date, Numeric, UniqueConstraint, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class FOMOCampaign(Base):
    """A FOMO campaign: countdown, limited spots, flash sale, etc."""
    __tablename__ = "fomo_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id', ondelete='CASCADE'), nullable=True)
    name = Column(String(200), nullable=False)
    campaign_type = Column(String(50), nullable=False)  # countdown | limited_spots | flash_sale | social_proof | progress | scarcity | exclusivity
    trigger_type = Column(String(50), nullable=True)  # cart_abandon | page_view | churn_risk | low_engagement | product_view

    # Content
    headline = Column(String(255), nullable=False)
    subheadline = Column(Text, nullable=True)
    cta_text = Column(String(100), default="Comprar ahora", nullable=False)
    cta_url = Column(String(500), nullable=True)

    # Urgency config
    ends_at = Column(DateTime(timezone=True), nullable=True)
    total_spots = Column(Integer, nullable=True)
    spots_taken = Column(Integer, default=0, nullable=False)

    # Config (flexible JSONB for A/B testing)
    config = Column(JSONB, nullable=True)  # {stockThreshold, countdownHours, segment, messageTemplate, discountPercent}

    # Visual
    accent_color = Column(String(20), default="#F97316", nullable=False)
    emoji = Column(String(10), nullable=True)
    is_dismissible = Column(Boolean, default=True, nullable=False)

    # Targeting
    target_plan_ids = Column(JSONB, default=list, nullable=False)
    target_user_ids = Column(JSONB, default=list, nullable=False)
    show_on_pages = Column(JSONB, default=list, nullable=False)

    # Status & lifecycle
    status = Column(String(20), default='active', nullable=False)  # active | paused | draft
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    events = relationship("FOMOEvent", back_populates="campaign", cascade="all, delete-orphan")
    ab_tests = relationship("FOMOABTest", back_populates="campaign", cascade="all, delete-orphan")
    metrics = relationship("FOMOMetric", back_populates="campaign", cascade="all, delete-orphan")


class FOMOEvent(Base):
    """Real-time FOMO events: purchases, views, cart abandonment, etc."""
    __tablename__ = "fomo_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('fomo_campaigns.id', ondelete='CASCADE'), nullable=False)
    event_type = Column(String(50), nullable=False)  # purchase | view | add_to_cart | abandoned
    customer_id = Column(UUID(as_uuid=True), nullable=True)
    product_id = Column(UUID(as_uuid=True), nullable=True)
    event_metadata = Column("metadata", JSONB, nullable=True)  # {revenue, customerName, productName, etc}
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # Relationships
    campaign = relationship("FOMOCampaign", back_populates="events")

    __table_args__ = (
        Index('idx_fomo_events_campaign', 'campaign_id', 'created_at'),
    )


class FOMOABTest(Base):
    """A/B testing framework for FOMO campaigns"""
    __tablename__ = "fomo_ab_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('fomo_campaigns.id', ondelete='CASCADE'), nullable=False)

    # Variants (JSONB config objects)
    variant_a = Column(JSONB, nullable=False)
    variant_b = Column(JSONB, nullable=False)

    # Counters
    variant_a_conversions = Column(Integer, default=0, nullable=False)
    variant_a_views = Column(Integer, default=0, nullable=False)
    variant_b_conversions = Column(Integer, default=0, nullable=False)
    variant_b_views = Column(Integer, default=0, nullable=False)

    # Results
    winner = Column(String(1), nullable=True)  # 'A' | 'B'
    status = Column(String(20), default='running', nullable=False)  # running | completed
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    campaign = relationship("FOMOCampaign", back_populates="ab_tests")

    __table_args__ = (
        Index('idx_fomo_ab_tests_campaign', 'campaign_id'),
    )


class FOMOMetric(Base):
    """Daily FOMO campaign metrics"""
    __tablename__ = "fomo_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('fomo_campaigns.id', ondelete='CASCADE'), nullable=False)
    date = Column(Date, nullable=False)
    impressions = Column(Integer, default=0, nullable=False)
    conversions = Column(Integer, default=0, nullable=False)
    revenue = Column(Numeric(15, 2), default=Decimal('0.00'), nullable=False)

    # Relationships
    campaign = relationship("FOMOCampaign", back_populates="metrics")

    __table_args__ = (
        UniqueConstraint('campaign_id', 'date', name='uq_fomo_metrics_campaign_date'),
        Index('idx_fomo_metrics_campaign', 'campaign_id', 'date'),
    )


class SocialProofEvent(Base):
    """Real-time social proof events: 'Juan acaba de comprar...'"""
    __tablename__ = "social_proof_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(50), nullable=False)
    user_display_name = Column(String(100), nullable=False)
    user_avatar_url = Column(String(500), nullable=True)
    action_text = Column(String(255), nullable=False)
    item_name = Column(String(255), nullable=True)
    location = Column(String(100), nullable=True)
    time_ago_text = Column(String(50), nullable=True)
    is_shown = Column(Boolean, default=False, nullable=False)
    shown_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
