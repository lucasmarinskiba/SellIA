"""
Referral & Affiliate System

Users earn credits/rewards for bringing new customers.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class ReferralCode(Base):
    """A user's unique referral code."""
    __tablename__ = "user_referral_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    code = Column(String(20), nullable=False, unique=True, index=True)
    link = Column(String(500), nullable=False)

    # Stats
    total_clicks = Column(Integer, default=0, nullable=False)
    total_signups = Column(Integer, default=0, nullable=False)
    total_conversions = Column(Integer, default=0, nullable=False)
    total_revenue_generated = Column(Numeric(14, 2), default=0, nullable=False)
    total_credits_earned = Column(Numeric(10, 2), default=0, nullable=False)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class ReferralTracking(Base):
    """Tracks each referral from click to conversion."""
    __tablename__ = "user_referral_trackings"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    referrer_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    referred_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    referral_code_id = Column(UUID(as_uuid=True), ForeignKey("referral_codes.id", ondelete="CASCADE"), nullable=False)

    # Funnel stages
    clicked_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    signed_up_at = Column(DateTime(timezone=True), nullable=True)
    converted_at = Column(DateTime(timezone=True), nullable=True)
    first_purchase_amount = Column(Numeric(10, 2), nullable=True)

    # Reward
    reward_amount = Column(Numeric(10, 2), nullable=True)
    reward_status = Column(String(20), default="pending", nullable=False)  # pending | paid | cancelled
    paid_at = Column(DateTime(timezone=True), nullable=True)

    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text(), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
