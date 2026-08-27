"""Background loop driving the cold-lead follow-up scan (Task 5).

There's no generic cron/beat infrastructure in this app — app.core.scheduler
is a Redis delay-queue for scheduled emails, not a periodic-job runner — so
this follows the same self-contained pattern already used for the email
task processor (app.core.task_processor): an infinite `while running` loop
started with asyncio.create_task() during the FastAPI lifespan and cancelled
on shutdown.
"""

import asyncio

from app.core.logger import get_logger

logger = get_logger(__name__)

FOLLOWUP_SCAN_INTERVAL_SECONDS = 1800  # 30 min — cold-lead detection doesn't need tighter polling

_running = False


async def run_followup_loop() -> None:
    """Runs forever until stop_followup_loop() flips the flag."""
    global _running
    _running = True
    logger.info("🔁 Follow-up scheduler started")

    from app.core.database import AsyncSessionLocal
    from app.domains.channels.followup_service import scan_and_send_followups

    while _running:
        try:
            async with AsyncSessionLocal() as db:
                await scan_and_send_followups(db)
        except Exception as e:
            logger.error(f"Follow-up loop iteration failed: {e}")

        await asyncio.sleep(FOLLOWUP_SCAN_INTERVAL_SECONDS)


def stop_followup_loop() -> None:
    global _running
    _running = False
    logger.info("🛑 Follow-up scheduler stopped")
