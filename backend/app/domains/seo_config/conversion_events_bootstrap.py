"""Patch `conversion_events` with a dedupe column + unique index.

`schema_bootstrap.ensure_all_tables()` only ever CREATEs missing tables — it
never ALTERs one that already exists. `conversion_events` already exists
wherever FOMO conversion tracking shipped, so declaring `external_event_id`
on the model is not enough: without this patch, the column (and the unique
index that makes duplicate-webhook ingestion safe) would be missing on those
databases. Same pattern and reasoning as positioning_bootstrap.py.

Why this exists: the Mercado Libre webhook (and any other webhook source)
used to dedupe by SELECTing for an existing row, then INSERTing if none was
found — classic check-then-insert. Two notifications for the same order
arriving close together (Mercado Libre does resend) could both pass the
SELECT before either commits, double-counting the sale in FOMO stats and
positioning signals. A partial unique index makes the database the single
source of truth for "already recorded", and the insert path now catches the
resulting IntegrityError as an expected duplicate instead of a failure.
"""

from __future__ import annotations

from sqlalchemy import text

from app.core.logger import get_logger

logger = get_logger(__name__)


async def ensure_conversion_event_dedupe_column() -> None:
    from app.db.database import engine

    statements = (
        "ALTER TABLE conversion_events ADD COLUMN IF NOT EXISTS external_event_id VARCHAR(255)",
        # Partial: most conversion sources (manual logs, sources with no stable
        # per-order id) leave this NULL, and NULLs must stay unconstrained.
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_conversion_dedupe ON conversion_events "
        "(business_id, platform_name, external_listing_id, external_event_id) "
        "WHERE external_event_id IS NOT NULL",
    )
    ok = 0
    for stmt in statements:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(stmt))
            ok += 1
        except Exception as e:  # noqa: BLE001 -- never block startup on this
            logger.warning("conversion_events bootstrap statement skipped (%s): %s", stmt[:60], str(e)[:180])
    logger.info("conversion_events dedupe column bootstrap (%s/%s statements)", ok, len(statements))
