"""Demand-forecasting Celery tasks."""

import asyncio

from celery import shared_task
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.businesses.models import Business
from app.domains.forecasting.service import ForecastingService

logger = get_logger(__name__)


def _async_run(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


@shared_task(name="app.tasks.forecasting_tasks.nightly_forecasts", time_limit=3600, soft_time_limit=3300)
def nightly_forecasts():
    """Retrain + forecast every active business's demand series."""
    async def _run():
        async with AsyncSessionLocal() as db:
            businesses = (
                await db.execute(select(Business).where(Business.is_active == True))
            ).scalars().all()

        summary = {"businesses": 0, "series_ok": 0}
        for biz in businesses:
            try:
                async with AsyncSessionLocal() as bdb:
                    res = await ForecastingService(bdb).run_all(biz.id, horizon=28)
                summary["businesses"] += 1
                summary["series_ok"] += res.get("ok", 0)
            except Exception as e:  # noqa: BLE001
                logger.error(f"nightly forecast failed for business {biz.id}: {e}")
        logger.info(f"nightly_forecasts: {summary}")
        return summary

    return _async_run(_run())


@shared_task(name="app.tasks.forecasting_tasks.weekly_accuracy_eval", time_limit=1800)
def weekly_accuracy_eval():
    """Score past forecasts against realised demand."""
    async def _run():
        async with AsyncSessionLocal() as db:
            businesses = (
                await db.execute(select(Business).where(Business.is_active == True))
            ).scalars().all()
        rows = 0
        for biz in businesses:
            try:
                async with AsyncSessionLocal() as bdb:
                    res = await ForecastingService(bdb).evaluate_accuracy(biz.id)
                rows += res.get("accuracy_rows", 0)
            except Exception as e:  # noqa: BLE001
                logger.error(f"accuracy eval failed for business {biz.id}: {e}")
        logger.info(f"weekly_accuracy_eval: {rows} rows")
        return {"accuracy_rows": rows}

    return _async_run(_run())
