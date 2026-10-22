"""Add `locations.timezone` to an already-existing table.

`Base.metadata.create_all()` only ever CREATEs missing tables, so a live `locations` table keeps its old shape
and the model's new column is absent there. Alembic is disabled in this deployment, so the column is added
here at startup, the same way app/db/catalog_bootstrap.py handles `catalog_items`.

Existing locations get 'UTC', which is what every location already got implicitly: no figure moves until an
owner sets a zone.
"""

from __future__ import annotations

from sqlalchemy import text

from app.core.logger import get_logger

logger = get_logger(__name__)

_DDL = "ALTER TABLE locations ADD COLUMN IF NOT EXISTS timezone VARCHAR(64) NOT NULL DEFAULT 'UTC'"


async def ensure_location_timezone_column() -> bool:
    """Add the column when it is missing. Returns True when this call added it.

    In the steady state this is one catalog read and no DDL: `ADD COLUMN IF NOT EXISTS` takes an
    ACCESS EXCLUSIVE lock even when it does nothing, and this runs on every boot.
    """
    from app.core.database import engine

    try:
        async with engine.connect() as conn:
            columns = {
                row[0]
                for row in await conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema = current_schema() AND table_name = 'locations'"
                    )
                )
            }
    except Exception as e:  # noqa: BLE001 -- never block startup on this
        logger.warning("locations timezone bootstrap: could not inspect locations: %s", str(e)[:160])
        return False

    if not columns:
        return False  # the table does not exist yet; ensure_all_tables() creates it whole
    if "timezone" in columns:
        return False

    try:
        async with engine.begin() as conn:
            await conn.execute(text(_DDL))
    except Exception as e:  # noqa: BLE001
        logger.warning("locations timezone bootstrap: column skipped: %s", str(e)[:180])
        return False

    logger.info("✅ locations.timezone column added")
    return True
