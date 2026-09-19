"""Patch `positioning_recommendations` for store-level recommendations.

`schema_bootstrap.ensure_all_tables()` only ever CREATEs missing tables — it
never ALTERs one that already exists. `positioning_recommendations` already
exists wherever the link-level positioning score shipped, so declaring
`store_score_id` / a nullable `link_id` on the model is not enough: without
this patch, inserting a store-scoped recommendation would 500 on those
databases. Same pattern and reasoning as app/db/leads_bootstrap.py.

Must run AFTER ensure_all_tables(), because `store_score_id` references the
`store_positioning_scores` table that ensure_all_tables() creates.
"""

from __future__ import annotations

from sqlalchemy import text

from app.core.logger import get_logger

logger = get_logger(__name__)


async def ensure_positioning_recommendation_columns() -> None:
    from app.db.database import engine

    statements = (
        "ALTER TABLE positioning_recommendations ADD COLUMN IF NOT EXISTS store_score_id UUID "
        "REFERENCES store_positioning_scores(id) ON DELETE SET NULL",
        "ALTER TABLE positioning_recommendations ALTER COLUMN link_id DROP NOT NULL",
        "CREATE INDEX IF NOT EXISTS idx_store_score_recommendation ON positioning_recommendations (store_score_id)",
    )
    # One transaction PER statement: a failure inside a shared transaction would
    # poison it and silently roll back the statements that had already succeeded.
    ok = 0
    for stmt in statements:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(stmt))
            ok += 1
        except Exception as e:  # noqa: BLE001 -- never block startup on this
            logger.warning("positioning bootstrap statement skipped (%s): %s", stmt[:60], str(e)[:180])
    logger.info("positioning recommendation columns bootstrap (%s/%s statements)", ok, len(statements))
