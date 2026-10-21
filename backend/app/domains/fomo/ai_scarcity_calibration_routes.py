"""Fase C: AI Scarcity Calibration Agent — API routes"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, Query

from app.core.deps import get_current_user
from app.domains.fomo.ai_scarcity_calibration_agent import AIScarcityCalibrationAgent
from app.domains.users.models import User

router = APIRouter(prefix="/fomo/ai/scarcity", tags=["fomo-ai-scarcity"])


@router.get("/calibrate-stock-display")
async def calibrate_stock_display(
    real_stock: Annotated[int, Query()],
    current_user: Annotated[User, Depends(get_current_user)],
    low_threshold: Annotated[int, Query()] = 20,
    critical_threshold: Annotated[int, Query()] = 5,
):
    """Decide what tier of scarcity messaging is truthfully justified by real stock"""
    return AIScarcityCalibrationAgent.calibrate_stock_display(real_stock, low_threshold, critical_threshold)


@router.get("/audit-message")
async def audit_scarcity_message(
    displayed_message: Annotated[str, Query()],
    real_stock: Annotated[int, Query()],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Check a scarcity message's numeric/urgency claims against real stock (compliance audit)"""
    return AIScarcityCalibrationAgent.audit_scarcity_message(displayed_message, real_stock)


@router.post("/calibrate-discount")
async def calibrate_discount(
    historical_data: Annotated[list[dict[str, float]], Body(description='[{"discount_percent": float, "conversion_rate": float}]')],
    current_user: Annotated[User, Depends(get_current_user)],
    min_discount: Annotated[int, Query()] = 10,
    max_discount: Annotated[int, Query()] = 50,
):
    """Recommend the revenue-maximizing discount % from historical elasticity data"""
    return AIScarcityCalibrationAgent.calibrate_discount(historical_data, min_discount, max_discount)


@router.post("/check-urgency-fatigue")
async def check_urgency_fatigue(
    campaign_history: Annotated[list[dict[str, Any]], Body(description='[{"sent_at": iso8601, "urgency_intensity": str, "conversion_rate": float}]')],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Detect whether urgency-intensity messaging is losing effect across campaigns"""
    return AIScarcityCalibrationAgent.check_urgency_fatigue(campaign_history)


@router.post("/ab-test-analysis")
async def run_ab_test_analysis(
    variant_low: Annotated[dict[str, int], Body(description='{"conversions": int, "visitors": int}')],
    variant_high: Annotated[dict[str, int], Body(description='{"conversions": int, "visitors": int}')],
    current_user: Annotated[User, Depends(get_current_user)],
    min_sample_size: Annotated[int, Query()] = 100,
):
    """Two-proportion z-test: does the high-intensity urgency variant significantly beat low-intensity?"""
    return AIScarcityCalibrationAgent.run_ab_test_analysis(variant_low, variant_high, min_sample_size)


@router.post("/full-calibration")
async def full_calibration(
    real_stock: Annotated[int, Query()],
    discount_historical_data: Annotated[list[dict[str, float]], Body()],
    campaign_history: Annotated[list[dict[str, Any]], Body()],
    current_user: Annotated[User, Depends(get_current_user)],
    ab_test_variants: Annotated[dict[str, dict[str, int]] | None, Body()] = None,
):
    """Run all four calibrations together and resolve a single final intensity recommendation"""
    return AIScarcityCalibrationAgent.full_calibration(
        real_stock, discount_historical_data, campaign_history, ab_test_variants
    )
