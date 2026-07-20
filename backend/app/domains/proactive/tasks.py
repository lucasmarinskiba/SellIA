"""Proactive Outreach Engine Celery Tasks"""

import asyncio
import uuid
from celery import shared_task
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.proactive.engine import ProactiveEngine
from app.domains.proactive.service import ProactiveService

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


@shared_task(name="app.domains.proactive.tasks.detect_opportunities_task")
def detect_opportunities_task():
    """Run opportunity detection for all active businesses every 30 minutes."""

    async def _run():
        async with AsyncSessionLocal() as db:
            from app.domains.businesses.models import Business
            from sqlalchemy import select

            # Find all active businesses
            result = await db.execute(
                select(Business.id).where(Business.is_active == True)
            )
            business_ids = [row[0] for row in result.all()]

            total_created = 0
            for business_id in business_ids:
                try:
                    engine = ProactiveEngine(db)
                    opportunities = await engine.detect_opportunities(business_id)
                    total_created += len(opportunities)
                    logger.info(
                        f"Detected {len(opportunities)} opportunities for business {business_id}"
                    )
                except Exception as e:
                    logger.exception(
                        f"Opportunity detection failed for business {business_id}: {e}"
                    )

            return {"status": "ok", "businesses_scanned": len(business_ids), "opportunities_created": total_created}

    return _async_run(_run())


@shared_task(name="app.domains.proactive.tasks.send_outreach_task")
def send_outreach_task(opportunity_id: str):
    """Send a scheduled outreach message for a given opportunity."""

    async def _run():
        async with AsyncSessionLocal() as db:
            service = ProactiveService(db)
            result = await service.execute_outreach(uuid.UUID(opportunity_id))
            return result

    return _async_run(_run())
