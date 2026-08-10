"""Phases 14-17: Advanced analytics, automation, and retention."""

from fastapi import APIRouter, Query
from typing import Dict, Any
import logging

from app.domains.analytics.seller_analytics import SellerAnalyticsEngine
from app.domains.automation.performance_optimizer import PerformanceOptimizer
from app.domains.retention.retention_engine import RetentionEngine

router = APIRouter(tags=["advanced-automation"])
logger = logging.getLogger(__name__)

analytics_engine = SellerAnalyticsEngine()
optimizer = PerformanceOptimizer()
retention_engine = RetentionEngine()


# ============================================================
# Phase 14: Analytics Dashboard
# ============================================================


@router.get("/analytics/dashboard/{seller_id}")
async def get_seller_dashboard(seller_id: str) -> Dict[str, Any]:
    """Get complete seller analytics dashboard."""

    try:
        dashboard = analytics_engine.generate_dashboard(seller_id)

        return {
            "status": "success",
            "seller_id": seller_id,
            "metrics": {
                "leads": dashboard.current_metrics.leads_generated,
                "qualified": dashboard.current_metrics.leads_qualified,
                "conversion_rate": f"{dashboard.current_metrics.conversion_rate * 100:.1f}%",
                "deals_closed": dashboard.current_metrics.deals_closed,
                "revenue": f"${dashboard.current_metrics.revenue_generated:,.2f}",
                "avg_deal_size": f"${dashboard.current_metrics.avg_deal_size:,.2f}",
                "customer_satisfaction": f"{dashboard.current_metrics.customer_satisfaction}/5"
            },
            "channel_performance": [
                {
                    "channel": ch.channel,
                    "rank": ch.rank,
                    "roi": f"{ch.roi:.1f}x",
                    "conversion": f"{ch.conversion_rate * 100:.1f}%",
                    "cost_per_lead": f"${ch.cost_per_lead:.2f}"
                }
                for ch in dashboard.channel_performance
            ],
            "daily_trend": dashboard.daily_trend[:7],
            "top_products": dashboard.top_products,
            "top_customers": dashboard.top_customers,
            "revenue_forecast": {
                "7_days": f"${dashboard.revenue_forecast['7_days']:,.0f}",
                "30_days": f"${dashboard.revenue_forecast['30_days']:,.0f}",
                "90_days": f"${dashboard.revenue_forecast['90_days']:,.0f}",
                "annual": f"${dashboard.revenue_forecast['annual']:,.0f}"
            },
            "alerts": dashboard.alerts
        }

    except Exception as e:
        logger.error(f"Dashboard generation failed: {e}")
        raise


@router.get("/analytics/channel-rankings/{seller_id}")
async def get_channel_rankings(seller_id: str) -> Dict[str, Any]:
    """Get ranked channels by performance."""

    channels = analytics_engine.get_channel_performance(seller_id)

    return {
        "status": "success",
        "channels": [
            {
                "rank": ch.rank,
                "channel": ch.channel,
                "roi": f"{ch.roi:.1f}x",
                "leads": ch.leads_generated,
                "conversion": f"{ch.conversion_rate * 100:.1f}%",
                "recommendation": "Increase spend" if ch.rank <= 2 else "Maintain" if ch.rank <= 3 else "Reduce"
            }
            for ch in channels
        ]
    }


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
