"""SellIA Department Tasks — Celery tasks for the virtual company."""

from datetime import UTC, datetime
from uuid import UUID

from celery import shared_task
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.async_bridge import run_async
from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.bi.services import BiService
from app.domains.businesses.models import Business
from app.domains.finance.services import FinanceService
from app.domains.orchestration.director import SellIADirector
from app.domains.retention.services import RetentionService

logger = get_logger(__name__)


async def _get_active_business_ids(db: AsyncSession) -> list[UUID]:
    """Fetch IDs of all active businesses."""
    result = await db.execute(select(Business.id).where(Business.is_active == True))
    return [row[0] for row in result.all()]


@shared_task(name="app.tasks.selia_tasks.selia_director_daily")
def selia_director_daily(business_id: str | None = None):
    """Run daily briefing for a business or all active businesses."""

    async def _run_single(bid: UUID):
        async with AsyncSessionLocal() as db:
            director = SellIADirector(db)
            result = await director.run_daily_briefing(bid)
            logger.info(f"SellIA Director daily briefing: {result}")
            return result

    async def _run_all():
        async with AsyncSessionLocal() as db:
            business_ids = await _get_active_business_ids(db)
        results = []
        for bid in business_ids:
            try:
                results.append(await _run_single(bid))
            except Exception:
                logger.exception(f"selia_director_daily failed for {bid}")
        return {"status": "ok", "processed": len(results), "total": len(business_ids)}

    if business_id:
        return run_async(_run_single(UUID(business_id)))
    return run_async(_run_all())


@shared_task(name="app.tasks.selia_tasks.rfm_segmentation")
def rfm_segmentation(business_id: str | None = None):
    """Calculate RFM segments for all customers of a business or all active businesses."""

    async def _run_single(bid: UUID):
        async with AsyncSessionLocal() as db:
            service = RetentionService(db)
            await service.calculate_rfm_for_business(bid)
            logger.info(f"RFM segmentation completed for business {bid}")
            return {"status": "ok", "business_id": str(bid)}

    async def _run_all():
        async with AsyncSessionLocal() as db:
            business_ids = await _get_active_business_ids(db)
        results = []
        for bid in business_ids:
            try:
                results.append(await _run_single(bid))
            except Exception:
                logger.exception(f"rfm_segmentation failed for {bid}")
        return {"status": "ok", "processed": len(results), "total": len(business_ids)}

    if business_id:
        return run_async(_run_single(UUID(business_id)))
    return run_async(_run_all())


@shared_task(name="app.tasks.selia_tasks.payment_reminder_check")
def payment_reminder_check(business_id: str | None = None):
    """Check and send pending payment reminders for a business or all active businesses."""

    async def _run_single(bid: UUID):
        async with AsyncSessionLocal() as db:
            service = FinanceService(db)
            reminders = await service.get_pending_reminders(bid)
            sent = 0
            for reminder in reminders:
                reminder.status = "sent"
                reminder.sent_at = datetime.now(UTC)
                sent += 1
            await db.commit()
            logger.info(f"Payment reminders sent: {sent} for business {bid}")
            return {"status": "ok", "sent": sent, "business_id": str(bid)}

    async def _run_all():
        async with AsyncSessionLocal() as db:
            business_ids = await _get_active_business_ids(db)
        total_sent = 0
        for bid in business_ids:
            try:
                result = await _run_single(bid)
                total_sent += result.get("sent", 0)
            except Exception:
                logger.exception(f"payment_reminder_check failed for {bid}")
        return {
            "status": "ok",
            "total_sent": total_sent,
            "total_businesses": len(business_ids),
        }

    if business_id:
        return run_async(_run_single(UUID(business_id)))
    return run_async(_run_all())


@shared_task(name="app.tasks.selia_tasks.bi_analytics_daily")
def bi_analytics_daily(business_id: str | None = None):
    """Generate daily BI analytics for a business or all active businesses."""

    async def _run_single(bid: UUID):
        async with AsyncSessionLocal() as db:
            service = BiService(db)
            period = datetime.now(UTC).strftime("%Y-%m-%d")
            await service.generate_funnel_report(bid, period, "daily")
            logger.info(f"BI analytics generated for business {bid}")
            return {"status": "ok", "business_id": str(bid)}

    async def _run_all():
        async with AsyncSessionLocal() as db:
            business_ids = await _get_active_business_ids(db)
        results = []
        for bid in business_ids:
            try:
                results.append(await _run_single(bid))
            except Exception:
                logger.exception(f"bi_analytics_daily failed for {bid}")
        return {"status": "ok", "processed": len(results), "total": len(business_ids)}

    if business_id:
        return run_async(_run_single(UUID(business_id)))
    return run_async(_run_all())
