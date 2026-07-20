"""
Coupon & Discount System
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Text, ForeignKey, DateTime, Integer, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB

from app.core.database import Base


class Coupon(Base):
    """A discount coupon."""
    __tablename__ = "coupons"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text(), nullable=True)

    # Discount config
    discount_type = Column(String(20), nullable=False)  # percentage | fixed_amount
    discount_value = Column(Numeric(10, 2), nullable=False)  # 20 = 20% or $20
    max_discount_amount = Column(Numeric(10, 2), nullable=True)  # cap for percentage
    min_purchase_amount = Column(Numeric(10, 2), nullable=True)

    # Limits
    max_uses = Column(Integer, nullable=True)
    max_uses_per_user = Column(Integer, default=1, nullable=False)
    current_uses = Column(Integer, default=0, nullable=False)

    # Validity
    starts_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # Targeting
    applicable_plans = Column(JSONB, default=list, nullable=False)
    applicable_items = Column(JSONB, default=list, nullable=False)

    # FOMO
    is_flash_sale = Column(Boolean, default=False, nullable=False)
    flash_sale_ends_at = Column(DateTime(timezone=True), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class CouponUsage(Base):
    """Tracks coupon redemptions."""
    __tablename__ = "coupon_usages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    coupon_id = Column(UUID(as_uuid=True), ForeignKey("coupons.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    discount_applied = Column(Numeric(10, 2), nullable=False)
    original_amount = Column(Numeric(10, 2), nullable=False)
    final_amount = Column(Numeric(10, 2), nullable=False)

    used_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
