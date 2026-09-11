"""Keep the platform_bots table in step with the model.

create_all() creates a table but never alters one, and migrations are disabled on
this deployment, so a column added to PlatformBot after the table already exists
in production simply would not be there — and every read of it would fail with
"column does not exist", which the callers would report as ordinary emptiness.
"""

from __future__ import annotations

from app.core.logger import get_logger

logger = get_logger(__name__)

#: column name -> DDL type/default, in the order they were added to the model.
COLUMNS: dict[str, str] = {
    "active_hours": "JSONB",
    "after_hours_message": "TEXT",
    "escalate_on_frustration": "BOOLEAN NOT NULL DEFAULT FALSE",
    "hold_on_policy_violation": "BOOLEAN NOT NULL DEFAULT TRUE",
}


async def ensure_chatbot_tables() -> None:
    from sqlalchemy import text

    from app.core.database import engine
    from app.domains.chatbots.models import CHATBOT_TABLES

    for table in CHATBOT_TABLES:
        try:
            async with engine.begin() as conn:
                await conn.run_sync(
                    lambda sync_conn, t=table: t.create(bind=sync_conn, checkfirst=True)
                )
        except Exception as e:  # noqa: BLE001
            logger.warning("chatbots bootstrap: table %s skipped: %s", table.name, str(e)[:160])

    added = 0
    for column, ddl in COLUMNS.items():
        try:
            # One transaction per column: a failure on one must not roll back
            # the others (Postgres aborts the whole transaction on first error).
            async with engine.begin() as conn:
                await conn.execute(
                    text(f"ALTER TABLE platform_bots ADD COLUMN IF NOT EXISTS {column} {ddl}")
                )
            added += 1
        except Exception as e:  # noqa: BLE001
            logger.warning("chatbots bootstrap: column %s skipped: %s", column, str(e)[:160])
    logger.info("✅ platform_bots columns ensured (%s/%s)", added, len(COLUMNS))
