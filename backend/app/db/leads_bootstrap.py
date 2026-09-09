"""Add the `leads.user_id` owner column to an already-existing table.

`Base.metadata.create_all()` (app/db/database.py's init_db) only ever CREATEs
missing tables -- it never ALTERs one that already exists, so declaring the
column on the model is not enough for a live database that already has
`leads`. Alembic is disabled in this deployment (railway.toml starts uvicorn
directly), so the column is added here, idempotently, at startup -- the same
pattern the other domains use for their tables.

Existing rows keep user_id NULL on purpose: they were created when nothing
recorded an owner, so they belong to nobody. They stay visible as the public
demo's data and are never shown to a signed-in account as its own.
"""

from __future__ import annotations

from sqlalchemy import text

from app.core.logger import get_logger

logger = get_logger(__name__)


async def ensure_leads_owner_column() -> None:
    from app.db.database import engine

    statements = (
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS user_id UUID",
        "CREATE INDEX IF NOT EXISTS ix_leads_user_id ON leads (user_id)",
        "CREATE INDEX IF NOT EXISTS idx_lead_owner_status ON leads (user_id, status, deleted_at)",
        # The old global UNIQUE(email) made per-account leads impossible: the
        # first account to store juan@cliente.com locked that address out for
        # everyone else. Uniqueness belongs to (owner, email) instead. NULL
        # user_id rows (the legacy demo rows) are exempt, since Postgres
        # treats NULLs as distinct in a unique index.
        "ALTER TABLE leads DROP CONSTRAINT IF EXISTS leads_email_key",
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_leads_user_email ON leads (user_id, email)",
    )
    # One transaction PER statement: a single failure inside a shared
    # transaction poisons it and silently rolls back the ones that had already
    # succeeded (the same trap documented in app/db/database.py's init_db).
    ok = 0
    for stmt in statements:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(stmt))
            ok += 1
        except Exception as e:  # noqa: BLE001 -- never block startup on this
            logger.warning("leads bootstrap statement skipped (%s): %s", stmt[:48], str(e)[:180])
    logger.info("✅ leads owner-column bootstrap (%s/%s statements)", ok, len(statements))
