"""PostgreSQL index names are per schema: two tables must not declare the same one.

Models declare indexes by hand with generic names ("idx_business_metrics", "idx_rep_id", ...)
and several tables reuse them. CREATE INDEX of the second table then failed with DuplicateTable
and the whole table was silently skipped on every boot (awards, location_inventory,
payment_metrics, sales_rep_performance, journey_executions, ...).
``ensure_unique_index_names`` makes the names unique in memory before any DDL.
"""

from __future__ import annotations

import contextlib
import uuid

import pytest
from sqlalchemy import Column, Index, Integer, MetaData, Table, text

from app.db.schema_bootstrap import ensure_unique_index_names


def _table(metadata: MetaData, name: str, *indexes: Index) -> Table:
    return Table(name, metadata, Column("id", Integer, primary_key=True), Column("business_id", Integer), *indexes)


def _names(metadata: MetaData) -> list[str]:
    return sorted(ix.name for t in metadata.tables.values() for ix in t.indexes)


def test_a_name_shared_by_different_tables_gets_the_table_name() -> None:
    metadata = MetaData()
    _table(metadata, "alpha", Index("idx_business", "business_id"))
    _table(metadata, "beta", Index("idx_business", "business_id"))
    _table(metadata, "gamma", Index("idx_other", "business_id"))

    assert ensure_unique_index_names(metadata) == {"renamed": 2, "dropped": 0}

    assert _names(metadata) == ["idx_business_alpha", "idx_business_beta", "idx_other"]  # the unique one is untouched


def test_the_same_name_twice_on_one_table_keeps_a_single_copy() -> None:
    """``index=True`` plus an explicit Index on the same column produced the same name twice."""
    metadata = MetaData()
    table = _table(metadata, "alpha", Index("ix_alpha_business_id", "business_id"), Index("ix_alpha_business_id", "business_id"))

    assert ensure_unique_index_names(metadata) == {"renamed": 0, "dropped": 1}
    assert len(table.indexes) == 1


def test_long_names_stay_within_the_postgresql_limit_and_stay_unique() -> None:
    metadata = MetaData()
    base = "idx_" + "x" * 40
    _table(metadata, "a_table_with_a_rather_long_name_one", Index(base, "business_id"))
    _table(metadata, "a_table_with_a_rather_long_name_two", Index(base, "business_id"))

    ensure_unique_index_names(metadata)

    names = _names(metadata)
    assert len(set(names)) == 2 and all(len(n) <= 63 for n in names)


def test_running_it_twice_changes_nothing_more() -> None:
    metadata = MetaData()
    _table(metadata, "alpha", Index("idx_business", "business_id"))
    _table(metadata, "beta", Index("idx_business", "business_id"))

    ensure_unique_index_names(metadata)
    before = _names(metadata)

    assert ensure_unique_index_names(metadata) == {"renamed": 0, "dropped": 0}
    assert _names(metadata) == before


def test_the_real_models_have_no_shared_index_names_after_the_bootstrap_fix() -> None:
    from collections import defaultdict

    import app.main  # noqa: F401  -- load every router and model, like the web process
    from app.core.database import Base
    from app.db.schema_bootstrap import _import_all_models

    _import_all_models()
    ensure_unique_index_names(Base.metadata)

    owners: dict[str, list[str]] = defaultdict(list)
    for table in Base.metadata.tables.values():
        for index in table.indexes:
            owners[index.name].append(table.name)
    shared = {name: tables for name, tables in owners.items() if len(tables) > 1}
    assert not shared, shared


async def test_two_tables_with_the_same_index_name_can_both_be_created(db_session) -> None:
    """The failure itself, against PostgreSQL: without the fix the second table is not created."""
    suffix = uuid.uuid4().hex[:6]
    engine = db_session.bind

    async def create_both(metadata: MetaData) -> list[str]:
        created = []
        for table in metadata.tables.values():
            # DuplicateTable (the unfixed bug) is the expected failure: the table is just not created
            with contextlib.suppress(Exception):
                async with engine.begin() as conn:
                    await conn.run_sync(lambda sync_conn, t=table: t.create(bind=sync_conn))
                created.append(table.name)
        return created

    def build() -> MetaData:
        metadata = MetaData()
        _table(metadata, f"idxtest_a_{suffix}", Index(f"idx_shared_{suffix}", "business_id"))
        _table(metadata, f"idxtest_b_{suffix}", Index(f"idx_shared_{suffix}", "business_id"))
        return metadata

    try:
        unfixed = await create_both(build())
        assert len(unfixed) == 1  # the second one is lost: that was the bug

        async with engine.begin() as conn:
            await conn.execute(text(f"DROP TABLE IF EXISTS idxtest_a_{suffix}, idxtest_b_{suffix}"))

        fixed_metadata = build()
        ensure_unique_index_names(fixed_metadata)
        assert len(await create_both(fixed_metadata)) == 2
    finally:
        async with engine.begin() as conn:
            await conn.execute(text(f"DROP TABLE IF EXISTS idxtest_a_{suffix}, idxtest_b_{suffix}"))


@pytest.mark.parametrize("table", ["awards", "location_inventory", "payment_metrics", "sales_rep_performance"])
async def test_the_tables_that_used_to_be_skipped_are_created_by_the_bootstrap(db_session, table: str) -> None:
    """The test database is built with ensure_all_tables (see conftest): these used to be missing."""
    exists = (await db_session.execute(text("SELECT to_regclass(:name)"), {"name": table})).scalar_one()
    assert exists is not None
