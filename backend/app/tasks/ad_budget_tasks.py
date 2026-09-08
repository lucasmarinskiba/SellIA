"""Ad-budget autopilot Celery tasks."""


from celery import shared_task
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.async_bridge import run_async
from app.core.logger import get_logger
from app.domains.ad_budget.models import AdBudgetConfig
from app.domains.ad_budget.service import AdBudgetService
from app.domains.businesses.models import Business

logger = get_logger(__name__)


@shared_task(name="app.tasks.ad_budget_tasks.run_budget_cycles")
def run_budget_cycles():
    """Daily: run the reallocation cycle for every business with the autopilot on."""
    async def _run():
        async with AsyncSessionLocal() as db:
            active = (
                await db.execute(
                    select(AdBudgetConfig).where(
                        AdBudgetConfig.is_active.is_(True),
                        AdBudgetConfig.is_paused.is_(False),
                    )
                )
            ).scalars().all()

            ran = 0
            applied = 0
            for cfg in active:
                try:
                    async with AsyncSessionLocal() as biz_db:
                        res = await AdBudgetService(biz_db).run_cycle(cfg.business_id)
                    if res.get("status") == "ok":
                        ran += 1
                        applied += 1 if res.get("applied") else 0
                except Exception as e:  # noqa: BLE001
                    logger.error(f"ad_budget cycle failed for business {cfg.business_id}: {e}")

            logger.info(f"ad_budget: {ran} cycles run, {applied} auto-applied")
            return {"cycles": ran, "applied": applied}

    return run_async(_run())
