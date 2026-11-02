"""Phases 14-17: Advanced analytics, automation, and retention."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import logging

from app.core.database import get_db
from app.core.deps import get_current_user, resolve_business_id
from app.domains.analytics.sales_dashboard import TimeRange, assert_owner, build_channel_ranking
from app.domains.automation.performance_optimizer import PerformanceOptimizer
from app.domains.retention.retention_engine import RetentionEngine
from app.domains.users.models import User

router = APIRouter(tags=["advanced-automation"])
logger = logging.getLogger(__name__)

optimizer = PerformanceOptimizer()
retention_engine = RetentionEngine()


# ============================================================
# Phase 14: Analytics Dashboard
# ============================================================


@router.get("/analytics/channel-rankings/{seller_id}")
async def get_channel_rankings(
    seller_id: str,
    time_range: TimeRange = Query("month", description="today, week, month, quarter or year"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Channels ranked by sales from the caller's own deals. Another account's id is refused."""

    assert_owner(seller_id, current_user)
    business_id = await resolve_business_id(db, current_user)
    channels = await build_channel_ranking(db, business_id, time_range)

    return {"status": "success", "seller_id": str(current_user.id), "time_range": time_range, "channels": channels}


# ============================================================
# Phase 15: Performance Optimization
# ============================================================


@router.post("/optimization/recommend-strategy")
async def recommend_optimization_strategy(
    seller_id: str = Query(...),
    roi: float = Query(2.0),
    growth_rate: float = Query(0.10),
) -> Dict[str, Any]:
    """Recommend optimization strategy based on performance."""

    try:
        metrics = {"roi": roi, "growth_rate": growth_rate, "market_position": "competitive"}
        strategy = optimizer.analyze_performance(metrics)

        return {
            "status": "success",
            "seller_id": seller_id,
            "current_roi": roi,
            "current_growth": f"{growth_rate * 100:.1f}%",
            "recommended_strategy": strategy.value,
            "rationale": "High ROI and growth momentum justify increased spend"
        }

    except Exception as e:
        logger.error(f"Strategy recommendation failed: {e}")
        raise


@router.post("/optimization/budget-allocation")
async def optimize_budget_allocation(
    seller_id: str = Query(...),
    total_budget: float = Query(1000.0),
    strategy: str = Query("balanced"),
) -> Dict[str, Any]:
    """Generate optimized budget allocation across channels."""

    try:
        from app.domains.automation.performance_optimizer import OptimizationStrategy

        opt_strategy = OptimizationStrategy(strategy)
        recommendation = optimizer.generate_optimization_plan(
            seller_id, {"roi": 2.0, "growth_rate": 0.10}, total_budget
        )

        return {
            "status": "success",
            "strategy": recommendation.strategy.value,
            "total_budget": f"${recommendation.total_recommended_budget:,.2f}",
            "expected_revenue": f"${recommendation.expected_total_revenue:,.2f}",
            "expected_roi": f"{recommendation.expected_roi:.1f}x",
            "channel_allocation": [
                {
                    "channel": alloc.channel,
                    "budget": f"${alloc.recommended_budget:,.2f}",
                    "expected_leads": alloc.expected_leads,
                    "expected_revenue": f"${alloc.expected_revenue:,.2f}",
                    "confidence": f"{alloc.confidence * 100:.0f}%"
                }
                for alloc in recommendation.channel_allocations
            ],
            "rationale": recommendation.rationale,
            "actions": recommendation.actions
        }

    except Exception as e:
        logger.error(f"Budget allocation failed: {e}")
        raise


# ============================================================
# Phase 17: Customer Retention Automation
# ============================================================


@router.post("/retention/analyze-customer/{customer_id}")
async def analyze_customer_churn_risk(customer_id: str) -> Dict[str, Any]:
    """Analyze customer churn risk and generate retention plan."""

    try:
        # Mock customer data
        customer_data = {
            "days_since_last_login": 25,
            "usage_percentage": 45,
            "open_support_tickets": 1,
            "failed_payment_attempts": 0,
            "viewed_competitor": False,
            "plan": "professional",
            "monthly_spend": 99
        }

        plan = retention_engine.generate_retention_plan(customer_id, customer_data)
        offer = retention_engine.generate_retention_offer(plan)

        return {
            "status": "success",
            "customer_id": customer_id,
            "churn_analysis": {
                "risk_score": f"{plan.churn_risk_score:.2f}",
                "risk_level": plan.churn_probability,
                "days_until_churn": plan.days_until_churn,
                "urgency": "Critical - Act within 24 hours" if plan.churn_probability == "critical" else "High - Act within 7 days"
            },
            "recommended_actions": [action.value for action in plan.recommended_actions],
            "retention_offer": {
                "upgrade_to": plan.upsell_opportunity,
                "original_price": f"${plan.upsell_amount:.2f}",
                "discount": f"{plan.suggested_discount * 100:.0f}%",
                "final_price": f"${plan.upsell_amount * (1 - plan.suggested_discount):.2f}",
                "savings": f"${plan.upsell_amount * plan.suggested_discount:.2f}"
            },
            "next_step": plan.next_step
        }

    except Exception as e:
        logger.error(f"Churn analysis failed: {e}")
        raise


@router.get("/retention/high-value-at-risk")
async def get_high_value_at_risk_customers() -> Dict[str, Any]:
    """Get list of high-value customers at risk of churn."""

    # Mock data
    at_risk = [
        {
            "customer_id": "cust_001",
            "customer_name": "Acme Corp",
            "monthly_value": 5000,
            "churn_risk": "critical",
            "days_until_churn": 7,
            "reason": "3+ unresolved support tickets"
        },
        {
            "customer_id": "cust_002",
            "customer_name": "Tech Solutions",
            "monthly_value": 3500,
            "churn_risk": "high",
            "days_until_churn": 14,
            "reason": "No login in 30 days"
        }
    ]

    return {
        "status": "success",
        "total_at_risk": len(at_risk),
        "total_monthly_value_at_risk": 8500,
        "customers": at_risk,
        "recommended_action": "Initiate retention campaigns immediately"
    }


@router.post("/retention/upsell-opportunity/{customer_id}")
async def identify_upsell_opportunity(customer_id: str) -> Dict[str, Any]:
    """Identify upsell opportunity for customer."""

    # Mock analysis
    return {
        "status": "success",
        "customer_id": customer_id,
        "current_plan": "Professional",
        "current_spend": 99,
        "upsell_opportunity": "Enterprise Plan",
        "upsell_price": 299,
        "expansion_potential": 200,
        "confidence": "85%",
        "trigger": "Customer usage at 95% capacity",
        "recommended_messaging": "You're maximizing your plan. Upgrade to Enterprise for unlimited features.",
        "expected_close_rate": "45%"
    }
