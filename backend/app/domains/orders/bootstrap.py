"""Create the orders tables at startup (migrations are disabled here).

`orders`, `revenue_events` and `payment_integrations` were never created by
anything, so every query against them answered `relation "orders" does not
exist`. Nothing crashed visibly because each caller catches the error and
reports zero revenue -- which is indistinguishable from an account that simply
has not sold anything yet. It also poisoned the surrounding transaction, which
is how it eventually took down an unrelated screen.
"""

from __future__ import annotations

from app.core.logger import get_logger

logger = get_logger(__name__)


async def ensure_orders_tables() -> None:
    from app.core.database import engine
    from app.domains.orders.models import Order, PaymentIntegration, RevenueEvent

    tables = [Order.__table__, RevenueEvent.__table__, PaymentIntegration.__table__]
    created = 0
    for table in tables:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn, t=table: t.create(bind=sync_conn, checkfirst=True)
                )
            created += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("orders bootstrap: table %s skipped: %s", table.name, str(e)[:160])
    logger.info("✅ orders tables ensured (%s/%s)", created, len(tables))
