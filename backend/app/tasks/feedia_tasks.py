"""Beat task: deliver the queued sales/refunds to feedIA. Does nothing until FEEDIA_BASE_URL and SELLIA_WEBHOOK_SECRET are set."""

from celery import shared_task

from app.core.async_bridge import run_async
from app.core.database import AsyncSessionLocal


@shared_task
def deliver_feedia_events() -> dict[str, int]:
    from app.core.config import get_settings
    from app.domains.feedia_link.delivery import deliver_due

    settings = get_settings()

    async def _run() -> dict[str, int]:
        async with AsyncSessionLocal() as db:
            return await deliver_due(db, base_url=settings.FEEDIA_BASE_URL, secret=settings.SELLIA_WEBHOOK_SECRET)

    return run_async(_run())
