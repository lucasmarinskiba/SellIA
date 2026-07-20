"""Simulation / Training Engine — Service Layer

Async service functions for scenario management and simulation orchestration.
"""

import uuid
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func

from app.core.logger import get_logger
from app.domains.training.models import TrainingScenario, TrainingRun
from app.domains.training.schemas import SimulationScenarioCreate, SimulationScenarioUpdate
from app.domains.training.simulator import SimulationEngine

logger = get_logger(__name__)


# ===== Scenario CRUD =====

async def create_scenario(db: AsyncSession, data: SimulationScenarioCreate) -> TrainingScenario:
    scenario = TrainingScenario(**data.model_dump())
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)
    logger.info(f"Created scenario {scenario.id} for business {scenario.business_id}")
    return scenario


async def list_scenarios(
    db: AsyncSession,
    business_id: uuid.UUID,
    difficulty: Optional[str] = None,
) -> List[TrainingScenario]:
    query = select(TrainingScenario).where(
        TrainingScenario.business_id == business_id,
        TrainingScenario.is_active == True,
    )
    if difficulty:
        query = query.where(TrainingScenario.difficulty == difficulty)
    query = query.order_by(TrainingScenario.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


async def get_scenario(db: AsyncSession, scenario_id: uuid.UUID) -> Optional[TrainingScenario]:
    result = await db.execute(
        select(TrainingScenario).where(TrainingScenario.id == scenario_id)
    )
    return result.scalar_one_or_none()


async def update_scenario(
    db: AsyncSession, scenario_id: uuid.UUID, data: SimulationScenarioUpdate
) -> Optional[TrainingScenario]:
    scenario = await get_scenario(db, scenario_id)
    if not scenario:
        return None
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(scenario, field, value)
    await db.commit()
    await db.refresh(scenario)
    return scenario


async def delete_scenario(db: AsyncSession, scenario_id: uuid.UUID) -> bool:
    scenario = await get_scenario(db, scenario_id)
    if not scenario:
        return False
    await db.delete(scenario)
    await db.commit()
    return True


# ===== Simulation Runs =====

async def start_simulation(
    db: AsyncSession,
    scenario_id: uuid.UUID,
    agent_type: Optional[str] = None,
) -> TrainingRun:
    """Queue a simulation run as a Celery task and return the pending run record."""
    scenario = await get_scenario(db, scenario_id)
    if not scenario:
        raise ValueError(f"Scenario {scenario_id} not found")

    # Use scenario's agent_type if none provided
    effective_agent_type = agent_type or scenario.agent_type

    # Create a pending run record so the API can poll immediately
    run = TrainingRun(
        scenario_id=scenario_id,
        agent_id=None,  # will be resolved by the engine
        status="running",
        messages=[],
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    # Queue Celery task
    try:
        from app.tasks.celery_app import celery_app
        celery_app.send_task(
            "app.domains.training.tasks.run_simulation_task",
            args=[str(scenario_id), effective_agent_type, str(run.id)],
        )
        logger.info(f"Queued simulation task for run {run.id}, scenario {scenario_id}")
    except Exception as exc:
        logger.error(f"Failed to queue simulation task: {exc}")
        run.status = "failed"
        run.feedback = f"Failed to queue task: {str(exc)[:200]}"
        run.completed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        await db.commit()

    return run


async def get_simulation_results(db: AsyncSession, run_id: uuid.UUID) -> Optional[TrainingRun]:
    result = await db.execute(
        select(TrainingRun).where(TrainingRun.id == run_id)
    )
    return result.scalar_one_or_none()


async def get_leaderboard(
    db: AsyncSession,
    business_id: uuid.UUID,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Return top simulations by score for a business."""
    result = await db.execute(
        select(TrainingRun, TrainingScenario)
        .join(TrainingScenario, TrainingRun.scenario_id == TrainingScenario.id)
        .where(
            TrainingScenario.business_id == business_id,
            TrainingRun.status == "completed",
            TrainingRun.score.isnot(None),
        )
        .order_by(desc(TrainingRun.score))
        .limit(limit)
    )

    entries = []
    for run, scenario in result.all():
        entries.append({
            "run_id": run.id,
            "scenario_id": scenario.id,
            "scenario_name": scenario.name,
            "agent_type": scenario.agent_type,
            "score": run.score,
            "objective_achieved": run.objective_achieved,
            "customer_satisfaction": run.customer_satisfaction,
            "created_at": run.created_at,
        })
    return entries


# ===== Direct simulation execution (used by Celery task) =====

async def execute_simulation(
    db: AsyncSession,
    scenario_id: uuid.UUID,
    agent_type: str,
    run_id: Optional[uuid.UUID] = None,
) -> TrainingRun:
    """Execute the simulation synchronously (intended for Celery workers)."""
    engine = SimulationEngine(db)
    run = await engine.run_simulation(scenario_id, agent_type, run_id=run_id)
    return run
