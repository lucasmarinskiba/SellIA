"""Brand Transformation — Celery tasks.

Drives the standing `bt_automations` (rediagnosis, fomo_cadence,
brand_consistency_monitor, positioning_drift_watch, competitor_narrative_watch)
on their per-row schedule. The beat entry fires hourly; each row only actually
runs when its own interval has elapsed since `last_run_at`, so the LLM cost is
bounded by the automations' declared cadence, not by the tick frequency.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.brand_transformation.models import BrandAutomation, TransformationProgram
from app.domains.brand_transformation.orchestrator import TransformationOrchestrator

logger = get_logger(__name__)

# schedule keyword -> minimum seconds between runs
_INTERVALS = {
    "hourly": 3600,
    "daily": 86_400,
    "weekly": 604_800,
    "monthly": 2_592_000,      # 30 days
    "quarterly": 7_776_000,    # 90 days
}
# run a bit early rather than skipping a whole cycle on scheduler jitter
_SLACK = 1800  # 30 min


def _async_run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio

            nest_asyncio.apply()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def _is_due(automation: BrandAutomation, now: datetime) -> bool:
    if not automation.is_active:
        return False
    interval = _INTERVALS.get(automation.schedule, _INTERVALS["monthly"])
    last = automation.last_run_at
    if last is None:
        return True
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    return (now - last) >= timedelta(seconds=interval - _SLACK)


@shared_task(name="app.tasks.brand_transformation_tasks.run_due_brand_automations")
def run_due_brand_automations():
    """Hourly: run every active brand automation whose interval has elapsed."""

    async def _run():
        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as db:
            rows = (
                await db.execute(
                    select(BrandAutomation).where(BrandAutomation.is_active.is_(True))
                )
            ).scalars().all()
            due_ids = [r.id for r in rows if _is_due(r, now)]

        ran, failed = 0, 0
        for automation_id in due_ids:
            try:
                async with AsyncSessionLocal() as run_db:
                    row = (
                        await run_db.execute(
                            select(BrandAutomation).where(BrandAutomation.id == automation_id)
                        )
                    ).scalar_one_or_none()
                    if row is None or not _is_due(row, datetime.now(timezone.utc)):
                        continue
                    await TransformationOrchestrator(run_db).run_automation(row)
                ran += 1
            except Exception as e:  # noqa: BLE001
                failed += 1
                logger.error(f"brand automation {automation_id} failed: {e}")

        logger.info(
            f"brand_transformation: {ran} automations run, {failed} failed "
            f"({len(due_ids)} due of {len(due_ids)} checked)"
        )
        return {"ran": ran, "failed": failed, "due": len(due_ids)}

    return _async_run(_run())


@shared_task(name="app.tasks.brand_transformation_tasks.run_program_all", time_limit=5400, soft_time_limit=5100)
def run_program_all(program_id: str):
    """Run every etapa of a program end to end. Dispatched by the /run-all
    endpoint because a full run is ~15 real LLM calls and would time out a
    synchronous HTTP request. Sets program.run_state along the way."""

    async def _run():
        async with AsyncSessionLocal() as db:
            orch = TransformationOrchestrator(db)
            prog = await orch.get_program(uuid.UUID(program_id))
            if prog is None:
                return {"error": "program not found"}
            prog.run_state = "running"
            await db.commit()
            try:
                results = await orch.run_all(prog)
                prog2 = await orch.get_program(uuid.UUID(program_id))
                prog2.run_state = "done"
                await db.commit()
                logger.info("brand_transformation: program %s run-all done (%s stages)", program_id, len(results))
                return {"program_id": program_id, "stages": len(results), "status": "done"}
            except Exception as e:  # noqa: BLE001
                logger.error("brand_transformation: program %s run-all failed: %s", program_id, e)
                prog3 = await orch.get_program(uuid.UUID(program_id))
                if prog3:
                    prog3.run_state = "failed"
                    await db.commit()
                return {"program_id": program_id, "status": "failed", "error": str(e)[:200]}

    return _async_run(_run())
