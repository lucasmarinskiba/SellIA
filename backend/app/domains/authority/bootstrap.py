"""Create the authority tables at startup (migrations are disabled here)."""

from __future__ import annotations

from app.core.logger import get_logger

logger = get_logger(__name__)


async def ensure_authority_tables() -> None:
    from app.core.database import engine
    from app.domains.authority.models import AUTHORITY_TABLES

    for table in AUTHORITY_TABLES:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn, t=table: t.create(bind=sync_conn, checkfirst=True)
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("authority bootstrap: table %s skipped: %s", table.name, str(e)[:160])
    logger.info("✅ authority tables ensured")
