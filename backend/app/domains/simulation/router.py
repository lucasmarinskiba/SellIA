"""Simulation / Training Engine — API Router

Exposes endpoints for scenario management, simulation runs, and leaderboards.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.simulation.models import SimulationScenario, SimulationRun, SimulationLeaderboard
from app.domains.simulation.schemas import (
    SimulationScenarioCreate,
    SimulationScenarioOut,
    SimulationRunOut,
    SimulationLeaderboardOut,
    QuickSimulationCreate,
    RunSimulationCreate,
)
from app.domains.simulation.engine import SimulationEngine

router = APIRouter(prefix="/simulations", tags=["simulations"])
engine = SimulationEngine()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/scenarios", response_model=SimulationScenarioOut, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    data: SimulationScenarioCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new simulation scenario."""
    scenario = await engine.create_scenario(
        db=db,
        business_id=data.business_id,
        name=data.name,
        description=data.description or "",
        difficulty=data.difficulty,
        objective=data.objective,
        customer_persona=data.customer_persona,
        agent_type=data.agent_type,
        success_criteria=data.success_criteria or {},
    )
    return scenario


@router.get("/scenarios", response_model=list[SimulationScenarioOut])
async def list_scenarios(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    agent_type: str | None = None,
    limit: int = 100,
):
    """List active simulation scenarios."""
    query = (
        select(SimulationScenario)
        .where(SimulationScenario.is_active == True)
        .order_by(desc(SimulationScenario.created_at))
        .limit(limit)
    )
    if agent_type:
        query = query.where(SimulationScenario.agent_type == agent_type)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/run/{scenario_id}", response_model=SimulationRunOut)
async def run_simulation(
    scenario_id: UUID,
    data: RunSimulationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Run a simulation for a given scenario."""
    run = await engine.run_simulation(
        db=db,
        scenario_id=scenario_id,
        user_id=current_user.id,
        agent_config=data.agent_config,
    )
    return run


@router.get("/runs", response_model=list[SimulationRunOut])
async def list_runs(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = 50,
):
    """List simulation runs for the current user."""
    result = await db.execute(
        select(SimulationRun)
        .where(SimulationRun.user_id == current_user.id)
        .order_by(desc(SimulationRun.created_at))
        .limit(limit)
    )
    return result.scalars().all()


@router.get("/runs/{run_id}", response_model=SimulationRunOut)
async def get_run(
    run_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get details of a specific simulation run."""
    result = await db.execute(
        select(SimulationRun).where(
            SimulationRun.id == run_id,
            SimulationRun.user_id == current_user.id,
        )
    )
    run = result.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return run


@router.get("/leaderboard", response_model=list[SimulationLeaderboardOut])
async def get_leaderboard(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    agent_type: str | None = None,
    limit: int = 50,
):
    """Get simulation leaderboard."""
    return await engine.get_leaderboard(db, agent_type=agent_type, limit=limit)


@router.post("/quick", response_model=SimulationRunOut)
async def quick_simulation(
    data: QuickSimulationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Run a quick simulation with a default scenario."""
    # Look for existing default scenario for this agent_type
    result = await db.execute(
        select(SimulationScenario).where(
            SimulationScenario.agent_type == data.agent_type,
            SimulationScenario.name == "__quick_default__",
            SimulationScenario.is_active == True,
        )
    )
    scenario = result.scalar_one_or_none()

    if not scenario:
        # Create a default scenario
        default_persona = {
            "name": "María",
            "personality": "dudosa pero con intención de compra",
            "budget": "$5000 - $10000",
            "pain_points": ["precio alto", "no conoce la marca"],
            "objections": ["es muy caro", "necesito pensarlo"],
            "communication_style": "formal pero cercana",
        }
        scenario = await engine.create_scenario(
            db=db,
            business_id=None,
            name="__quick_default__",
            description="Escenario rápido por defecto para entrenamiento.",
            difficulty="beginner",
            objective="close_sale",
            customer_persona=default_persona,
            agent_type=data.agent_type,
            success_criteria={"min_score": 60, "required_actions": ["qualify", "close"]},
        )

    run = await engine.run_simulation(
        db=db,
        scenario_id=scenario.id,
        user_id=current_user.id,
        agent_config=data.agent_config,
    )
    return run
