"""
Support Celery Tasks

Periodic tasks for auto-resolving tickets and generating support metrics.
"""

import asyncio
from celery import shared_task

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.support.auto_resolve import auto_resolve_tickets, get_auto_resolution_stats

logger = get_logger(__name__)


@shared_task
def auto_resolve_tickets_task():
    """Run auto-resolution every 6 hours."""
    async def _run():
        async with AsyncSessionLocal() as db:
            await auto_resolve_tickets(db)
    asyncio.run(_run())
    logger.info("Auto-resolve tickets task completed")


@shared_task
def generate_support_stats_task():
    """Generate and cache support stats daily."""
    async def _run():
        async with AsyncSessionLocal() as db:
            stats = await get_auto_resolution_stats(db, days=30)
            logger.info(f"Support stats: {stats}")
    asyncio.run(_run())
