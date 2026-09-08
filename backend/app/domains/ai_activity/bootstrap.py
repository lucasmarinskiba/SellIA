"""Create the ai_activity tables at startup (migrations disabled)."""

from __future__ import annotations

from app.core.logger import get_logger

logger = get_logger(__name__)


async def ensure_ai_activity_tables() -> None:
    from app.core.database import engine  # noqa: WPS433
    from app.domains.ai_activity.models import AI_ACTIVITY_TABLES

    created = 0
    for table in AI_ACTIVITY_TABLES:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn, t=table: t.create(bind=sync_conn, checkfirst=True)
                )
            created += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("ai_activity bootstrap: table %s skipped: %s", table.name, str(e)[:160])
    logger.info("✅ ai_activity tables ensured (%s/%s)", created, len(AI_ACTIVITY_TABLES))
