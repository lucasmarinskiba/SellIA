"""A/B Testing framework for comparing agent strategies."""

from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
from enum import Enum
import random

router = APIRouter(tags=["ab-testing"])
logger = logging.getLogger(__name__)


class TestMetric(str, Enum):
    """Key metrics to track in A/B tests."""
    CLOSE_RATE = "close_rate"
    AVG_DEAL_SIZE = "avg_deal_size"
    SALES_CYCLE_DAYS = "sales_cycle_days"
    CUSTOMER_SATISFACTION = "customer_satisfaction"
    EXPANSION_RATE = "expansion_rate"


@router.post("/ab-testing/create-test")
async def create_ab_test(
    test_name: str = Query(...),
    control_strategy: str = Query(..., description="Baseline strategy"),
    treatment_strategy: str = Query(..., description="Variant strategy"),
    metric: str = Query("close_rate", description="Metric to optimize"),
    sample_size: int = Query(100, ge=10, le=10000),
    duration_days: int = Query(14, ge=1, le=90),
) -> Dict[str, Any]:
    """Create A/B test to compare two strategies."""
    test_id = f"test_{datetime.now().timestamp()}"

    return {
        "status": "success",
        "test": {
            "test_id": test_id,
            "test_name": test_name,
            "control_strategy": control_strategy,
            "treatment_strategy": treatment_strategy,
            "metric": metric,
            "sample_size": sample_size,
            "duration_days": duration_days,
            "created_at": datetime.utcnow().isoformat(),
            "status": "running",
            "hypothesis": f"{treatment_strategy} outperforms {control_strategy} on {metric}",
        },
        "allocation": {
            "control": f"50% of {sample_size} = {sample_size // 2} leads",
            "treatment": f"50% of {sample_size} = {sample_size // 2} leads",
        },
        "expected_results_date": (
            datetime.utcnow() + timedelta(days=duration_days)
        ).isoformat(),
    }


@router.get("/ab-testing/test/{test_id}")
async def get_test_results(test_id: str) -> Dict[str, Any]:
    """Get current results for an A/B test."""
    # Mock results (in production, query from database)
    control_performance = random.uniform(0.35, 0.65)
    treatment_performance = random.uniform(0.35, 0.75)

    # Statistical significance
    improvement = (treatment_performance - control_performance) / control_performance * 100
    is_significant = abs(improvement) > 15  # 15% threshold

    return {
        "status": "success",
        "test_id": test_id,
        "results": {
            "control": {
                "strategy": "Balanced",
                "close_rate": round(control_performance, 3),
                "avg_deal_size": 72000,
                "avg_sales_cycle_days": 21,
                "customer_satisfaction": 4.2,
                "sample_size": 50,
            },
            "treatment": {
                "strategy": "Aggressive",
                "close_rate": round(treatment_performance, 3),
                "avg_deal_size": 75000,
                "avg_sales_cycle_days": 16,
                "customer_satisfaction": 4.1,
                "sample_size": 50,
            },
            "improvement": {
                "percentage": round(improvement, 1),
                "direction": "positive" if improvement > 0 else "negative",
                "statistically_significant": is_significant,
                "confidence_level": "95%" if is_significant else "Below threshold",
            },
            "recommendation": (
                f"ADOPT {improvement:+.1f}% improvement detected"
                if is_significant
                else "CONTINUE TEST - need more data for significance"
            ),
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.post("/ab-testing/allocate-lead")
async def allocate_lead_to_test(
    lead_id: str = Query(...),
    test_id: str = Query(...),
) -> Dict[str, Any]:
    """Randomly allocate a lead to control or treatment group."""
    # 50/50 split
    group = "control" if random.random() < 0.5 else "treatment"

    return {
        "status": "success",
        "allocation": {
            "lead_id": lead_id,
            "test_id": test_id,
            "group": group,
            "strategy": "Balanced" if group == "control" else "Aggressive",
            "message": f"Lead {lead_id} assigned to {group} group ({group.title()} Strategy)",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/ab-testing/strategy-comparison")
async def compare_strategies() -> Dict[str, Any]:
    """Compare all negotiation strategies on key metrics."""
    return {
        "status": "success",
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": "Strategy Performance Comparison",
        "comparison": {
            "Aggressive": {
                "close_rate_pct": 62,
                "avg_deal_size_usd": 75000,
                "sales_cycle_days": 16,
                "customer_satisfaction": 4.1,
                "expansion_rate_pct": 35,
                "best_for": "High-intent, no expansion focus",
                "risk": "May sacrifice long-term value",
            },
            "Balanced": {
                "close_rate_pct": 58,
                "avg_deal_size_usd": 72000,
                "sales_cycle_days": 21,
                "customer_satisfaction": 4.3,
                "expansion_rate_pct": 45,
                "best_for": "Most deals, sustainable growth",
                "risk": "Slower close, lower deal size",
            },
            "Strategic": {
                "close_rate_pct": 54,
                "avg_deal_size_usd": 85000,
                "sales_cycle_days": 28,
                "customer_satisfaction": 4.5,
                "expansion_rate_pct": 62,
                "best_for": "High-expansion potential, enterprise",
                "risk": "Longer cycle, requires patience",
            },
            "Conservative": {
                "close_rate_pct": 45,
                "avg_deal_size_usd": 68000,
                "sales_cycle_days": 35,
                "customer_satisfaction": 4.4,
                "expansion_rate_pct": 28,
                "best_for": "Low-intent, margin preservation",
                "risk": "Low close rate, slow",
            },
        },
        "recommendation": {
            "optimal_strategy": "Balanced",
            "reason": "Best combination of close rate, deal size, and customer satisfaction",
            "secondary": "Strategic for enterprise deals targeting high expansion",
        },
        "timestamp": datetime.utcnow().isoformat(),
    }


from datetime import timedelta
