"""Create forecasting tables at startup (migrations disabled in this deploy)."""

from __future__ import annotations

from app.core.logger import get_logger

logger = get_logger(__name__)


async def ensure_forecasting_tables() -> None:
    from app.core.database import engine  # noqa: WPS433
    from app.domains.forecasting.models_db import FORECASTING_TABLES

    created = 0
    for table in FORECASTING_TABLES:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(lambda c, t=table: t.create(bind=c, checkfirst=True))
            created += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("forecasting bootstrap: table %s skipped: %s", table.name, str(e)[:160])
    logger.info("✅ forecasting tables ensured (%s/%s)", created, len(FORECASTING_TABLES))
