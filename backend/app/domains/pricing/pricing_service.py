"""Dynamic pricing service — location-based + flash sales."""

import logging
import random
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional
from decimal import Decimal

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.pricing.pricing_models import (
    LocationPricingTier, LocationDiscountCode, PricingABTest, PricingTransaction,
    LocationRevenueImpact, PricingTier, TestVariant, DiscountTrigger
)

logger = logging.getLogger(__name__)


class DynamicPricingService:
    """Calculate prices based on location tier + peak hours + discounts."""

    @staticmethod
    def calculate_price(
        location_id: UUID,
        base_price: Decimal,
        discount_code: str = None,
        checkin_id: UUID = None,
        db: Session = None
    ) -> dict:
        """Calculate final price with all adjustments.

        Returns: {final_price, tier_adjusted, discount_applied, peak_hour_discount, test_variant}
        """
        if not db:
            raise ValueError("Database session required")

        # Get location tier
        tier = db.query(LocationPricingTier).filter(
            LocationPricingTier.location_id == location_id,
            LocationPricingTier.is_active == True
        ).first()

        tier_multiplier = Decimal("1.00")
        if tier:
            tier_multiplier = tier.tier_multiplier

        # Apply tier adjustment
        tier_adjusted_price = base_price * tier_multiplier

        # Check for peak hour discount
        peak_discount = Decimal("0")
        applied_peak = False

        if tier:
            now = datetime.now(timezone.utc)
            current_hour = now.hour
            current_day = now.weekday()

            is_peak = (
                current_hour >= tier.peak_hours_start
                and current_hour < tier.peak_hours_end
                and current_day in tier.peak_days
            )

            if is_peak and tier.peak_discount_pct > 0:
                peak_discount = tier_adjusted_price * (tier.peak_discount_pct / Decimal("100"))
                applied_peak = True

        price_after_peak = tier_adjusted_price - peak_discount

        # Check for discount code
        code_discount = Decimal("0")
        code_used = None

        if discount_code:
            code_obj = db.query(LocationDiscountCode).filter(
                LocationDiscountCode.code == discount_code,
                LocationDiscountCode.location_id == location_id,
                LocationDiscountCode.is_active == True
            ).first()

            if code_obj:
                now = datetime.now(timezone.utc)
                if code_obj.valid_from <= now <= code_obj.valid_until:
                    if code_obj.usage_limit is None or code_obj.current_usage < code_obj.usage_limit:
                        if code_obj.discount_type == "percentage":
                            code_discount = price_after_peak * (code_obj.discount_value / Decimal("100"))
                        else:
                            code_discount = code_obj.discount_value

                        if code_obj.max_discount_cap:
                            code_discount = min(code_discount, code_obj.max_discount_cap)

                        code_used = code_obj.code
                        code_obj.current_usage += 1

        final_price = max(price_after_peak - code_discount, Decimal("0"))

        # Check for A/B test
        test_variant = None
        test_id = None

        active_test = db.query(PricingABTest).filter(
            PricingABTest.location_id == location_id,
            PricingABTest.is_active == True
        ).first()

        if active_test:
            rand = random.randint(1, 100)
            if rand <= active_test.control_traffic_pct:
                test_variant = TestVariant.CONTROL
                final_price = active_test.control_price
            elif rand <= active_test.control_traffic_pct + active_test.variant_a_traffic_pct:
                test_variant = TestVariant.VARIANT_A
                final_price = active_test.variant_a_price or final_price
            elif rand <= active_test.control_traffic_pct + active_test.variant_a_traffic_pct + active_test.variant_b_traffic_pct:
                test_variant = TestVariant.VARIANT_B
                final_price = active_test.variant_b_price or final_price
            else:
                test_variant = TestVariant.VARIANT_C
                final_price = active_test.variant_c_price or final_price

            test_id = active_test.id

        db.commit()

        logger.info(f"Price calculated: location={location_id} base={base_price} final={final_price}")

        return {
            "location_id": str(location_id),
            "base_price": float(base_price),
            "tier_adjusted_price": float(tier_adjusted_price),
            "tier_multiplier": float(tier_multiplier),
            "peak_discount": float(peak_discount) if applied_peak else 0,
            "code_discount": float(code_discount) if code_used else 0,
            "discount_code_used": code_used,
            "final_price": float(final_price),
            "test_variant": test_variant.value if test_variant else None,
            "total_discount": float(base_price - final_price)
        }

    @staticmethod
    def log_pricing_transaction(
        location_id: UUID,
        business_id: UUID,
        order_id: str,
        base_price: Decimal,
        final_price: Decimal,
        discount_code: str = None,
        discount_amount: Decimal = None,
        applied_peak: bool = False,
        test_variant: str = None,
        test_id: UUID = None,
        checkin_id: UUID = None,
        db: Session = None
    ) -> dict:
        """Log pricing transaction for analytics."""
        if not db:
            raise ValueError("Database session required")

        tier_multiplier = Decimal("1.00")
        tier = db.query(LocationPricingTier).filter(
            LocationPricingTier.location_id == location_id,
            LocationPricingTier.is_active == True
        ).first()

        if tier:
            tier_multiplier = tier.tier_multiplier

        tier_adjusted_price = base_price * tier_multiplier

        transaction = PricingTransaction(
            location_id=location_id,
            business_id=business_id,
            order_id=order_id,
            checkin_id=checkin_id,
            base_price=base_price,
            location_tier_multiplier=tier_multiplier,
            tier_adjusted_price=tier_adjusted_price,
            discount_code=discount_code,
            discount_amount=discount_amount or Decimal("0"),
            final_price=final_price,
            applied_peak_discount=applied_peak,
            applied_ab_test=test_id,
            test_variant=TestVariant[test_variant.upper()] if test_variant else None
        )

        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        logger.info(f"Pricing transaction logged: {order_id}")

        return {
            "transaction_id": str(transaction.id),
            "base_price": float(base_price),
            "final_price": float(final_price),
            "discount_applied": float(discount_amount or 0)
        }

    @staticmethod
    def get_location_pricing_tier(
        location_id: UUID,
        db: Session
    ) -> dict:
        """Get pricing tier config for location."""
        tier = db.query(LocationPricingTier).filter(
            LocationPricingTier.location_id == location_id
        ).first()

        if not tier:
            return {"configured": False}

        return {
            "configured": True,
            "location_id": str(location_id),
            "tier": tier.tier.value,
            "tier_multiplier": float(tier.tier_multiplier),
            "peak_hours": f"{tier.peak_hours_start}:00-{tier.peak_hours_end}:00",
            "peak_discount_pct": float(tier.peak_discount_pct),
            "off_peak_discount_pct": float(tier.off_peak_discount_pct)
        }

    @staticmethod
    def update_pricing_tier(
        location_id: UUID,
        business_id: UUID,
        tier: str,
        tier_multiplier: Decimal,
        peak_discount_pct: Decimal = None,
        db: Session = None
    ) -> dict:
        """Update location pricing tier."""
        if not db:
            raise ValueError("Database session required")

        existing = db.query(LocationPricingTier).filter(
            LocationPricingTier.location_id == location_id
        ).first()

        if existing:
            existing.tier = PricingTier[tier.upper()]
            existing.tier_multiplier = tier_multiplier
            if peak_discount_pct is not None:
                existing.peak_discount_pct = peak_discount_pct
        else:
            existing = LocationPricingTier(
                location_id=location_id,
                business_id=business_id,
                tier=PricingTier[tier.upper()],
                tier_multiplier=tier_multiplier,
                peak_discount_pct=peak_discount_pct or Decimal("0")
            )
            db.add(existing)

        db.commit()
        db.refresh(existing)

        logger.info(f"Pricing tier updated: {location_id} = {tier}")

        return {
            "updated": True,
            "location_id": str(location_id),
            "tier": existing.tier.value,
            "multiplier": float(existing.tier_multiplier)
        }


class DiscountCodeService:
    """Manage location-based discount codes."""

    @staticmethod
    def create_discount_code(
        location_id: UUID,
        business_id: UUID,
        code: str,
        discount_value: Decimal,
        discount_type: str = "percentage",
        valid_days: int = 30,
        usage_limit: int = None,
        db: Session = None
    ) -> dict:
        """Create location-specific discount code."""
        if not db:
            raise ValueError("Database session required")

        now = datetime.now(timezone.utc)
        valid_until = now + timedelta(days=valid_days)

        discount_code = LocationDiscountCode(
            location_id=location_id,
            business_id=business_id,
            code=code,
            discount_type=discount_type,
            discount_value=discount_value,
            valid_from=now,
            valid_until=valid_until,
            usage_limit=usage_limit
        )

        db.add(discount_code)
        db.commit()
        db.refresh(discount_code)

        logger.info(f"Discount code created: {code} for location {location_id}")

        return {
            "code": code,
            "discount_value": float(discount_value),
            "discount_type": discount_type,
            "valid_until": valid_until.isoformat(),
            "usage_limit": usage_limit
        }

    @staticmethod
    def validate_discount_code(
        code: str,
        location_id: UUID,
        db: Session
    ) -> dict:
        """Validate discount code for location."""
        discount = db.query(LocationDiscountCode).filter(
            LocationDiscountCode.code == code,
            LocationDiscountCode.location_id == location_id,
            LocationDiscountCode.is_active == True
        ).first()

        if not discount:
            return {"valid": False, "reason": "Code not found"}

        now = datetime.now(timezone.utc)

        if now < discount.valid_from:
            return {"valid": False, "reason": "Code not yet active"}

        if now > discount.valid_until:
            return {"valid": False, "reason": "Code expired"}

        if discount.usage_limit and discount.current_usage >= discount.usage_limit:
            return {"valid": False, "reason": "Usage limit reached"}

        return {
            "valid": True,
            "discount_value": float(discount.discount_value),
            "discount_type": discount.discount_type,
            "remaining_uses": discount.usage_limit - discount.current_usage if discount.usage_limit else None
        }


class ABTestService:
    """Manage A/B tests for pricing."""

    @staticmethod
    def create_ab_test(
        location_id: UUID,
        business_id: UUID,
        test_name: str,
        control_price: Decimal,
        variant_a_price: Decimal = None,
        variant_b_price: Decimal = None,
        test_duration_days: int = 14,
        db: Session = None
    ) -> dict:
        """Create A/B test for pricing variant."""
        if not db:
            raise ValueError("Database session required")

        test = PricingABTest(
            location_id=location_id,
            business_id=business_id,
            test_name=test_name,
            control_price=control_price,
            variant_a_price=variant_a_price,
            variant_b_price=variant_b_price,
            started_at=datetime.now(timezone.utc),
            ended_at=datetime.now(timezone.utc) + timedelta(days=test_duration_days)
        )

        db.add(test)
        db.commit()
        db.refresh(test)

        logger.info(f"A/B test created: {test_name} for location {location_id}")

        return {
            "test_id": str(test.id),
            "test_name": test_name,
            "control_price": float(control_price),
            "variant_a_price": float(variant_a_price) if variant_a_price else None,
            "variant_b_price": float(variant_b_price) if variant_b_price else None,
            "duration_days": test_duration_days
        }

    @staticmethod
    def get_test_results(
        test_id: UUID,
        db: Session
    ) -> dict:
        """Get A/B test results + winner."""
        test = db.query(PricingABTest).filter(PricingABTest.id == test_id).first()

        if not test:
            raise ValueError(f"Test {test_id} not found")

        # Calculate conversion rates
        control_conversion_rate = (test.control_conversions / max(test.control_conversions + 10, 1)) * 100
        variant_a_rate = (test.variant_a_conversions / max(test.variant_a_conversions + 10, 1)) * 100 if test.variant_a_conversions else 0
        variant_b_rate = (test.variant_b_conversions / max(test.variant_b_conversions + 10, 1)) * 100 if test.variant_b_conversions else 0

        # Calculate revenue per conversion
        control_rev_per_conv = float(test.control_revenue) / max(test.control_conversions, 1) if test.control_conversions else 0
        variant_a_rev_per_conv = float(test.variant_a_revenue) / max(test.variant_a_conversions, 1) if test.variant_a_conversions else 0

        # Simple winner: highest revenue per conversion
        best_variant = TestVariant.CONTROL
        best_revenue = control_rev_per_conv

        if variant_a_rev_per_conv > best_revenue:
            best_variant = TestVariant.VARIANT_A
            best_revenue = variant_a_rev_per_conv
        if variant_b_rate > best_revenue:
            best_variant = TestVariant.VARIANT_B

        return {
            "test_name": test.test_name,
            "control": {
                "price": float(test.control_price),
                "conversions": test.control_conversions,
                "revenue": float(test.control_revenue),
                "rev_per_conversion": control_rev_per_conv
            },
            "variant_a": {
                "price": float(test.variant_a_price) if test.variant_a_price else None,
                "conversions": test.variant_a_conversions,
                "revenue": float(test.variant_a_revenue),
                "rev_per_conversion": variant_a_rev_per_conv
            },
            "winning_variant": best_variant.value,
            "revenue_improvement": ((best_revenue - control_rev_per_conv) / max(control_rev_per_conv, 0.01)) * 100
        }


class RevenueAnalyticsService:
    """Track revenue impact of dynamic pricing."""

    @staticmethod
    def aggregate_daily_impact(
        location_id: UUID,
        business_id: UUID,
        date: str,
        db: Session = None
    ) -> dict:
        """Aggregate pricing impact for day."""
        if not db:
            raise ValueError("Database session required")

        from datetime import datetime as dt

        date_start = dt.fromisoformat(f"{date}T00:00:00+00:00")
        date_end = date_start + timedelta(days=1)

        transactions = db.query(PricingTransaction).filter(
            PricingTransaction.location_id == location_id,
            PricingTransaction.created_at >= date_start,
            PricingTransaction.created_at < date_end
        ).all()

        if not transactions:
            return {"aggregated": False, "reason": "No transactions"}

        total_base = sum(float(t.base_price) for t in transactions)
        total_final = sum(float(t.final_price) for t in transactions)
        total_discounts = sum(float(t.discount_amount) for t in transactions)

        revenue_delta = total_final - total_base

        # Create/update impact record
        existing = db.query(LocationRevenueImpact).filter(
            LocationRevenueImpact.location_id == location_id,
            LocationRevenueImpact.date == date
        ).first()

        if existing:
            existing.transactions_count = len(transactions)
            existing.total_base_revenue = Decimal(str(total_base))
            existing.total_final_revenue = Decimal(str(total_final))
            existing.total_discounts_given = Decimal(str(total_discounts))
            existing.revenue_delta = Decimal(str(revenue_delta))
        else:
            existing = LocationRevenueImpact(
                location_id=location_id,
                business_id=business_id,
                date=date,
                transactions_count=len(transactions),
                total_base_revenue=Decimal(str(total_base)),
                total_final_revenue=Decimal(str(total_final)),
                total_discounts_given=Decimal(str(total_discounts)),
                revenue_delta=Decimal(str(revenue_delta))
            )
            db.add(existing)

        db.commit()

        logger.info(f"Daily impact aggregated: {location_id} on {date} revenue_delta={revenue_delta}")

        return {
            "date": date,
            "transactions": len(transactions),
            "base_revenue": total_base,
            "final_revenue": total_final,
            "total_discounts": total_discounts,
            "revenue_impact": revenue_delta,
            "impact_pct": (revenue_delta / max(total_base, 0.01)) * 100
        }
