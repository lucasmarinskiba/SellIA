"""Fase C: AI Scarcity Calibration Agent — API routes"""

from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, Body, Query

from app.core.deps import get_current_user
from app.domains.fomo.ai_scarcity_calibration_agent import AIScarcityCalibrationAgent

router = APIRouter(prefix="/fomo/ai/scarcity", tags=["fomo-ai-scarcity"])


@router.get("/calibrate-stock-display")
async def calibrate_stock_display(
    real_stock: int = Query(...),
    low_threshold: int = Query(20),
    critical_threshold: int = Query(5),
    current_user=Depends(get_current_user),
):
    """Decide what tier of scarcity messaging is truthfully justified by real stock"""
    return AIScarcityCalibrationAgent.calibrate_stock_display(real_stock, low_threshold, critical_threshold)


@router.get("/audit-message")
async def audit_scarcity_message(
    displayed_message: str = Query(...),
    real_stock: int = Query(...),
    current_user=Depends(get_current_user),
):
    """Check a scarcity message's numeric/urgency claims against real stock (compliance audit)"""
    return AIScarcityCalibrationAgent.audit_scarcity_message(displayed_message, real_stock)


@router.post("/calibrate-discount")
async def calibrate_discount(
    historical_data: List[Dict[str, float]] = Body(
        ..., description='[{"discount_percent": float, "conversion_rate": float}]'
    ),
    min_discount: int = Query(10),
    max_discount: int = Query(50),
    current_user=Depends(get_current_user),
):
    """Recommend the revenue-maximizing discount % from historical elasticity data"""
    return AIScarcityCalibrationAgent.calibrate_discount(historical_data, min_discount, max_discount)


@router.post("/check-urgency-fatigue")
async def check_urgency_fatigue(
    campaign_history: List[Dict[str, Any]] = Body(
        ..., description='[{"sent_at": iso8601, "urgency_intensity": str, "conversion_rate": float}]'
    ),
    current_user=Depends(get_current_user),
):
    """Detect whether urgency-intensity messaging is losing effect across campaigns"""
    return AIScarcityCalibrationAgent.check_urgency_fatigue(campaign_history)


@router.post("/ab-test-analysis")
async def run_ab_test_analysis(
    variant_low: Dict[str, int] = Body(..., description='{"conversions": int, "visitors": int}'),
    variant_high: Dict[str, int] = Body(..., description='{"conversions": int, "visitors": int}'),
    min_sample_size: int = Query(100),
    current_user=Depends(get_current_user),
):
    """Two-proportion z-test: does the high-intensity urgency variant significantly beat low-intensity?"""
    return AIScarcityCalibrationAgent.run_ab_test_analysis(variant_low, variant_high, min_sample_size)


@router.post("/full-calibration")
async def full_calibration(
    real_stock: int = Query(...),
    discount_historical_data: List[Dict[str, float]] = Body(...),
    campaign_history: List[Dict[str, Any]] = Body(...),
    ab_test_variants: Optional[Dict[str, Dict[str, int]]] = Body(None),
    current_user=Depends(get_current_user),
):
    """Run all four calibrations together and resolve a single final intensity recommendation"""
    return AIScarcityCalibrationAgent.full_calibration(
        real_stock, discount_historical_data, campaign_history, ab_test_variants
    )
