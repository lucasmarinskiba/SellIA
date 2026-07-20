"""Retention & Loyalty Models

Referrals, loyalty programs, NPS campaigns, and customer segmentation.
"""

import uuid
import enum
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Enum, Integer, Numeric, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class ReferralStatus(str, enum.Enum):
    PENDING = "pending"
    CONVERTED = "converted"
    REWARDED = "rewarded"
    EXPIRED = "expired"


class NpsCampaignStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


class CustomerSegmentType(str, enum.Enum):
    CHAMPIONS = "champions"
    LOYAL = "loyal"
    POTENTIAL = "potential"
    NEW = "new"
    AT_RISK = "at_risk"
    LOST = "lost"


class LoyaltyProgram(Base):
    """A points/rewards loyalty program for a business."""
    __tablename__ = "loyalty_programs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    points_per_currency = Column(Numeric(10, 2), default=1, nullable=False)  # 1 punto por $1 gastado
    min_redeem_points = Column(Integer, default=100, nullable=False)
    welcome_bonus = Column(Integer, default=0, nullable=False)
    referral_bonus = Column(Integer, default=50, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ReferralProgram(Base):
    """A referral program configuration."""
    __tablename__ = "referral_programs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    reward_type = Column(String(50), default="discount_percent", nullable=False)  # discount_percent, discount_fixed, credit, product_free
    reward_value = Column(Numeric(10, 2), default=10, nullable=False)  # 10 = 10% o $10
    max_referrals_per_user = Column(Integer, default=10, nullable=False)
    expiry_days = Column(Integer, default=30, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class ReferralCode(Base):
    """A unique referral code for a customer."""
    __tablename__ = "referral_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    program_id = Column(UUID(as_uuid=True), ForeignKey("referral_programs.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)

    code = Column(String(50), nullable=False, unique=True, index=True)
    referrer_name = Column(String(255), nullable=True)
    referrer_email = Column(String(255), nullable=True)

    total_uses = Column(Integer, default=0, nullable=False)
    total_conversions = Column(Integer, default=0, nullable=False)
    total_revenue = Column(Numeric(14, 2), default=0, nullable=False)

    expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_referral_codes_business', 'business_id', 'code'),
    )


class ReferralUse(Base):
    """Tracks when someone uses a referral code."""
    __tablename__ = "referral_uses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code_id = Column(UUID(as_uuid=True), ForeignKey("referral_codes.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    referred_conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True)
    referred_email = Column(String(255), nullable=True)
    status = Column(Enum(ReferralStatus), default=ReferralStatus.PENDING, nullable=False)
    converted_order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)
    reward_given = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    converted_at = Column(DateTime(timezone=True), nullable=True)


class NpsCampaign(Base):
    """An NPS survey campaign."""
    __tablename__ = "nps_campaigns"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(200), nullable=False)
    trigger_type = Column(String(50), default="post_purchase", nullable=False)  # post_purchase, periodic, manual
    trigger_days = Column(Integer, default=14, nullable=False)  # days after purchase/event
    status = Column(Enum(NpsCampaignStatus), default=NpsCampaignStatus.DRAFT, nullable=False)

    question_text = Column(String(500), default="¿Qué tan probable es que recomiendes nuestro producto/servicio?", nullable=False)
    thank_you_message = Column(String(500), default="¡Gracias por tu feedback!", nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class NpsResponse(Base):
    """A single NPS survey response."""
    __tablename__ = "nps_responses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    campaign_id = Column(UUID(as_uuid=True), ForeignKey("nps_campaigns.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="SET NULL"), nullable=True, index=True)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True)

    score = Column(Integer, nullable=False)  # 0-10
    feedback_text = Column(Text, nullable=True)
    category = Column(String(20), nullable=True)  # promoter, passive, detractor

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_nps_responses_business_score', 'business_id', 'score'),
    )


class CustomerSegment(Base):
    """RFM-based customer segment assignment."""
    __tablename__ = "customer_segments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    segment = Column(Enum(CustomerSegmentType), nullable=False, index=True)
    r_score = Column(Integer, default=1, nullable=False)  # Recency 1-5
    f_score = Column(Integer, default=1, nullable=False)  # Frequency 1-5
    m_score = Column(Integer, default=1, nullable=False)  # Monetary 1-5
    rfm_score = Column(Integer, default=111, nullable=False)  # Combined RFM

    last_order_at = Column(DateTime(timezone=True), nullable=True)
    total_orders = Column(Integer, default=0, nullable=False)
    total_revenue = Column(Numeric(14, 2), default=0, nullable=False)
    avg_order_value = Column(Numeric(14, 2), default=0, nullable=False)

    calculated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True, nullable=False)

    __table_args__ = (
        Index('ix_customer_segments_business_segment', 'business_id', 'segment'),
    )


class HealthScoreRecord(Base):
    """Current health score for a customer (churn prevention)."""
    __tablename__ = "health_score_records"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    health_score = Column(Integer, default=100, nullable=False)  # 0-100
    trend = Column(String(20), default="stable", nullable=False)  # improving, stable, declining
    churn_risk_level = Column(String(20), default="none", nullable=False, index=True)  # none, low, medium, high, critical
    recommended_action = Column(Text, nullable=True)

    # Component scores
    last_order_days = Column(Integer, default=0, nullable=False)
    engagement_score = Column(Integer, default=0, nullable=False)
    nps_score = Column(Integer, nullable=True)
    support_ticket_count = Column(Integer, default=0, nullable=False)

    calculated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_health_scores_business_risk', 'business_id', 'churn_risk_level'),
    )


class HealthScoreHistory(Base):
    """Historical health score snapshots."""
    __tablename__ = "health_score_histories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    health_score = Column(Integer, default=100, nullable=False)
    trend = Column(String(20), default="stable", nullable=False)
    churn_risk_level = Column(String(20), default="none", nullable=False)

    calculated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('ix_health_histories_conv_date', 'conversation_id', 'calculated_at'),
    )
