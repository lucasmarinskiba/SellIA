"""Tareas de retención de datos de Google Places (ver places_retention)."""

from celery import shared_task

from app.core.async_bridge import run_async


@shared_task
def purge_expired_place_contacts_task() -> int:
    """Redacta datos de contacto de Places vencidos. Corre una vez al día."""

    async def _run() -> int:
        from app.core.database import AsyncSessionLocal
        from app.domains.lead_generation.places_retention import (
            purge_expired_place_contacts,
        )

        async with AsyncSessionLocal() as db:
            return await purge_expired_place_contacts(db)

    return run_async(_run())
