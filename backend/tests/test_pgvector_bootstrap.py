"""pgvector must be installed by the bootstrap when the server ships it.

Four tables (customer_memories, conversation_memory_chunks, document_chunks,
semantic_cache_embeddings) have ``vector(768)`` columns. Nothing ever ran
``CREATE EXTENSION``, so they failed with ``type "vector" does not exist`` on every boot and
the features that read them (memory, proactive detectors, document search, semantic cache)
failed too. The CI database may or may not ship pgvector, so the DB tests accept either
outcome and check that it is consistent with what the server reports.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import pytest
from sqlalchemy import text

VECTOR_TABLES = {"customer_memories", "conversation_memory_chunks", "document_chunks", "semantic_cache_embeddings"}


async def _server_ships_pgvector(engine) -> bool:
    async with engine.connect() as conn:
        return (await conn.execute(text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'"))).first() is not None


async def _installed(engine) -> bool:
    async with engine.connect() as conn:
        return (await conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))).first() is not None


async def test_outcome_matches_what_the_server_offers_and_is_idempotent(db_session) -> None:
    from app.db.schema_bootstrap import ensure_vector_extension

    engine = db_session.bind
    shipped, was_installed = await _server_ships_pgvector(engine), await _installed(engine)

    first = await ensure_vector_extension(engine)
    second = await ensure_vector_extension(engine)

    if was_installed:
        assert (first, second) == ("already", "already")
    elif shipped:
        assert (first, second) == ("installed", "already")
        async with engine.connect() as conn:  # the type really works
            assert (await conn.execute(text("SELECT '[1,2,3]'::vector(3)::text"))).scalar_one() == "[1,2,3]"
        async with engine.begin() as conn:  # leave the test database as it was found
            await conn.execute(text("DROP EXTENSION IF EXISTS vector"))
    else:
        assert (first, second) == ("unavailable", "unavailable")


async def test_vector_tables_can_be_created_once_the_extension_exists(db_session) -> None:
    from app.core.database import Base
    from app.db.schema_bootstrap import _import_all_models, ensure_vector_extension

    engine = db_session.bind
    if not (await _server_ships_pgvector(engine)):
        pytest.skip("this PostgreSQL does not ship pgvector")
    was_installed = await _installed(engine)

    _import_all_models()
    await ensure_vector_extension(engine)
    table = Base.metadata.tables["conversation_memory_chunks"]
    async with engine.connect() as conn:
        exists_before = (await conn.execute(text("SELECT to_regclass('conversation_memory_chunks')"))).scalar_one() is not None

    try:
        if not exists_before:
            async with engine.begin() as conn:
                await conn.run_sync(lambda sync_conn: table.create(bind=sync_conn, checkfirst=True))
            async with engine.connect() as conn:
                assert (await conn.execute(text("SELECT to_regclass('conversation_memory_chunks')"))).scalar_one() is not None
    finally:
        if not exists_before:
            async with engine.begin() as conn:
                await conn.execute(text("DROP TABLE IF EXISTS conversation_memory_chunks"))
        if not was_installed:
            async with engine.begin() as conn:
                await conn.execute(text("DROP EXTENSION IF EXISTS vector"))


class _Conn:
    def __init__(self, dialect: str, rows: dict[str, bool], fail_create: bool = False) -> None:
        self.dialect = type("D", (), {"name": dialect})()
        self._rows, self._fail_create, self.executed = rows, fail_create, []

    async def execute(self, statement):
        sql = str(statement)
        self.executed.append(sql)
        if "CREATE EXTENSION" in sql and self._fail_create:
            raise PermissionError("permission denied to create extension \"vector\"")
        key = "installed" if "pg_extension" in sql else "available"
        return type("R", (), {"first": lambda _self: (1,) if self._rows.get(key) else None})()


class _Engine:
    def __init__(self, conn: _Conn) -> None:
        self.conn = conn

    @asynccontextmanager
    async def connect(self):
        yield self.conn

    @asynccontextmanager
    async def begin(self):
        yield self.conn


@pytest.mark.parametrize(
    ("dialect", "rows", "fail", "expected", "creates"),
    [
        ("sqlite", {}, False, "unavailable", False),
        ("postgresql", {"installed": True}, False, "already", False),
        ("postgresql", {}, False, "unavailable", False),
        ("postgresql", {"available": True}, False, "installed", True),
        ("postgresql", {"available": True}, True, "failed", True),
    ],
)
async def test_every_branch_is_safe_and_never_raises(dialect, rows, fail, expected, creates) -> None:
    from app.db.schema_bootstrap import ensure_vector_extension

    conn = _Conn(dialect, rows, fail_create=fail)
    assert await ensure_vector_extension(_Engine(conn)) == expected
    assert any("CREATE EXTENSION" in sql for sql in conn.executed) is creates
