"""Add the columns `CatalogItem` declares but a pre-existing `catalog_items` table lacks.

`ensure_all_tables()` only ever CREATEs missing tables; it never ALTERs one that
already exists, and Alembic is disabled in this deployment (railway.toml starts
uvicorn directly). So `category`, `source_platform`, `external_id`, `listing_url`
and the re-sync dedup constraint -- added to the model after the table was first
created in production -- never reached the live table. The only way to apply them
was a superuser-only "Temporary" endpoint (POST /catalog/debug/add-listing-columns)
nobody called, which left every query that loads a `CatalogItem` failing with
`column catalog_items.category does not exist`: the catalog API, content generation,
the self-optimisation loop and the Celery tasks that read them.

This does what that endpoint did, at startup, idempotently.

A pre-existing row keeps NULL in all four columns, which is exactly what the model
declares (`nullable=True`) and what manually created items have. The unique
constraint cannot be violated by them: Postgres treats NULLs as distinct.
"""

from __future__ import annotations

from sqlalchemy import text

from app.core.logger import get_logger

logger = get_logger(__name__)

#: column -> DDL type, in the order they were added to the model.
_COLUMNS: dict[str, str] = {
    "category": "VARCHAR(120)",
    "source_platform": "VARCHAR(50)",
    "external_id": "VARCHAR(255)",
    "listing_url": "VARCHAR(1024)",
}
_CONSTRAINT = "uq_catalog_item_external"


async def ensure_catalog_item_columns() -> dict[str, list[str]]:
    """Bring `catalog_items` up to the model. Returns what it had to add.

    In the steady state (everything already there) this is two catalog reads and
    no DDL: `ADD COLUMN IF NOT EXISTS` takes an ACCESS EXCLUSIVE lock even when it
    does nothing, and this runs on every boot.
    """
    from app.core.database import engine

    added: dict[str, list[str]] = {"columns": [], "constraints": []}

    try:
        async with engine.connect() as conn:
            present = {
                row[0]
                for row in await conn.execute(
                    text(
                        "SELECT column_name FROM information_schema.columns "
                        "WHERE table_schema = current_schema() AND table_name = 'catalog_items'"
                    )
                )
            }
            has_constraint = bool(
                (
                    await conn.execute(
                        text("SELECT 1 FROM pg_constraint WHERE conname = :name"),
                        {"name": _CONSTRAINT},
                    )
                ).first()
            )
    # never block startup on this
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "catalog bootstrap: could not inspect catalog_items: %s", str(e)[:160]
        )
        return added

    if not present:
        return added  # the table does not exist yet; ensure_all_tables() will create it whole

    # One transaction PER statement: a failure inside a shared transaction poisons it
    # and silently rolls back the statements that had already succeeded.
    for column, ddl_type in _COLUMNS.items():
        if column in present:
            continue
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    text(
                        f"ALTER TABLE catalog_items ADD COLUMN IF NOT EXISTS {column} {ddl_type}"
                    )
                )
            added["columns"].append(column)
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "catalog bootstrap: column %s skipped: %s", column, str(e)[:160]
            )

    # Only once the columns it names exist. Constraints have no IF NOT EXISTS, hence the
    # guard (also covers two instances booting at once during a rolling deploy).
    needs_constraint = not has_constraint and {"source_platform", "external_id"} <= (
        present | set(added["columns"])
    )
    if needs_constraint:
        try:
            async with engine.begin() as conn:
                await conn.execute(
                    text(
                        "DO $$ BEGIN "
                        f"IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = '{_CONSTRAINT}') THEN "
                        f"ALTER TABLE catalog_items ADD CONSTRAINT {_CONSTRAINT} "
                        "UNIQUE (business_id, source_platform, external_id); "
                        "END IF; END $$;"
                    )
                )
            added["constraints"].append(_CONSTRAINT)
        except Exception as e:  # noqa: BLE001
            logger.warning(
                "catalog bootstrap: constraint %s skipped: %s",
                _CONSTRAINT,
                str(e)[:160],
            )

    if added["columns"] or added["constraints"]:
        logger.info(
            "✅ catalog_items brought up to the model: columns=%s constraints=%s",
            added["columns"],
            added["constraints"],
        )
    return added
