"""Harvey automatic loop: one pass per enabled business, every 15 minutes."""

from datetime import datetime, timedelta, timezone

from celery import shared_task
from sqlalchemy import select

from app.core.async_bridge import run_async
from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.alerts.models import Alert, AlertSeverity, AlertStatus
from app.domains.businesses.models import Business
from app.domains.harvey import weekly
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


WEEKLY_TITLE = "Tu semana con Harvey"


@shared_task(name="app.tasks.harvey_tasks.send_weekly_summaries")
def send_weekly_summaries():
    """Once a week, leave each active Harvey business an in-app alert with its week and what to do next."""

    async def _run():
        async with AsyncSessionLocal() as db:
            business_ids = (
                await db.execute(select(HarveyProfile.business_id).where(HarveyProfile.is_enabled.is_(True)))
            ).scalars().all()

        sent = skipped = failed = 0
        for business_id in business_ids:
            try:
                async with AsyncSessionLocal() as biz_db:
                    recent = (
                        await biz_db.execute(
                            select(Alert.id).where(
                                Alert.business_id == business_id,
                                Alert.title == WEEKLY_TITLE,
                                Alert.created_at >= datetime.now(timezone.utc) - timedelta(days=6),
                            )
                        )
                    ).first()
                    summary = await weekly.weekly_summary(biz_db, business_id)
                    active = summary["sent"] or summary["replies"]["total"] or summary["prospects_added"] or summary["pending_review"]
                    if recent or not active:  # no repeat within the week, and no noise for a week with nothing in it
                        skipped += 1
                        continue
                    title, body = weekly.alert_text(summary)
                    biz_db.add(
                        Alert(
                            business_id=business_id,
                            title=title,
                            description=body,
                            severity=AlertSeverity.INFO,
                            status=AlertStatus.UNREAD,
                            recommended_action=" ".join(summary["next_steps"][:3]) or None,
                            alert_metadata={"source": "harvey_weekly", "summary": summary},
                        )
                    )
                    await biz_db.commit()
                sent += 1
            except Exception as e:  # one business must never stop the others
                failed += 1
                logger.error(f"harvey weekly summary failed for business {business_id}: {type(e).__name__}")

        logger.info(f"harvey weekly: {sent} sent, {skipped} skipped, {failed} failed")
        return {"sent": sent, "skipped": skipped, "failed": failed}

    return run_async(_run())
