"""Create the business_links table at startup (migrations are disabled here)."""

from __future__ import annotations

from app.core.logger import get_logger

logger = get_logger(__name__)


async def ensure_web_presence_tables() -> None:
    from app.core.database import engine
    from app.domains.web_presence.models import WEB_PRESENCE_TABLES

    for table in WEB_PRESENCE_TABLES:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn, t=table: t.create(bind=sync_conn, checkfirst=True)
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("web_presence bootstrap: table %s skipped: %s", table.name, str(e)[:160])
    logger.info("✅ web_presence tables ensured")
