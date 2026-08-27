"""Create the ad-budget autopilot tables at startup (migrations disabled)."""

from __future__ import annotations

from app.core.logger import get_logger

logger = get_logger(__name__)


async def ensure_ad_budget_tables() -> None:
    from app.core.database import engine  # noqa: WPS433
    from app.domains.ad_budget.models import AD_BUDGET_TABLES

    created = 0
    for table in AD_BUDGET_TABLES:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn, t=table: t.create(bind=sync_conn, checkfirst=True)
                )
            created += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("ad_budget bootstrap: table %s skipped: %s", table.name, str(e)[:160])
    logger.info("✅ ad_budget tables ensured (%s/%s)", created, len(AD_BUDGET_TABLES))
