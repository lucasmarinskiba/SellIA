"""Auto-Responder Celery Tasks"""

from celery import shared_task
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.domains.agents.auto_responder.service import check_and_respond
from app.domains.businesses.models import Business
from app.core.logger import get_logger

logger = get_logger(__name__)


@shared_task(name="app.domains.agents.auto_responder.tasks.auto_responder_check_task")
def auto_responder_check_task():
    """Celery task that runs every 5 minutes to check auto-responder rules."""
    import asyncio
    asyncio.run(_run_check())


async def _run_check():
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(Business).where(Business.is_active == True)
            )
            businesses = result.scalars().all()

            for business in businesses:
                try:
                    responses = await check_and_respond(db, business.id)
                    if responses:
                        logger.info(
                            f"Auto-responder sent {len(responses)} responses for business {business.id}"
                        )
                except Exception as e:
                    logger.warning(f"Auto-responder failed for business {business.id}: {e}")
        except Exception as e:
            logger.error(f"Auto-responder check task failed: {e}")
