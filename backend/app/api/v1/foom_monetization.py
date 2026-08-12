"""FOOM Monetization API - Convert free users to paid + Enable user FOOM selling."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.domains.enterprise.foom_monetization import (
    PlatformMonetizationFOOM,
    UserFOOMEnablement,
    FOMOPerformanceOptimizer,
    NetworkEffectFOOM,
)

router = APIRouter(prefix="/api/v1/foom-monetization", tags=["foom-monetization"])


# ============================================================
# REQUEST/RESPONSE MODELS
# ============================================================


class UpgradeTriggerRequest(BaseModel):
    user_id: str
    segment: Optional[str] = None


class UpgradeTriggerResponse(BaseModel):
    user_segment: str
    trigger_type: str
    urgency_message: str
    offer: str
    psychology: str
    expected_conversion: float


class UserFOOMStrategyRequest(BaseModel):
    user_id: str
    product_name: str
    industry: str
    avg_deal_size: float


class UserFOOMStrategyResponse(BaseModel):
    product_name: str
    scarcity: List[dict]
    social_proof: dict
    urgency_templates: List[str]
    landing_page_foom: dict
    email_sequence: List[dict]
    social_posts: List[dict]


class ABTestRequest(BaseModel):
    user_id: str
    variants: List[dict]
    monthly_visitors: int
    avg_deal_size: float


class OptimizationResponse(BaseModel):
    current_conversion_rate: float
    optimized_conversion_rate: float
    recommendations: List[str]
    revenue_lift: dict


# ============================================================
# ENDPOINTS
# ============================================================


@router.post("/upgrade-trigger/{user_id}", response_model=UpgradeTriggerResponse)
def get_upgrade_trigger(user_id: str, db: Session = Depends(get_db)):
    """Get optimal upgrade trigger for user."""
    try:
        # Mock user data
        user_data = {
            "days_since_login": 3,
            "login_count_7d": 6,
            "feature_usage_pct": 0.65,
            "features_used": ["reporting", "analytics", "dashboards"],
            "feature_limit_hits_7d": 8,
            "is_paid": False,
            "days_until_trial_end": 999,
        }

        monetizer = PlatformMonetizationFOOM(db)
        trigger = monetizer.get_upgrade_trigger(user_id, user_data)

        if not trigger:
            raise HTTPException(status_code=404, detail="No upgrade trigger identified")

        return UpgradeTriggerResponse(
            user_segment=trigger.user_segment.value,
            trigger_type=trigger.trigger_type,
            urgency_message=trigger.urgency_message,
            offer=trigger.offer,
            psychology=trigger.psychology,
            expected_conversion=trigger.expected_conversion,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/user-foom-strategy", response_model=UserFOOMStrategyResponse)
def generate_user_foom_strategy(request: UserFOOMStrategyRequest, db: Session = Depends(get_db)):
    """Generate complete FOOM selling strategy for user's product."""
    try:
        product_data = {
            "product_name": request.product_name,
            "industry": request.industry,
            "avg_deal_size": request.avg_deal_size,
            "customer_count": 500,
            "top_customer": "Fortune 500 Company",
        }

        enabler = UserFOOMEnablement(db)
        strategy = enabler.generate_user_foom_strategy(request.user_id, product_data)

        return UserFOOMStrategyResponse(
            product_name=strategy["product_name"],
            scarcity=strategy["scarcity"],
            social_proof=strategy["social_proof"],
            urgency_templates=strategy["urgency_templates"],
            landing_page_foom=strategy["landing_page_foom"],
            email_sequence=strategy["email_sequence"],
            social_posts=strategy["social_posts"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/optimize-foom", response_model=OptimizationResponse)
def optimize_foom_strategy(request: ABTestRequest, db: Session = Depends(get_db)):
    """Get optimized FOOM strategy based on A/B tests."""
    try:
        ab_test_results = {
            "current_conversion_rate": 0.15,
            "variants": request.variants,
            "monthly_visitors": request.monthly_visitors,
            "avg_deal_size": request.avg_deal_size,
        }

        optimizer = FOMOPerformanceOptimizer(db)
        optimization = optimizer.optimize_foom_strategy(request.user_id, ab_test_results)

        return OptimizationResponse(
            current_conversion_rate=optimization["current_conversion_rate"],
            optimized_conversion_rate=optimization["optimized_conversion_rate"],
            recommendations=optimization["recommendations"],
            revenue_lift=optimization["expected_revenue_lift"],
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/referral-program/{user_id}")
def get_referral_foom(user_id: str, db: Session = Depends(get_db)):
    """Get FOOM-based referral program strategy."""
    try:
        user_metrics = {
            "base_ltv": 1000,
            "referral_rate": 0.15,
        }

        network_foom = NetworkEffectFOOM(db)
        referral_strategy = network_foom.generate_referral_foom(user_id, user_metrics)
        ltv_with_network = network_foom.calculate_lifetime_value_with_network(user_metrics)

        return {
            "referral_program": referral_strategy,
            "lifetime_value": ltv_with_network,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
