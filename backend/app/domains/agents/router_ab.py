"""A/B Testing Router

Endpoints for creating, running, and analyzing prompt experiments.
"""

from uuid import UUID
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.agents.ab_service import ABTestEngine
from app.domains.agents.schemas_ab import PromptExperimentCreate

router = APIRouter(prefix="/ab", tags=["ab-testing"])


def _to_response(experiment) -> dict:
    return {
        "id": experiment.id,
        "business_id": experiment.business_id,
        "name": experiment.name,
        "agent_type": experiment.agent_type,
        "metric": experiment.metric,
        "variant_a_name": experiment.variant_a_name,
        "variant_a_prompt": experiment.variant_a_prompt,
        "variant_b_name": experiment.variant_b_name,
        "variant_b_prompt": experiment.variant_b_prompt,
        "status": experiment.status,
        "confidence_threshold": experiment.confidence_threshold,
        "min_samples": experiment.min_samples,
        "winner_variant": experiment.winner_variant,
        "started_at": experiment.started_at,
        "completed_at": experiment.completed_at,
        "created_at": experiment.created_at,
        "updated_at": experiment.updated_at,
    }


@router.post("/experiments", status_code=status.HTTP_201_CREATED)
async def create_experiment(
    payload: PromptExperimentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new prompt A/B experiment."""
    experiment = await ABTestEngine.create_experiment(
        db=db,
        name=payload.name,
        agent_type=payload.agent_type,
        variant_a_name=payload.variant_a_name,
        variant_a_prompt=payload.variant_a_prompt,
        variant_b_name=payload.variant_b_name,
        variant_b_prompt=payload.variant_b_prompt,
        metric=payload.metric,
        business_id=current_user.business_id,
        confidence_threshold=payload.confidence_threshold,
        min_samples=payload.min_samples,
    )
    return _to_response(experiment)


@router.get("/experiments")
async def list_experiments(
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List prompt experiments for the current user's business."""
    result = await ABTestEngine.list_experiments(
        db=db,
        status=status,
        business_id=current_user.business_id,
        limit=limit,
        offset=offset,
    )
    return {
        "total": result["total"],
        "experiments": [_to_response(e) for e in result["experiments"]],
    }


@router.get("/experiments/{experiment_id}")
async def get_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a single experiment with computed stats."""
    experiment = await ABTestEngine.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if experiment.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    stats = await ABTestEngine.analyze_experiment(db, experiment_id)
    return {
        **_to_response(experiment),
        "stats": stats,
    }


@router.post("/experiments/{experiment_id}/start")
async def start_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Start a draft or paused experiment."""
    experiment = await ABTestEngine.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if experiment.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        updated = await ABTestEngine.start_experiment(db, experiment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_response(updated)


@router.post("/experiments/{experiment_id}/pause")
async def pause_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Pause a running experiment."""
    experiment = await ABTestEngine.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if experiment.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        updated = await ABTestEngine.pause_experiment(db, experiment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_response(updated)


@router.post("/experiments/{experiment_id}/analyze")
async def analyze_experiment(
    experiment_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze an experiment and return statistics."""
    experiment = await ABTestEngine.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if experiment.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        analysis = await ABTestEngine.analyze_experiment(db, experiment_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return analysis


@router.post("/experiments/{experiment_id}/promote/{variant}")
async def promote_experiment(
    experiment_id: UUID,
    variant: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Manually promote a variant and close the experiment."""
    experiment = await ABTestEngine.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if experiment.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    try:
        updated = await ABTestEngine.promote_experiment(db, experiment_id, variant)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return _to_response(updated)


@router.get("/experiments/{experiment_id}/results")
async def get_experiment_results(
    experiment_id: UUID,
    variant: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get raw results for an experiment."""
    experiment = await ABTestEngine.get_experiment(db, experiment_id)
    if not experiment:
        raise HTTPException(status_code=404, detail="Experiment not found")
    if experiment.business_id != current_user.business_id:
        raise HTTPException(status_code=403, detail="Forbidden")

    results = await ABTestEngine.get_results(
        db=db,
        experiment_id=experiment_id,
        variant=variant,
        limit=limit,
        offset=offset,
    )
    return {
        "experiment_id": experiment_id,
        "results": [
            {
                "id": r.id,
                "experiment_id": r.experiment_id,
                "variant": r.variant,
                "conversation_id": r.conversation_id,
                "outcome": r.outcome,
                "revenue": float(r.revenue) if r.revenue is not None else None,
                "engagement_score": r.engagement_score,
                "created_at": r.created_at,
            }
            for r in results
        ],
    }
