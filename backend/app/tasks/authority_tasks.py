"""Scheduled authority measurement.

The trend chart is only real history if something measures on a cadence. Until
now a snapshot was written when the user happened to open the screen, so a month
of work followed by a single visit produced one point and no story.

This runs weekly for every account that has something to measure, which makes
"¿mejoró?" answerable without asking the user to remember to press a button.
It is internal and read-only towards the outside world: it writes snapshots and
refreshes the action list, and sends nothing to anyone.
"""

from __future__ import annotations

import asyncio

from app.core.logger import get_logger
from app.tasks.celery_app import celery_app

logger = get_logger(__name__)


async def _measure_all() -> dict[str, int]:
    from sqlalchemy import select

    from app.core.database import AsyncSessionLocal
    from app.domains.authority.service import capture_snapshot
    from app.domains.businesses.models import Business
    from app.domains.users.models import User

    measured, failed = 0, 0
    async with AsyncSessionLocal() as db:
        # Only accounts with a business: an empty account would produce an
        # endless series of identical zeros and no insight.
        result = await db.execute(
            select(User).where(
                User.id.in_(select(Business.user_id).where(Business.user_id.isnot(None)))
            )
        )
        users = list(result.scalars().all())

    for user in users:
        try:
            async with AsyncSessionLocal() as db:
                await capture_snapshot(db, user, force=True)
            measured += 1
        except Exception as e:  # noqa: BLE001 -- one account must not stop the sweep
            logger.warning("authority weekly: %s failed: %s", user.id, str(e)[:200])
            failed += 1

    logger.info("authority weekly measurement: %s ok, %s failed", measured, failed)
    return {"measured": measured, "failed": failed}


@celery_app.task(name="app.tasks.authority_tasks.weekly_authority_snapshot")
def weekly_authority_snapshot() -> dict[str, int]:
    """Measure every account's authority so the trend keeps advancing on its own."""
    return asyncio.run(_measure_all())
