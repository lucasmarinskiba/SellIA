"""Simulation / Training Engine — Celery Tasks

Async Celery task to run simulations in the background.
"""

import asyncio
import uuid
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.training.service import execute_simulation

logger = get_logger(__name__)


def _async_run(coro):
    """Helper to run async coroutine in sync Celery task."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio

            nest_asyncio.apply()
            return loop.run_until_complete(coro)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@shared_task(name="app.domains.training.tasks.run_simulation_task")
def run_simulation_task(scenario_id: str, agent_type: str, run_id: str):
    """Execute a simulation run asynchronously."""

    async def _run():
        async with AsyncSessionLocal() as db:
            try:
                run = await execute_simulation(
                    db,
                    scenario_id=uuid.UUID(scenario_id),
                    agent_type=agent_type,
                    run_id=uuid.UUID(run_id),
                )
                logger.info(
                    f"Simulation run {run.id} completed with score={run.score}, "
                    f"objective_achieved={run.objective_achieved}"
                )
                return {
                    "status": "completed",
                    "run_id": str(run.id),
                    "score": run.score,
                    "objective_achieved": run.objective_achieved,
                }
            except Exception as exc:
                logger.exception(f"Simulation task failed for run {run_id}: {exc}")
                # Attempt to mark run as failed
                try:
                    from sqlalchemy import select
                    from app.domains.training.models import TrainingRun
                    from datetime import datetime, timezone

                    result = await db.execute(
                        select(TrainingRun).where(TrainingRun.id == uuid.UUID(run_id))
                    )
                    run = result.scalar_one_or_none()
                    if run:
                        run.status = "failed"
                        run.feedback = f"Task error: {str(exc)[:500]}"
                        run.completed_at = datetime.now(timezone.utc)
                        await db.commit()
                except Exception as inner_exc:
                    logger.error(f"Failed to mark run as failed: {inner_exc}")
                raise

    return _async_run(_run())
