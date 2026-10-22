"""Reloj UTC para el backend.

``utc_now()`` devuelve un datetime naive en UTC, igual que el deprecado
``datetime.utcnow()``. Las columnas de la base son naive, así que mantener ese
valor evita cambiar cómo se guardan o se comparan las fechas. Para algo nuevo
que necesite zona horaria, usar ``datetime.now(UTC)`` directamente.
"""

from datetime import UTC, datetime


def utc_now() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)
