"""Add `business_contexts.contact_email` to an already-existing table.

`create_all()` only creates missing tables, so the live `business_contexts` table keeps its old shape. Alembic is
disabled in this deployment; the column is added here at startup, the same way app/db/locations_bootstrap.py
handles `locations.timezone`.

Existing profiles get NULL: no contact yet, so post-visit mail for those businesses waits until one is set.
"""

from sqlalchemy import text

from app.core.logger import get_logger

logger = get_logger(__name__)

_DDL = "ALTER TABLE business_contexts ADD COLUMN IF NOT EXISTS contact_email VARCHAR(255)"


async def ensure_business_contact_email_column() -> bool:
    """Add the column when it is missing. Returns True when this call added it."""
    from app.core.database import engine

    try:
        async with engine.connect() as conn:
            columns = {
                row[0]
                for row in await conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema = current_schema() AND table_name = 'business_contexts'"
                    )
                )
            }
    except Exception as e:  # noqa: BLE001 -- never block startup on this
        logger.warning("business contact bootstrap: could not inspect business_contexts: %s", str(e)[:160])
        return False

    if not columns:
        return False  # the table does not exist yet; ensure_all_tables() creates it whole
    if "contact_email" in columns:
        return False

    try:
        async with engine.begin() as conn:
            await conn.execute(text(_DDL))
    except Exception as e:  # noqa: BLE001
        logger.warning("business contact bootstrap: column skipped: %s", str(e)[:180])
        return False

    logger.info("✅ business_contexts.contact_email column added")
    return True
