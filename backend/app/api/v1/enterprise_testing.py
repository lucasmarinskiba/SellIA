from fastapi import APIRouter, Query
from app.domains.enterprise.testing_framework import TestingFramework, TestType

router = APIRouter(tags=["testing"])
testing_framework = TestingFramework()


@router.post("/testing/create")
async def create_test(
    user_id: str = Query(...),
    test_name: str = Query(...),
    test_type: str = Query(...),
    hypothesis: str = Query(...),
    variant_a_name: str = Query(...),
    variant_b_name: str = Query(...),
):
    """Create new A/B test."""
    try:
        test_type_enum = TestType(test_type)
        test = testing_framework.create_test(
            user_id,
            test_name,
            test_type_enum,
            hypothesis,
            variant_a_name,
            variant_b_name,
        )

        return {
            "status": "created",
            "test_id": test.id,
            "name": test.name,
            "variants": [
                {"id": v.id, "name": v.name} for v in test.variants
            ],
        }
    except ValueError:
        return {"status": "error", "message": f"Invalid test type: {test_type}"}


@router.post("/testing/{test_id}/start")
async def start_test(
    user_id: str = Query(...),
    test_id: str = Query(...),
):
    """Start A/B test."""
    success = testing_framework.start_test(user_id, test_id)

    return {
        "status": "started" if success else "not_found",
        "test_id": test_id,
    }


@router.post("/testing/{test_id}/pause")
async def pause_test(
    user_id: str = Query(...),
    test_id: str = Query(...),
):
    """Pause running test."""
    success = testing_framework.pause_test(user_id, test_id)

    return {
        "status": "paused" if success else "not_found",
        "test_id": test_id,
    }


@router.post("/testing/{test_id}/end")
async def end_test(
    user_id: str = Query(...),
    test_id: str = Query(...),
):
    """End test and calculate results."""
    success = testing_framework.end_test(user_id, test_id)

    if success:
        result = testing_framework.get_test_results(user_id, test_id)
        if result:
            return {
                "status": "completed",
                "test_id": test_id,
                "winning_variant": result.winning_variant,
                "uplift": f"{result.uplift_percentage:.2f}%",
                "confidence": f"{result.confidence:.0f}%",
                "recommendation": result.recommendation,
            }

    return {"status": "not_found", "test_id": test_id}


@router.get("/testing/tests/{user_id}")
async def list_tests(
    user_id: str,
    status: str = Query(None, description="draft, running, completed"),
):
    """List A/B tests."""
    tests = testing_framework.list_tests(user_id, status)

    return {
        "user_id": user_id,
        "total": len(tests),
        "tests": [
            {
                "id": t.id,
                "name": t.name,
                "type": t.test_type.value,
                "status": t.status.value,
                "hypothesis": t.hypothesis,
                "started_at": t.started_at.isoformat() if t.started_at else None,
            }
            for t in tests
        ],
    }


@router.get("/testing/active/{user_id}")
async def get_active_tests(user_id: str):
    """Get currently running tests."""
    tests = testing_framework.get_active_tests(user_id)

    return {
        "user_id": user_id,
        "active_count": len(tests),
        "tests": [
            {
                "id": t.id,
                "name": t.name,
                "type": t.test_type.value,
                "variants": [v.name for v in t.variants],
                "days_running": (
                    (datetime.now() - t.started_at).days
                    if t.started_at
                    else 0
                ),
            }
            for t in tests
        ],
    }


@router.get("/testing/results/{user_id}/{test_id}")
async def get_test_results(user_id: str, test_id: str):
    """Get test results and recommendations."""
    result = testing_framework.get_test_results(user_id, test_id)

    if not result:
        return {"status": "not_found", "message": "Test not completed yet"}

    return {
        "test_id": test_id,
        "test_name": result.test_name,
        "winning_variant": result.winning_variant,
        "uplift": f"{result.uplift_percentage:.2f}%",
        "revenue_impact": f"${result.revenue_impact:,.2f}/month",
        "sample_size": result.sample_size,
        "confidence": f"{result.confidence:.0f}%",
        "recommendation": result.recommendation,
    }


@router.get("/testing/portfolio/{user_id}")
async def get_portfolio_status(user_id: str):
    """Get overall testing portfolio health."""
    status = testing_framework.get_portfolio_status(user_id)

    return {
        "user_id": user_id,
        "portfolio": {
            "total_tests": status["total_tests"],
            "active_tests": status["active_tests"],
            "completed_tests": status["completed_tests"],
            "avg_uplift": f"{status['avg_uplift']:.2f}%",
            "total_impact": f"${status['total_estimated_impact']:,.2f}/month",
        },
    }


from datetime import datetime
