"""Retención de datos de Google Places.

Google permite guardar el place_id sin límite de tiempo, pero no el resto del
contenido del lugar (nombre, teléfono, dirección, web, rating) más allá de un
plazo corto. Pasados RETENTION_DAYS desde la ingesta, la purga deja solo el
place_id. Así el lead no se vuelve a importar en la próxima búsqueda, y el
resto de los datos de contacto deja de existir.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.growth.models import InboundLead

logger = logging.getLogger(__name__)

RETENTION_DAYS = 30
PURGE_BATCH_SIZE = 500
PLACES_SOURCE_PREFIX = "google_places:"


def redact_place_contact(contact_info: dict[str, Any] | None) -> dict[str, Any]:
    """Devuelve solo lo que Places permite conservar: el place_id."""
    place_id = (contact_info or {}).get("place_id")
    return {"place_id": place_id} if place_id else {}


async def purge_expired_place_contacts(
    db: AsyncSession, now: datetime | None = None
) -> int:
    """Redacta contact_info de los leads de Places ingeridos hace más de RETENTION_DAYS.

    Recorre por lotes ordenados por id (keyset), así la purga no carga toda la
    tabla en memoria. Hace commit por lote. Devuelve la cantidad de leads redactados.
    """
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(days=RETENTION_DAYS)
    conditions = [
        InboundLead.source_detail.startswith(PLACES_SOURCE_PREFIX, autoescape=True),
        InboundLead.first_touch_at < cutoff,
    ]

    purged = 0
    last_id = None
    while True:
        keyset = [InboundLead.id > last_id] if last_id is not None else []
        stmt = (
            select(InboundLead)
            .where(*conditions, *keyset)
            .order_by(InboundLead.id)
            .limit(PURGE_BATCH_SIZE)
        )
        leads = (await db.execute(stmt)).scalars().all()
        if not leads:
            break

        # Capturar el id antes del commit: después del commit el objeto expira
        # y leer un atributo fuera de la sesión async dispara MissingGreenlet.
        last_id = leads[-1].id
        batch_purged = 0
        for lead in leads:
            current = lead.contact_info or {}
            redacted = redact_place_contact(current)
            if redacted != current:
                lead.contact_info = redacted
                batch_purged += 1

        if batch_purged:
            await db.commit()
            purged += batch_purged

        if len(leads) < PURGE_BATCH_SIZE:
            break

    logger.info(
        "Places retention: %d leads redactados (corte %s)", purged, cutoff.isoformat()
    )
    return purged
