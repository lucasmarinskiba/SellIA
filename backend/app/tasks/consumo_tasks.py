"""
Consumo Celery Tasks

Periodic tasks for Predictive Churn Shield and onboarding progress updates.
"""

import asyncio
from celery import shared_task

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.consumo.service import run_churn_analysis

logger = get_logger(__name__)


@shared_task
def churn_shield_analysis_task():
    """Run daily churn risk analysis for all active users."""
    async def _run():
        async with AsyncSessionLocal() as db:
            signals = await run_churn_analysis(db)
            logger.info(f"Churn Shield: {len(signals)} risk signals detected")
    asyncio.run(_run())
