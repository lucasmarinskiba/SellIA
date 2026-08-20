"""Loyalty program models — customer retention + rewards."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, String, DateTime, ForeignKey, Integer, Decimal, Enum as SQLEnum, Index, Boolean, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class MembershipTier(str, Enum):
    """Loyalty program membership tier."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"


class RewardType(str, Enum):
    """Reward redemption type."""
    DISCOUNT_PERCENTAGE = "discount_percentage"
    DISCOUNT_FIXED = "discount_fixed"
    FREE_PRODUCT = "free_product"
    BONUS_POINTS = "bonus_points"
    EARLY_ACCESS = "early_access"


class LoyaltyProgram(Base):
    """Business loyalty program configuration."""
    __tablename__ = "loyalty_programs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Program config
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)

    # Points system
    points_per_dollar = Column(Decimal(4, 2), default=Decimal("1.0"))  # 1 point = $1 spent
    points_expiration_days = Column(Integer, nullable=True)  # None = never expire

    # Tier thresholds (lifetime spent)
    bronze_threshold = Column(Decimal(10, 2), default=0)  # $0+
    silver_threshold = Column(Decimal(10, 2), default=Decimal("500"))  # $500+
    gold_threshold = Column(Decimal(10, 2), default=Decimal("2000"))  # $2000+
    platinum_threshold = Column(Decimal(10, 2), default=Decimal("10000"))  # $10000+

    # Tier benefits
    bronze_bonus_points = Column(Decimal(4, 2), default=1)  # 1x multiplier
    silver_bonus_points = Column(Decimal(4, 2), default=Decimal("1.25"))  # 1.25x
    gold_bonus_points = Column(Decimal(4, 2), default=Decimal("1.5"))  # 1.5x
    platinum_bonus_points = Column(Decimal(4, 2), default=Decimal("2.0"))  # 2x

    # Engagement
    welcome_bonus_points = Column(Integer, default=50)  # On signup
    birthday_bonus_points = Column(Integer, default=25)  # On birthday

    # Settings
    allow_points_transfer = Column(Boolean, default=False)
    require_account_to_earn = Column(Boolean, default=True)
    send_point_reminders = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    business = relationship("Business", foreign_keys=[business_id])


class LoyaltyMember(Base):
    """Customer loyalty program enrollment."""
    __tablename__ = "loyalty_members"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(UUID(as_uuid=True), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    loyalty_program_id = Column(UUID(as_uuid=True), ForeignKey("loyalty_programs.id", ondelete="CASCADE"), nullable=False)

    # Membership
    member_number = Column(String(50), nullable=False, unique=True)  # Membership ID
    current_tier = Column(SQLEnum(MembershipTier), default=MembershipTier.BRONZE)
    tier_since = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    # Points
    lifetime_points_earned = Column(Integer, default=0)
    current_points_balance = Column(Integer, default=0)
    points_redeemed_total = Column(Integer, default=0)

    # Lifetime metrics
    lifetime_spend = Column(Decimal(12, 2), default=0)
    total_purchases = Column(Integer, default=0)
    avg_purchase_value = Column(Decimal(10, 2), default=0)
    last_purchase_date = Column(DateTime(timezone.utc), nullable=True)
    days_since_purchase = Column(Integer, nullable=True)  # For churn detection

    # Engagement
    referral_code = Column(String(50), nullable=True)
    referred_by_member_id = Column(UUID(as_uuid=True), nullable=True)  # Referral chain
    referral_count = Column(Integer, default=0)  # Customers they've referred

    # Status
    is_active = Column(Boolean, default=True)
    enrollment_date = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    churn_risk = Column(Boolean, default=False)  # ML flag for at-risk customers

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    customer = relationship("Customer", foreign_keys=[customer_id])
    loyalty_program = relationship("LoyaltyProgram", foreign_keys=[loyalty_program_id])

    __table_args__ = (
        Index("idx_business_customer", "business_id", "customer_id"),
        Index("idx_tier_since", "current_tier", "tier_since"),
    )


class LoyaltyReward(Base):
    """Reward offer in loyalty program."""
    __tablename__ = "loyalty_rewards"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loyalty_program_id = Column(UUID(as_uuid=True), ForeignKey("loyalty_programs.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Reward details
    reward_name = Column(String(255), nullable=False)
    reward_type = Column(SQLEnum(RewardType), nullable=False)
    description = Column(String(500), nullable=True)

    # Cost
    points_required = Column(Integer, nullable=False)

    # Value
    discount_percentage = Column(Decimal(5, 2), nullable=True)  # For discount_percentage
    discount_fixed_amount = Column(Decimal(10, 2), nullable=True)  # For discount_fixed
    product_name = Column(String(255), nullable=True)  # For free_product

    # Availability
    is_active = Column(Boolean, default=True)
    min_tier_required = Column(SQLEnum(MembershipTier), default=MembershipTier.BRONZE)
    max_redemptions = Column(Integer, nullable=True)  # None = unlimited
    redemptions_count = Column(Integer, default=0)

    # Dates
    valid_from = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))
    valid_until = Column(DateTime(timezone.utc), nullable=True)

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    loyalty_program = relationship("LoyaltyProgram", foreign_keys=[loyalty_program_id])

    __table_args__ = (
        Index("idx_program_active", "loyalty_program_id", "is_active"),
    )


class LoyaltyTransaction(Base):
    """Point earning/redemption transaction."""
    __tablename__ = "loyalty_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    loyalty_member_id = Column(UUID(as_uuid=True), ForeignKey("loyalty_members.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Transaction
    transaction_type = Column(String(20), nullable=False)  # earn, redeem, bonus, expiration, transfer
    points_change = Column(Integer, nullable=False)  # Positive for earn, negative for redeem
    balance_before = Column(Integer, nullable=False)
    balance_after = Column(Integer, nullable=False)

    # Reference
    order_id = Column(String(255), nullable=True)  # For purchase-based earning
    reward_id = Column(UUID(as_uuid=True), ForeignKey("loyalty_rewards.id", ondelete="SET NULL"), nullable=True)  # For redemption
    description = Column(String(255), nullable=True)

    # Dates
    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc), index=True)

    member = relationship("LoyaltyMember", foreign_keys=[loyalty_member_id])
    reward = relationship("LoyaltyReward", foreign_keys=[reward_id])

    __table_args__ = (
        Index("idx_member_date", "loyalty_member_id", "created_at"),
        Index("idx_business_date", "business_id", "created_at"),
    )


class LoyaltyMetrics(Base):
    """Aggregate loyalty program metrics."""
    __tablename__ = "loyalty_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Date
    date = Column(String(10), nullable=False)  # YYYY-MM-DD

    # Enrollment
    total_members = Column(Integer, default=0)
    active_members = Column(Integer, default=0)
    new_members_month = Column(Integer, default=0)
    churn_risk_members = Column(Integer, default=0)

    # Tier distribution
    bronze_members = Column(Integer, default=0)
    silver_members = Column(Integer, default=0)
    gold_members = Column(Integer, default=0)
    platinum_members = Column(Integer, default=0)

    # Points
    total_points_issued = Column(Integer, default=0)
    total_points_redeemed = Column(Integer, default=0)
    avg_points_per_member = Column(Decimal(8, 2), default=0)

    # Engagement
    reward_redemption_rate = Column(Decimal(5, 2), default=0)  # % of members with redemption
    avg_redemptions_per_member = Column(Decimal(5, 2), default=0)
    referral_count = Column(Integer, default=0)

    # Revenue impact
    member_revenue_month = Column(Decimal(12, 2), default=0)
    non_member_revenue_month = Column(Decimal(12, 2), default=0)
    member_vs_nonmember_aov = Column(Decimal(8, 2), nullable=True)  # Member AOV / NonMember AOV ratio

    created_at = Column(DateTime(timezone.utc), default=lambda: datetime.now(timezone.utc))

    business = relationship("Business", foreign_keys=[business_id])

    __table_args__ = (
        Index("idx_business_date", "business_id", "date"),
    )
