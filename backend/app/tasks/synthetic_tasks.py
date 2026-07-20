"""
Synthetic Monitoring Celery Tasks

Periodic health checks that run every 5 minutes.
"""

import asyncio
from celery import shared_task

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.synthetic.service import run_all_checks

logger = get_logger(__name__)


@shared_task
def run_synthetic_checks_task():
    """Run all synthetic checks every 5 minutes."""
    async def _run():
        async with AsyncSessionLocal() as db:
            snapshot = await run_all_checks(db)
            logger.info(
                f"Synthetic checks: {snapshot.checks_passed}/{snapshot.checks_total} passed, "
                f"status={snapshot.overall_status}"
            )
    asyncio.run(_run())
