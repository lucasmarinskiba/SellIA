"""Beat task: send the post-visit messages that are due. Nothing is sent unless OFFLINE_SEQUENCE_SEND_ENABLED is on."""

from datetime import datetime, timezone

from celery import shared_task

from app.core.async_bridge import run_async
from app.core.database import AsyncSessionLocal


@shared_task
def process_offline_sequence_jobs() -> dict[str, int]:
    from app.core.config import get_settings
    from app.core.email_service import send_email
    from app.domains.sequences.offline_sequence_jobs import send_due_jobs

    async def _run() -> dict[str, int]:
        async with AsyncSessionLocal() as db:
            return await send_due_jobs(
                db,
                now=datetime.now(timezone.utc),
                enabled=get_settings().OFFLINE_SEQUENCE_SEND_ENABLED,
                sender=send_email,
            )

    return run_async(_run())
