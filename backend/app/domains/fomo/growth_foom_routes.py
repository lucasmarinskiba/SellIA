"""
Growth FOOM Routes: Acquisition channels endpoint
"""

import re

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.fomo.growth_foom import (
    SeoFOOMService,
    ViralLoopsService,
    CaseStudyFOOMService,
    PressAndPRService,
    ProductLedGrowthService,
    PartnershipFOOMService,
    ViralMechanicsService,
    BrandBuildingService,
)

router = APIRouter(prefix="/fomo/growth", tags=["growth-foom"])


def _parse_mau(expected_mau) -> int:
    """expected_mau is a display string like '+2000/month' in growth_foom.py's
    partnership data — extract the leading number for aggregation, 0 if absent."""
    if isinstance(expected_mau, (int, float)):
        return int(expected_mau)
    if isinstance(expected_mau, str):
        match = re.search(r"\d+", expected_mau)
        if match:
            return int(match.group(0))
    return 0


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# SEO Endpoints
@router.get("/seo/content-calendar")
async def get_seo_content_calendar(
    days: int = Query(90, ge=30, le=365),
):
    """Get SEO content calendar (90-day plan)"""
    plan = await SeoFOOMService.generate_seo_content_calendar(days)
    return {
        "plan": plan,
        "total_pieces": len(plan),
        "estimated_traffic": f"+30-50% organic traffic",
        "timeline": f"{days} days",
    }


@router.get("/seo/serp-optimization/{content_type}")
async def get_serp_optimization(content_type: str):
    """Get SERP feature optimization tips"""
    optimization = await SeoFOOMService.optimize_for_serp_features(content_type)
    return {
        "content_type": content_type,
        "optimization": optimization,
        "expected_ctr_improvement": "+150-300%",
    }


# Viral Loops Endpoints
@router.get("/viral/referral-program")
async def get_referral_program():
    """Get referral program details"""
    program = await ViralLoopsService.create_referral_program()
    return program


@router.get("/viral/community-program")
async def get_community_program():
    """Get community building strategy"""
    program = await ViralLoopsService.create_community_program()
    return program


@router.get("/viral/waitlist")
async def get_waitlist_program():
    """Get waitlist FOOM mechanics"""
    waitlist = await ViralLoopsService.create_waitlist_fomo()
    return waitlist


@router.get("/viral/mechanics")
async def get_viral_mechanics():
    """Get viral coefficient mechanics"""
    mechanics = await ViralMechanicsService.create_viral_mechanics()
    return mechanics


# Case Study Endpoints
@router.get("/case-studies/generate")
async def generate_case_study_template(
    business_name: str,
    cr_improvement_percent: float,
    revenue_improvement_percent: float,
):
    """Template for converting user success to case study"""
    before_metrics = {
        "business_name": business_name,
        "conversion_rate": 2.0,
        "monthly_revenue": 5000,
        "aov": 100,
    }
    after_metrics = {
        "conversion_rate": 2.0 * (1 + cr_improvement_percent / 100),
        "monthly_revenue": 5000 * (1 + revenue_improvement_percent / 100),
        "aov": 100 * (1 + revenue_improvement_percent / 100),
    }

    case_study = await CaseStudyFOOMService.generate_case_study_from_user(
        None,
        before_metrics,
        after_metrics,
        "ecommerce",
        "small",
    )
    return case_study


# Press & PR Endpoints
@router.get("/press/release-template/{news_type}")
async def get_press_release_template(news_type: str):
    """Get press release template"""
    template = await PressAndPRService.generate_press_release(
        news_type,
        {"milestone_number": "15,000", "milestone_revenue": "2.3"},
    )
    return template


@router.get("/press/influencer-seeding")
async def get_influencer_seeding():
    """Get influencer seeding program"""
    program = await PressAndPRService.create_influencer_seeding()
    return program


# Product-Led Growth Endpoints
@router.get("/plg/free-trial-optimization")
async def get_trial_optimization():
    """Get free trial optimization strategy"""
    strategy = await ProductLedGrowthService.optimize_free_trial_foom()
    return strategy


@router.get("/plg/feature-gates")
async def get_feature_gates():
    """Get feature gate configuration"""
    gates = await ProductLedGrowthService.create_feature_gates_for_fomo()
    return gates


# Partnership Endpoints
@router.get("/partnerships/list")
async def get_partnerships():
    """List all partnership opportunities"""
    partnerships = await PartnershipFOOMService.create_partnerships()
    total_mau = sum(_parse_mau(p.get("expected_mau", 0)) for p in partnerships)
    return {
        "partnerships": partnerships,
        "total_expected_mau": total_mau,
        "estimated_contribution": "30-40% of total growth",
    }


# Brand Building Endpoints
@router.get("/brand/thought-leadership")
async def get_thought_leadership():
    """Get thought leadership strategy"""
    strategy = await BrandBuildingService.create_thought_leadership()
    return strategy


# Summary Dashboard
@router.get("/dashboard/growth-summary")
async def get_growth_summary():
    """Get all acquisition channels summary"""

    seo_plan = await SeoFOOMService.generate_seo_content_calendar()
    referral = await ViralLoopsService.create_referral_program()
    community = await ViralLoopsService.create_community_program()
    trial = await ProductLedGrowthService.optimize_free_trial_foom()
    partnerships = await PartnershipFOOMService.create_partnerships()
    viral = await ViralMechanicsService.create_viral_mechanics()
    brand = await BrandBuildingService.create_thought_leadership()

    return {
        "acquisition_channels": {
            "organic_seo": {
                "content_pieces": len(seo_plan),
                "estimated_mau": "1000-2000",
                "timeline": "60-90 days to see results",
            },
            "referral_viral": {
                "viral_coefficient": referral["viral_coefficient"],
                "payback_period_days": referral["payback_period_days"],
                "estimated_mau": "3000-5000",
            },
            "community": {
                "channels": 5,
                "estimated_engaged_users": "500+",
                "ugc_value": "$100K+/year",
            },
            "product_led_growth": {
                "trial_to_paid_percent": "15-20%",
                "customer_acquisition_cost": "$50-75",
                "ltv": "$1500+",
            },
            "partnerships": {
                "total_channels": len(partnerships),
                "estimated_mau": sum(_parse_mau(p.get("expected_mau", 0)) for p in partnerships),
            },
            "influencer_seeding": {
                "estimated_mau": "2000-3000",
                "content_leverage": "5x impressions",
            },
            "viral_mechanics": {
                "k_factor": viral["k_factor"],
                "estimated_mau": "1500-2500",
            },
            "brand_building": {
                "channels": len(brand["channels"]),
                "target_reach": "1M+ annually",
            },
        },
        "total_estimated_mau": "12000-20000",
        "blended_cac": "$40-60",
        "payback_period_avg": "5 months",
        "year_1_growth_target": "200% MAU",
    }
