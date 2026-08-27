"""Create the ledger tables at startup.

Migrations are disabled in this deployment (see backend/entrypoint.sh) and
the CoreBase-wide create_all is intentionally skipped because of messy FK
graphs elsewhere. The ledger models have a small, self-contained FK graph
(only -> businesses), so we create just those tables here, each in its own
transaction so one failure never poisons the rest.
"""

from __future__ import annotations

from app.core.logger import get_logger

logger = get_logger(__name__)


async def ensure_ledger_tables() -> None:
    from app.core.database import Base, engine  # noqa: WPS433 (late import)
    from app.domains.ledger.models import LEDGER_TABLES

    created = 0
    for table in LEDGER_TABLES:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn, t=table: t.create(bind=sync_conn, checkfirst=True)
                )
            created += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("ledger bootstrap: table %s skipped: %s", table.name, str(e)[:160])
    logger.info("✅ ledger tables ensured (%s/%s)", created, len(LEDGER_TABLES))
