"""Create the websites/domains tables at startup (migrations disabled)."""

from __future__ import annotations

from app.core.logger import get_logger

logger = get_logger(__name__)


async def ensure_website_tables() -> None:
    from app.core.database import engine  # noqa: WPS433
    from app.domains.websites.models import WEBSITE_TABLES

    tables = list(WEBSITE_TABLES)
    try:
        # The storefront (products/cart/orders) hangs off a website, and its
        # tables had never been created either -- every call to the storefront
        # routes 500'd with relation "storefront_orders" does not exist.
        from app.domains.products.models import STOREFRONT_TABLES
        tables += list(STOREFRONT_TABLES)
    except Exception as e:  # noqa: BLE001
        logger.warning("storefront tables not available for bootstrap: %s", str(e)[:160])

    created = 0
    for table in tables:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn, t=table: t.create(bind=sync_conn, checkfirst=True)
                )
            created += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("websites bootstrap: table %s skipped: %s", table.name, str(e)[:160])
    logger.info("✅ websites/storefront tables ensured (%s/%s)", created, len(tables))
