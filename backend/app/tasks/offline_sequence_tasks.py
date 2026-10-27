"""Beat task: send the post-visit messages that are due. Nothing is sent unless OFFLINE_SEQUENCE_SEND_ENABLED is on."""

from datetime import datetime, timezone

from celery import shared_task

from app.core.async_bridge import run_async
from app.core.database import AsyncSessionLocal


@shared_task
def process_offline_sequence_jobs() -> dict[str, int]:
    from app.core.config import get_settings
    from app.core.email_service import send_email
    from app.core.logger import get_logger
    from app.domains.sequences.offline_sequence_jobs import send_due_jobs

    settings = get_settings()
    if settings.OFFLINE_SEQUENCE_SEND_ENABLED and not settings.TRACKING_BASE_URL:
        get_logger(__name__).warning(
            "Post-visit sending is enabled but TRACKING_BASE_URL is not set: messages stay pending until it is."
        )

    async def _send(to: str, subject: str, html: str, from_name: str) -> bool:
        return await send_email(to, subject, html, from_name=from_name)

    async def _run() -> dict[str, int]:
        async with AsyncSessionLocal() as db:
            return await send_due_jobs(
                db,
                now=datetime.now(timezone.utc),
                enabled=settings.OFFLINE_SEQUENCE_SEND_ENABLED,
                sender=_send,
                base_url=settings.TRACKING_BASE_URL,
                secret=settings.SECRET_KEY,
            )

    return run_async(_run())
