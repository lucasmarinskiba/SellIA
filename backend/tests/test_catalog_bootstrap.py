"""`catalog_items` in production lacked four columns the model declares.

`create_all()` never ALTERs an existing table, so every query loading a `CatalogItem`
failed with `column catalog_items.category does not exist`. These tests rebuild that
exact production state and pin the startup bootstrap that repairs it.
"""

from __future__ import annotations

import pytest
from sqlalchemy import event, select, text
from sqlalchemy.exc import DBAPIError

_DROP_ALL = (
    "ALTER TABLE catalog_items DROP CONSTRAINT IF EXISTS uq_catalog_item_external",
    "ALTER TABLE catalog_items DROP COLUMN IF EXISTS category",
    "ALTER TABLE catalog_items DROP COLUMN IF EXISTS source_platform",
    "ALTER TABLE catalog_items DROP COLUMN IF EXISTS external_id",
    "ALTER TABLE catalog_items DROP COLUMN IF EXISTS listing_url",
)


async def _columns(session) -> set[str]:
    rows = await session.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = 'catalog_items'"
        )
    )
    return {r[0] for r in rows}


async def _constraint_exists(session) -> bool:
    row = await session.execute(
        text("SELECT 1 FROM pg_constraint WHERE conname = 'uq_catalog_item_external'")
    )
    return row.first() is not None


@pytest.fixture
async def production_shaped_catalog(db_session):
    """catalog_items exactly as production has it: without the four late columns."""
    for stmt in _DROP_ALL:
        await db_session.execute(text(stmt))
    await db_session.commit()
    yield db_session
    # Leave the shared test schema as the rest of the suite expects it.
    from app.db.catalog_bootstrap import ensure_catalog_item_columns

    await ensure_catalog_item_columns()


async def test_model_query_fails_on_the_production_shaped_table(production_shaped_catalog) -> None:
    """Documents the bug: this is the error the Celery workers were logging."""
    from app.domains.catalogs.models import CatalogItem

    with pytest.raises(DBAPIError, match="category"):
        await production_shaped_catalog.execute(select(CatalogItem).limit(1))
    await production_shaped_catalog.rollback()


async def test_bootstrap_adds_columns_constraint_and_the_query_works(production_shaped_catalog) -> None:
    from app.db.catalog_bootstrap import ensure_catalog_item_columns
    from app.domains.catalogs.models import CatalogItem

    added = await ensure_catalog_item_columns()

    assert set(added["columns"]) == {"category", "source_platform", "external_id", "listing_url"}
    assert added["constraints"] == ["uq_catalog_item_external"]
    session = production_shaped_catalog
    assert {"category", "source_platform", "external_id", "listing_url"} <= await _columns(session)
    assert await _constraint_exists(session)
    # The query that was failing now runs.
    await session.execute(select(CatalogItem).limit(1))


async def test_bootstrap_is_idempotent_and_takes_no_locks_when_up_to_date(production_shaped_catalog) -> None:
    from app.core.database import engine
    from app.db.catalog_bootstrap import ensure_catalog_item_columns

    await ensure_catalog_item_columns()  # first run repairs

    ddl: list[str] = []

    def record(conn, cursor, statement, parameters, context, executemany) -> None:
        if statement.lstrip().upper().startswith(("ALTER", "CREATE", "DO ")):
            ddl.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", record)
    try:
        again = await ensure_catalog_item_columns()
    finally:
        event.remove(engine.sync_engine, "before_cursor_execute", record)

    assert again == {"columns": [], "constraints": []}
    assert ddl == [], f"steady state must not run DDL (ACCESS EXCLUSIVE locks on every boot): {ddl}"


async def test_existing_rows_survive_with_null_in_the_new_columns(production_shaped_catalog, test_user) -> None:
    """The repair must not touch data: rows created before keep NULL, like manual items."""
    from uuid import uuid4

    from app.db.catalog_bootstrap import ensure_catalog_item_columns
    from app.domains.businesses.models import Business

    session = production_shaped_catalog
    business = Business(user_id=test_user.id, name="Cat Co")
    session.add(business)
    await session.commit()
    item_id = uuid4()
    # Raw SQL: the ORM cannot insert a CatalogItem while the table lacks its columns.
    await session.execute(
        text(
            "INSERT INTO catalog_items (id, business_id, type, name, price, currency, is_available, "
            "extra_data, images, tags, is_active) "
            "VALUES (:i, :b, 'GOOD', 'Old item', 10, 'ARS', true, '{}', '[]', '[]', true)"
        ),
        {"i": item_id, "b": business.id},
    )
    await session.commit()

    await ensure_catalog_item_columns()

    row = (
        await session.execute(
            text(
                "SELECT name, category, source_platform, external_id, listing_url "
                "FROM catalog_items WHERE id = :i"
            ),
            {"i": item_id},
        )
    ).one()
    assert tuple(row) == ("Old item", None, None, None, None)

    await session.execute(text("DELETE FROM catalog_items WHERE id = :i"), {"i": item_id})
    await session.delete(business)
    await session.commit()
