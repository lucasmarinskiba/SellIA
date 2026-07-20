"""Simulation / Training Engine — FastAPI Router

Endpoints:
- GET  /training/scenarios
- POST /training/scenarios
- POST /training/simulations
- GET  /training/simulations/{id}
- GET  /training/leaderboard
"""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.training import service as training_service
from app.domains.training.schemas import (
    SimulationScenarioCreate,
    SimulationScenarioOut,
    SimulationScenarioUpdate,
    SimulationStartRequest,
    SimulationRunOut,
    LeaderboardEntry,
)

router = APIRouter(prefix="/training", tags=["training"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# ===== Scenarios =====

@router.get("/scenarios", response_model=list[SimulationScenarioOut])
async def list_scenarios(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    business_id: UUID,
    difficulty: Optional[str] = Query(None, pattern=r"^(easy|medium|hard|expert)$"),
):
    """List active simulation scenarios for a business."""
    scenarios = await training_service.list_scenarios(db, business_id, difficulty=difficulty)
    return scenarios


@router.post("/scenarios", response_model=SimulationScenarioOut, status_code=201)
async def create_scenario(
    data: SimulationScenarioCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new training scenario."""
    scenario = await training_service.create_scenario(db, data)
    return scenario


@router.patch("/scenarios/{scenario_id}", response_model=SimulationScenarioOut)
async def update_scenario(
    scenario_id: UUID,
    data: SimulationScenarioUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update an existing training scenario."""
    scenario = await training_service.update_scenario(db, scenario_id, data)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.delete("/scenarios/{scenario_id}", status_code=204)
async def delete_scenario(
    scenario_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete a training scenario."""
    deleted = await training_service.delete_scenario(db, scenario_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return None


# ===== Simulations =====

@router.post("/simulations", response_model=SimulationRunOut, status_code=202)
async def start_simulation(
    req: SimulationStartRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Start a new simulation run (queued via Celery)."""
    scenario = await training_service.get_scenario(db, req.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    run = await training_service.start_simulation(
        db,
        scenario_id=req.scenario_id,
        agent_type=req.agent_id and str(req.agent_id) or None,
    )
    return run


@router.get("/simulations/{run_id}", response_model=SimulationRunOut)
async def get_simulation_results(
    run_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get results for a simulation run."""
    run = await training_service.get_simulation_results(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation run not found")
    return run


# ===== Leaderboard =====

@router.get("/leaderboard", response_model=list[LeaderboardEntry])
async def get_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    business_id: UUID,
    limit: int = Query(20, ge=1, le=100),
):
    """Get top simulation runs by score for a business."""
    entries = await training_service.get_leaderboard(db, business_id, limit=limit)
    return entries
