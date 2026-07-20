"""RQ-Scheduler · cron-style recurring jobs.

Run via: `python -m app.jobs.scheduler`
"""
import asyncio
import logging
from datetime import datetime, timezone

from rq_scheduler import Scheduler

from app.core.logging import setup_logging
from app.jobs.queue import get_queue
from app.jobs.tasks import daily_report, stock_check


logger = logging.getLogger(__name__)


# ─── Job functions executed by worker ──────────────────────────────────────


def cron_dispatch_daily_reports() -> dict:
    """Fan out daily reports to all active tenants. Runs once · enqueues per-tenant."""
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.db.models import Tenant

    async def _do():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Tenant.id).where(Tenant.plan != "trial"))
            tenant_ids = [str(tid) for (tid,) in result.all()]

        q = get_queue()
        for tid in tenant_ids:
            q.enqueue(daily_report, tid)
        return {"dispatched": len(tenant_ids)}

    return asyncio.run(_do())


def cron_stock_check_all() -> dict:
    """Every 30min · check stock thresholds + trigger auto-reorders."""
    from sqlalchemy import select
    from app.db.session import AsyncSessionLocal
    from app.db.models import Tenant

    async def _do():
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Tenant.id))
            tenant_ids = [str(tid) for (tid,) in result.all()]
        q = get_queue()
        for tid in tenant_ids:
            q.enqueue(stock_check, tid)
        return {"checked": len(tenant_ids)}

    return asyncio.run(_do())


def cron_session_cleanup() -> dict:
    """Hourly · kill stale CUA sandboxes past 30min TTL."""
    logger.info("session_cleanup_running")
    # TODO: query active sandboxes table · tear down expired
    return {"cleaned": 0}


# ─── Schedule setup ─────────────────────────────────────────────────────────


SCHEDULE = [
    # (cron expr, callable, description)
    ("0 9 * * *",  cron_dispatch_daily_reports, "Daily reports · 9am UTC"),
    ("*/30 * * * *", cron_stock_check_all,      "Stock check · every 30min"),
    ("0 * * * *",  cron_session_cleanup,        "CUA cleanup · hourly"),
]


def main() -> None:
    setup_logging()
    queue = get_queue()
    scheduler = Scheduler(queue=queue, connection=queue.connection)

    # Wipe + recreate (idempotent across deploys)
    for job in scheduler.get_jobs():
        scheduler.cancel(job)

    for cron, func, desc in SCHEDULE:
        scheduler.cron(
            cron,
            func=func,
            queue_name="default",
            use_local_timezone=False,
            description=desc,
        )
        logger.info("cron_scheduled", extra={"cron": cron, "func": func.__name__})

    logger.info("scheduler_running", extra={"jobs": len(SCHEDULE), "since": datetime.now(timezone.utc).isoformat()})
    scheduler.run()


if __name__ == "__main__":
    main()
