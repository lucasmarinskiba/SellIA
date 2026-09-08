"""Sales-agent message/prompt A/B testing -- business-facing API.

Real, DB-backed A/B testing for the sales agent's messages/prompts,
measuring real conversion (lead -> deal won). This is a thin, auth'd,
business-scoped CRUD layer over the engine that already existed and was
already used internally for funnel-voice testing (app.domains.agents.ab_service
.ABTestEngine + app.domains.agents.ab_testing.PromptExperiment) -- the
previous version of this router (app.domains.enterprise.testing_framework)
was a 100% in-memory mock with a fabricated `_calculate_winner` that called
random.randint()/random.uniform() instead of measuring anything real.

variant_a_prompt/variant_b_prompt store the FULL system prompt text for the
agent_type (personality slug, e.g. "vendedor") being tested -- ai_reply.py's
generate_ai_response() looks up the running experiment for
(business_id, agent_type) and swaps the whole system prompt for whichever
variant a conversation is deterministically assigned to, then remembers the
assignment on the conversation so a later deal outcome (won/lost) can be
attributed back to it. See app/domains/agents/ai_reply.py and
app/api/v1/enterprise_deal_intelligence.py's record_deal_outcome.
"""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.agents.models import AgentPersonality
from app.domains.agents.ab_service import ABTestEngine

router = APIRouter(tags=["testing"])


async def _get_business_for_user(business_id: UUID, user: User, db: AsyncSession) -> Business:
    result = await db.execute(select(Business).where(Business.id == business_id, Business.user_id == user.id))
    business = result.scalar_one_or_none()
    if not business:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


async def _get_owned_experiment(test_id: UUID, user: User, db: AsyncSession):
    experiment = await ABTestEngine.get_experiment(db, test_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Test no encontrado")
    if experiment.business_id is not None:
        await _get_business_for_user(experiment.business_id, user, db)
    return experiment


@router.post("/testing/create")
async def create_test(
    business_id: UUID = Query(...),
    test_name: str = Query(...),
    agent_type: str = Query(..., description="Personality slug being tested, e.g. 'vendedor', 'captador'"),
    hypothesis: str = Query(""),
    variant_a_name: str = Query(...),
    variant_a_prompt: str = Query(..., description="Full system prompt text for variant A"),
    variant_b_name: str = Query(...),
    variant_b_prompt: str = Query(..., description="Full system prompt text for variant B"),
    confidence_threshold: float = Query(0.95, ge=0.5, le=0.999),
    min_samples: int = Query(50, ge=10),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new A/B test on the sales agent's messages/prompt for this business."""
    await _get_business_for_user(business_id, current_user, db)

    personality_result = await db.execute(select(AgentPersonality).where(AgentPersonality.slug == agent_type))
    if not personality_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail=f"agent_type '{agent_type}' no es una personalidad de agente válida")

    experiment = await ABTestEngine.create_experiment(
        db,
        name=test_name,
        agent_type=agent_type,
        variant_a_name=variant_a_name,
        variant_a_prompt=variant_a_prompt,
        variant_b_name=variant_b_name,
        variant_b_prompt=variant_b_prompt,
        metric="conversion",
        business_id=business_id,
        confidence_threshold=confidence_threshold,
        min_samples=min_samples,
    )

    return {
        "status": "created",
        "test_id": str(experiment.id),
        "name": experiment.name,
        "agent_type": experiment.agent_type,
        "hypothesis": hypothesis,
        "variants": [
            {"id": "a", "name": experiment.variant_a_name},
            {"id": "b", "name": experiment.variant_b_name},
        ],
    }


@router.post("/testing/{test_id}/start")
async def start_test(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start an A/B test -- new conversations for this agent_type will begin being split."""
    await _get_owned_experiment(test_id, current_user, db)
    try:
        experiment = await ABTestEngine.start_experiment(db, test_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "started", "test_id": str(test_id), "state": experiment.status}


@router.post("/testing/{test_id}/pause")
async def pause_test(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pause a running test -- existing assignments are kept, no new conversations enrolled."""
    await _get_owned_experiment(test_id, current_user, db)
    try:
        experiment = await ABTestEngine.pause_experiment(db, test_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"status": "paused", "test_id": str(test_id), "state": experiment.status}


@router.post("/testing/{test_id}/end")
async def end_test(
    test_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """End the test and compute the real winner from recorded deal outcomes."""
    experiment = await _get_owned_experiment(test_id, current_user, db)
    analysis = await ABTestEngine.analyze_experiment(db, test_id)
    winner = analysis["winner"] if analysis["is_significant"] else None
    experiment = await ABTestEngine.complete_experiment(db, test_id, winner=winner)

    return {
        "status": "completed",
        "test_id": str(test_id),
        "winning_variant": winner,
        "is_significant": analysis["is_significant"],
        "rate_a": f"{analysis['rate_a'] * 100:.2f}%",
        "rate_b": f"{analysis['rate_b'] * 100:.2f}%",
        "sample_size": analysis["n_a"] + analysis["n_b"],
        "confidence": f"{experiment.confidence_threshold * 100:.0f}%",
        "recommendation": (
            f"Usar variante {winner.upper()} -- estadísticamente significativo"
            if winner and winner != "tie"
            else "Datos insuficientes o sin diferencia significativa"
        ),
    }


@router.get("/testing/tests/{business_id}")
async def list_tests(
    business_id: UUID,
    status: str = Query(None, description="draft, running, paused, completed, auto_promoted"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List A/B tests for this business."""
    await _get_business_for_user(business_id, current_user, db)
    listing = await ABTestEngine.list_experiments(db, status=status, business_id=business_id)

    return {
        "business_id": str(business_id),
        "total": listing["total"],
        "tests": [
            {
                "id": str(t.id),
                "name": t.name,
                "agent_type": t.agent_type,
                "status": t.status,
                "started_at": t.started_at.isoformat() if t.started_at else None,
                "winner_variant": t.winner_variant,
            }
            for t in listing["experiments"]
        ],
    }


@router.get("/testing/active/{business_id}")
async def get_active_tests(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get currently running tests for this business."""
    await _get_business_for_user(business_id, current_user, db)
    listing = await ABTestEngine.list_experiments(db, status="running", business_id=business_id)

    return {
        "business_id": str(business_id),
        "active_count": listing["total"],
        "tests": [
            {
                "id": str(t.id),
                "name": t.name,
                "agent_type": t.agent_type,
                "variants": [t.variant_a_name, t.variant_b_name],
                "days_running": (datetime.now(timezone.utc) - t.started_at).days if t.started_at else 0,
            }
            for t in listing["experiments"]
        ],
    }


@router.get("/testing/results/{business_id}/{test_id}")
async def get_test_results(
    business_id: UUID,
    test_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get real test results computed from recorded deal outcomes."""
    await _get_business_for_user(business_id, current_user, db)
    experiment = await ABTestEngine.get_experiment(db, test_id)
    if not experiment or experiment.business_id != business_id:
        raise HTTPException(status_code=404, detail="Test no encontrado")

    analysis = await ABTestEngine.analyze_experiment(db, test_id)

    return {
        "test_id": str(test_id),
        "test_name": experiment.name,
        "status": experiment.status,
        "winning_variant": experiment.winner_variant or analysis["winner"],
        "is_significant": analysis["is_significant"],
        "sample_size": analysis["n_a"] + analysis["n_b"],
        "variant_a": {"name": experiment.variant_a_name, "n": analysis["n_a"], "conversions": analysis["conversions_a"], "rate": f"{analysis['rate_a'] * 100:.2f}%", "revenue": f"${analysis['revenue_a']:,.2f}"},
        "variant_b": {"name": experiment.variant_b_name, "n": analysis["n_b"], "conversions": analysis["conversions_b"], "rate": f"{analysis['rate_b'] * 100:.2f}%", "revenue": f"${analysis['revenue_b']:,.2f}"},
        "p_value": analysis["p_value"],
        "confidence_threshold": f"{experiment.confidence_threshold * 100:.0f}%",
    }


@router.get("/testing/portfolio/{business_id}")
async def get_portfolio_status(
    business_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Overall testing portfolio health for this business, from real recorded outcomes."""
    await _get_business_for_user(business_id, current_user, db)
    listing = await ABTestEngine.list_experiments(db, business_id=business_id, limit=1000)
    tests = listing["experiments"]

    completed = [t for t in tests if t.status in ("completed", "auto_promoted")]
    total_revenue = 0.0
    uplifts = []
    for t in completed:
        analysis = await ABTestEngine.analyze_experiment(db, t.id)
        total_revenue += analysis["revenue_a"] + analysis["revenue_b"]
        if analysis["rate_a"] > 0:
            uplifts.append(((analysis["rate_b"] - analysis["rate_a"]) / analysis["rate_a"]) * 100)

    return {
        "business_id": str(business_id),
        "portfolio": {
            "total_tests": len(tests),
            "active_tests": len([t for t in tests if t.status == "running"]),
            "completed_tests": len(completed),
            "avg_uplift": f"{(sum(uplifts) / len(uplifts)):.2f}%" if uplifts else "N/A",
            "total_revenue_from_completed_tests": f"${total_revenue:,.2f}",
        },
    }
