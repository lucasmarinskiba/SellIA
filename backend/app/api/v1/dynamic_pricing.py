"""Dynamic pricing API endpoints."""

import logging
from datetime import UTC
from decimal import Decimal
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.pricing.pricing_service import (
    ABTestService,
    DiscountCodeService,
    DynamicPricingService,
    RevenueAnalyticsService,
)
from app.domains.users.models import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["pricing"])


class CalculatePriceRequest(BaseModel):
    location_id: UUID
    base_price: Decimal
    discount_code: str | None = None
    checkin_id: UUID | None = None


class LogPricingRequest(BaseModel):
    location_id: UUID
    order_id: str
    base_price: Decimal
    final_price: Decimal
    discount_code: str | None = None
    discount_amount: Decimal | None = None


class UpdateTierRequest(BaseModel):
    tier: str  # flagship, standard, discount
    tier_multiplier: Decimal
    peak_discount_pct: Decimal | None = None


class CreateDiscountRequest(BaseModel):
    code: str
    discount_value: Decimal
    discount_type: str = "percentage"
    valid_days: int = 30
    usage_limit: int | None = None


class CreateABTestRequest(BaseModel):
    test_name: str
    control_price: Decimal
    variant_a_price: Decimal | None = None
    variant_b_price: Decimal | None = None
    test_duration_days: int = 14


@router.post("/pricing/calculate")
async def calculate_price(
    request: CalculatePriceRequest,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Calculate price with dynamic adjustments."""
    try:
        result = DynamicPricingService.calculate_price(
            location_id=request.location_id,
            base_price=request.base_price,
            discount_code=request.discount_code,
            checkin_id=request.checkin_id,
            db=db,
        )
        return result
    except Exception as e:
        logger.exception("calculate_price: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/pricing/log-transaction")
async def log_pricing_transaction(
    request: LogPricingRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Log pricing transaction."""
    try:
        result = DynamicPricingService.log_pricing_transaction(
            location_id=request.location_id,
            business_id=UUID(
                "00000000-0000-0000-0000-000000000000"
            ),  # TODO: from location
            order_id=request.order_id,
            base_price=request.base_price,
            final_price=request.final_price,
            discount_code=request.discount_code,
            discount_amount=request.discount_amount,
            db=db,
        )
        return result
    except Exception as e:
        logger.exception("log_pricing_transaction: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/pricing-tier")
async def get_pricing_tier(
    location_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get pricing tier config."""
    try:
        result = DynamicPricingService.get_location_pricing_tier(location_id, db)
        return result
    except Exception as e:
        logger.exception("get_pricing_tier: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/locations/{location_id}/pricing-tier")
async def update_pricing_tier(
    location_id: UUID,
    request: UpdateTierRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Update pricing tier."""
    try:
        result = DynamicPricingService.update_pricing_tier(
            location_id=location_id,
            business_id=UUID("00000000-0000-0000-0000-000000000000"),
            tier=request.tier,
            tier_multiplier=request.tier_multiplier,
            peak_discount_pct=request.peak_discount_pct,
            db=db,
        )
        return result
    except Exception as e:
        logger.exception("update_pricing_tier: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/locations/{location_id}/discount-codes")
async def create_discount_code(
    location_id: UUID,
    request: CreateDiscountRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create location-specific discount code."""
    try:
        result = DiscountCodeService.create_discount_code(
            location_id=location_id,
            business_id=UUID("00000000-0000-0000-0000-000000000000"),
            code=request.code,
            discount_value=request.discount_value,
            discount_type=request.discount_type,
            valid_days=request.valid_days,
            usage_limit=request.usage_limit,
            db=db,
        )
        return result
    except Exception as e:
        logger.exception("create_discount_code: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/discount-codes/{code}/validate")
async def validate_discount(
    code: str,
    location_id: Annotated[UUID, Query()],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Validate discount code."""
    try:
        result = DiscountCodeService.validate_discount_code(code, location_id, db)
        return result
    except Exception as e:
        logger.exception("validate_discount: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/locations/{location_id}/ab-tests")
async def create_ab_test(
    location_id: UUID,
    request: CreateABTestRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Create A/B test for pricing."""
    try:
        result = ABTestService.create_ab_test(
            location_id=location_id,
            business_id=UUID("00000000-0000-0000-0000-000000000000"),
            test_name=request.test_name,
            control_price=request.control_price,
            variant_a_price=request.variant_a_price,
            variant_b_price=request.variant_b_price,
            test_duration_days=request.test_duration_days,
            db=db,
        )
        return result
    except Exception as e:
        logger.exception("create_ab_test: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/ab-tests/{test_id}/results")
async def get_ab_test_results(
    test_id: UUID,
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get A/B test results."""
    try:
        result = ABTestService.get_test_results(test_id, db)
        return result
    except Exception as e:
        logger.exception("get_ab_test_results: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/revenue-impact")
async def get_revenue_impact(
    location_id: UUID,
    date: Annotated[str, Query()],  # YYYY-MM-DD
    db: Annotated[Session, Depends(get_db)],
) -> dict:
    """Get revenue impact for date."""
    try:
        result = RevenueAnalyticsService.aggregate_daily_impact(
            location_id=location_id,
            business_id=UUID("00000000-0000-0000-0000-000000000000"),
            date=date,
            db=db,
        )
        return result
    except Exception as e:
        logger.exception("get_revenue_impact: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/pricing-analytics")
async def get_pricing_analytics(
    location_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    days: Annotated[int, Query(ge=1, le=365)] = 30,
) -> dict:
    """Get pricing analytics for location."""
    try:
        from datetime import datetime, timedelta

        from app.domains.pricing.pricing_models import LocationRevenueImpact

        cutoff = datetime.now(UTC) - timedelta(days=days)
        cutoff_str = cutoff.strftime("%Y-%m-%d")

        impacts = (
            db.query(LocationRevenueImpact)
            .filter(
                LocationRevenueImpact.location_id == location_id,
                LocationRevenueImpact.date >= cutoff_str,
            )
            .order_by(LocationRevenueImpact.date.desc())
            .all()
        )

        total_base = sum(float(i.total_base_revenue) for i in impacts)
        total_final = sum(float(i.total_final_revenue) for i in impacts)
        total_discounts = sum(float(i.total_discounts_given) for i in impacts)

        impact_data = [
            {
                "date": i.date,
                "transactions": i.transactions_count,
                "base_revenue": float(i.total_base_revenue),
                "final_revenue": float(i.total_final_revenue),
                "discounts": float(i.total_discounts_given),
                "impact": float(i.revenue_delta),
            }
            for i in impacts
        ]

        return {
            "location_id": str(location_id),
            "period_days": days,
            "total_transactions": sum(i.transactions_count for i in impacts),
            "total_base_revenue": total_base,
            "total_final_revenue": total_final,
            "total_discounts_given": total_discounts,
            "net_revenue_impact": total_final - total_base,
            "impact_pct": ((total_final - total_base) / max(total_base, 0.01)) * 100,
            "daily_breakdown": impact_data,
        }
    except Exception as e:
        logger.exception("get_pricing_analytics: error inesperado")
        raise HTTPException(status_code=400, detail=str(e))
