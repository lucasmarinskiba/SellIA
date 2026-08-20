"""Dynamic pricing per location — location-based pricing + flash sales."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from decimal import Decimal

from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Integer, Enum as SQLEnum, Index, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class PricingTier(str, Enum):
    """Location pricing tier."""
    FLAGSHIP = "flagship"  # Premium location, higher margins
    STANDARD = "standard"  # Regular satellite location
    DISCOUNT = "discount"  # Budget/promotional location


class DiscountTrigger(str, Enum):
    """When to apply discount."""
    PEAK_HOURS = "peak_hours"  # During high-traffic periods
    OFF_PEAK = "off_peak"  # During low-traffic periods
    BULK_PURCHASE = "bulk_purchase"  # Multiple items
    LOYALTY = "loyalty"  # Returning customer
    MANUAL = "manual"  # Staff-applied


class TestVariant(str, Enum):
    """A/B test variants."""
    CONTROL = "control"  # Original price
    VARIANT_A = "variant_a"  # Lower price
    VARIANT_B = "variant_b"  # Higher price
    VARIANT_C = "variant_c"  # Different offer


class LocationPricingTier(Base):
    """Base pricing tier per location."""
    __tablename__ = "location_pricing_tiers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Tier configuration
    tier = Column(SQLEnum(PricingTier), default=PricingTier.STANDARD)
    tier_multiplier = Column(Decimal(3, 2), default=Decimal("1.00"))  # 1.2 = +20%, 0.8 = -20%

    # Peak hours definition
    peak_hours_start = Column(Integer, default=12)  # Hour 0-23
    peak_hours_end = Column(Integer, default=18)
    peak_days = Column(JSONB, default=[1, 2, 3, 4, 5])  # 0=Monday, 6=Sunday

    # Discount config
    peak_discount_pct = Column(Decimal(5, 2), default=0)  # 0-100
    off_peak_discount_pct = Column(Decimal(5, 2), default=0)

    # Flags
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index("idx_location_tier", "location_id", "is_active"),
    )


class LocationDiscountCode(Base):
    """Discount codes tied to specific location."""
    __tablename__ = "location_discount_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Code details
    code = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(String(255), nullable=True)

    # Discount value
    discount_type = Column(String(20), default="percentage")  # percentage, fixed
    discount_value = Column(Decimal(8, 2), nullable=False)  # % or $ amount

    # Applicability
    min_order_value = Column(Decimal(10, 2), nullable=True)
    max_discount_cap = Column(Decimal(10, 2), nullable=True)  # Max discount amount

    # Validity
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)
    usage_limit = Column(Integer, nullable=True)  # NULL = unlimited
    current_usage = Column(Integer, default=0)

    # Trigger
    trigger = Column(SQLEnum(DiscountTrigger), default=DiscountTrigger.MANUAL)
    trigger_condition = Column(String(255), nullable=True)  # e.g., "checkin_at_location"

    # Flags
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index("idx_code_active", "code", "is_active"),
        Index("idx_location_discount", "location_id", "is_active"),
    )


class PricingABTest(Base):
    """A/B test for pricing variants."""
    __tablename__ = "pricing_ab_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Test config
    test_name = Column(String(255), nullable=False)
    product_id = Column(String(255), nullable=True)  # NULL = all products

    # Variants
    control_price = Column(Decimal(10, 2), nullable=False)
    variant_a_price = Column(Decimal(10, 2), nullable=True)
    variant_b_price = Column(Decimal(10, 2), nullable=True)
    variant_c_price = Column(Decimal(10, 2), nullable=True)

    # Traffic split
    control_traffic_pct = Column(Integer, default=25)
    variant_a_traffic_pct = Column(Integer, default=25)
    variant_b_traffic_pct = Column(Integer, default=25)
    variant_c_traffic_pct = Column(Integer, default=25)

    # Test window
    started_at = Column(DateTime(timezone=True), nullable=False)
    ended_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)

    # Results (auto-calculated)
    control_conversions = Column(Integer, default=0)
    control_revenue = Column(Decimal(12, 2), default=0)
    variant_a_conversions = Column(Integer, default=0)
    variant_a_revenue = Column(Decimal(12, 2), default=0)
    variant_b_conversions = Column(Integer, default=0)
    variant_b_revenue = Column(Decimal(12, 2), default=0)
    variant_c_conversions = Column(Integer, default=0)
    variant_c_revenue = Column(Decimal(12, 2), default=0)

    # Winner
    winning_variant = Column(SQLEnum(TestVariant), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index("idx_location_test", "location_id", "is_active"),
    )


class PricingTransaction(Base):
    """Log pricing decisions per transaction."""
    __tablename__ = "pricing_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Order/transaction context
    order_id = Column(String(255), nullable=False)
    checkin_id = Column(UUID(as_uuid=True), nullable=True)  # If from location visit

    # Pricing applied
    base_price = Column(Decimal(10, 2), nullable=False)
    location_tier_multiplier = Column(Decimal(3, 2), default=Decimal("1.00"))
    tier_adjusted_price = Column(Decimal(10, 2), nullable=False)

    # Discount applied
    discount_code = Column(String(50), nullable=True)
    discount_amount = Column(Decimal(10, 2), default=0)
    final_price = Column(Decimal(10, 2), nullable=False)

    # Context
    applied_peak_discount = Column(Boolean, default=False)
    applied_ab_test = Column(UUID(as_uuid=True), nullable=True)
    test_variant = Column(SQLEnum(TestVariant), nullable=True)

    # Revenue tracking
    original_margin = Column(Decimal(10, 2), nullable=True)
    final_margin = Column(Decimal(10, 2), nullable=True)
    margin_impact = Column(Decimal(10, 2), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_location_transaction", "location_id", "created_at"),
        Index("idx_order_transaction", "order_id"),
    )


class LocationRevenueImpact(Base):
    """Daily revenue impact summary per location."""
    __tablename__ = "location_revenue_impact"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id", ondelete="CASCADE"), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)

    # Date
    date = Column(String(10), nullable=False)  # YYYY-MM-DD

    # Volume
    transactions_count = Column(Integer, default=0)
    avg_base_price = Column(Decimal(10, 2), default=0)
    avg_final_price = Column(Decimal(10, 2), default=0)

    # Revenue impact
    total_base_revenue = Column(Decimal(12, 2), default=0)
    total_discounts_given = Column(Decimal(12, 2), default=0)
    total_final_revenue = Column(Decimal(12, 2), default=0)
    revenue_delta = Column(Decimal(12, 2), default=0)  # final - base

    # Margin impact
    total_base_margin = Column(Decimal(12, 2), default=0)
    total_final_margin = Column(Decimal(12, 2), default=0)
    margin_impact = Column(Decimal(12, 2), default=0)

    # Discounts breakdown
    peak_hour_discounts_count = Column(Integer, default=0)
    code_discounts_count = Column(Integer, default=0)
    tier_adjustments_count = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    location = relationship("Location", foreign_keys=[location_id])

    __table_args__ = (
        Index("idx_location_date", "location_id", "date"),
    )
