"""Harvey automatic loop: one pass per enabled business, every 15 minutes."""

from celery import shared_task
from sqlalchemy import select

from app.core.async_bridge import run_async
from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.businesses.models import Business
from app.domains.harvey.models import HarveyProfile
from app.domains.harvey.service import HarveyService

logger = get_logger(__name__)


@shared_task(name="app.tasks.harvey_tasks.run_harvey_cycles")
def run_harvey_cycles():
    """Read inboxes, draft (if the business allows it), discover, and send what was approved."""

    async def _run():
        async with AsyncSessionLocal() as db:
            business_ids = (
                await db.execute(
                    select(HarveyProfile.business_id).where(HarveyProfile.is_enabled.is_(True))
                )
            ).scalars().all()

        ran = failed = 0
        for business_id in business_ids:
            try:
                async with AsyncSessionLocal() as biz_db:
                    business = (
                        await biz_db.execute(select(Business).where(Business.id == business_id))
                    ).scalar_one_or_none()
                    if business is None or not business.is_active:
                        continue
                    service = HarveyService(biz_db)
                    profile = await service.get_or_create_profile(business)
                    await service.run_cycle(business, profile)
                ran += 1
            except Exception as e:  # one business must never stop the others
                failed += 1
                logger.error(f"harvey cycle failed for business {business_id}: {type(e).__name__}")

        logger.info(f"harvey: {ran} cycles run, {failed} failed")
        return {"cycles": ran, "failed": failed}

    return run_async(_run())
