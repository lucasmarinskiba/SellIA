"""Create the tables the LLM path depends on.

`user_api_keys` (per-business provider keys) and `catalog_items` (the product
catalogue the business-context builder reads) were never created on this
deployment. Both failures were swallowed, so the only visible symptom was that
every AI answer came back as a template -- indistinguishable from having no API
key configured.
"""

from __future__ import annotations

from app.core.logger import get_logger

logger = get_logger(__name__)


async def ensure_llm_support_tables() -> None:
    from app.core.database import engine

    tables = []
    try:
        from app.domains.subscriptions.models import UserAPIKey
        tables.append(UserAPIKey.__table__)
    except Exception as e:  # noqa: BLE001
        logger.warning("llm bootstrap: UserAPIKey model unavailable: %s", str(e)[:160])

    try:
        from app.domains.catalogs.models import CatalogItem
        tables.append(CatalogItem.__table__)
    except Exception as e:  # noqa: BLE001
        logger.warning("llm bootstrap: CatalogItem model unavailable: %s", str(e)[:160])

    created = 0
    for table in tables:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn, t=table: t.create(bind=sync_conn, checkfirst=True)
                )
            created += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("llm bootstrap: table %s skipped: %s", table.name, str(e)[:160])
    logger.info("✅ LLM support tables ensured (%s/%s)", created, len(tables))
