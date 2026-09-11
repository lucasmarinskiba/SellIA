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
    await _scope_order_number_to_business()


async def _scope_order_number_to_business() -> None:
    """Make order_number unique per business instead of globally.

    The column was created UNIQUE on its own, so the second account to issue
    "1001" — or to import a marketplace order whose number another account
    already had — hit a duplicate-key error on an order that was genuinely
    theirs. create_all() never alters an existing table, so the live constraint
    has to be swapped by hand (migrations are disabled on this deployment).
    """
    from sqlalchemy import text

    from app.core.database import engine

    statements = [
        # Two shapes to clear, because it is not obvious which one exists:
        # `unique=True` alone would have produced the constraint
        # orders_order_number_key, but `unique=True, index=True` — what the
        # model actually had — makes SQLAlchemy emit
        # `CREATE UNIQUE INDEX ix_orders_order_number` instead. The first
        # attempt at this migration only dropped the constraint, so the unique
        # INDEX survived and order numbers stayed globally unique in production.
        "ALTER TABLE orders DROP CONSTRAINT IF EXISTS orders_order_number_key",
        "DROP INDEX IF EXISTS ix_orders_order_number",
        """
        CREATE UNIQUE INDEX IF NOT EXISTS uq_orders_business_number
        ON orders (business_id, order_number)
        WHERE order_number IS NOT NULL
        """,
        # Recreated without UNIQUE: lookups by number still want an index.
        "CREATE INDEX IF NOT EXISTS ix_orders_order_number ON orders (order_number)",
    ]
    for statement in statements:
        try:
            # One transaction each: a statement that cannot apply (duplicate
            # numbers already in one business, say) must not undo the others.
            async with engine.begin() as conn:
                await conn.execute(text(statement))
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "orders bootstrap: order_number constraint step skipped (%s): %s",
                statement.strip().split("\n")[0][:60],
                str(e)[:160],
            )
