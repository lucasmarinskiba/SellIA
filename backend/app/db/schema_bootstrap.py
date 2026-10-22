"""Create every table the ORM declares, one at a time.

Why this exists: migrations are disabled on this deployment (see entrypoint.sh),
and init_db() explicitly skipped the CoreBase domain tables, leaving them to
Alembic. The result is that most domain tables were never created at all --
orders, subscriptions, appointments, user_api_keys, catalog_items,
platform_reviews and more. Each of those failures is swallowed by its caller and
reported as ordinary emptiness ("$0 facturado", "todavía no hay reseñas", "no
hay API key configurada"), so the gap survived for a long time and was only ever
patched one ad-hoc bootstrap at a time, per feature that happened to notice.

Two rules make this safe, and they are the same two the old comment in init_db()
identified before deciding to skip the work anyway:

1. Import each model module independently. A single failing import (a duplicate
   table name, a broken relationship) must not stop the remaining ones from
   registering, which is exactly what a single try block around eight imports
   was doing.
2. Create each table in its OWN transaction. Postgres aborts the whole
   transaction on the first failing statement, so one bad table inside a single
   create_all() silently rolls back every table that call had already created.

create(checkfirst=True) only ever CREATEs what is missing; it never alters or
drops an existing table.
"""

from __future__ import annotations

import hashlib
import importlib
import pathlib
from typing import TYPE_CHECKING

from sqlalchemy import exists, select
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.schema import DDLElement

from app.core.logger import get_logger

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

logger = get_logger(__name__)

#: Model modules that do not live at app/domains/<name>/models.py.
EXTRA_MODEL_MODULES = [
    "app.models.authority_building",
    "app.domains.businesses.location_models",
    "app.domains.businesses.mobile_device_models",
    # Read/written by the mounted unified_dashboard endpoints (aggregate_location_day
    # queries staff_tasks and pricing_transactions). Nothing imports the last two at
    # boot, so without listing them here those tables are never created in production.
    "app.domains.analytics.unified_dashboard_models",
    "app.domains.staff.task_models",
    "app.domains.pricing.pricing_models",
    "app.domains.feedback.feedback_alert_models",
    "app.domains.businesses.team_models",
    "app.domains.agents.llm_usage_models",
    "app.domains.integrations.integration_models",
    "app.core.semantic_cache",  # lives outside app/domains, so the scan never found it
    # seo_config keeps its tables in several modules; the scan only finds models.py, so these
    # were never created and the scheduled seo_config tasks failed on every run (UndefinedTable).
    # (sync_models.py redeclares platform_sync_logs from models.py and cannot be imported.)
    "app.domains.seo_config.fomo_models",
    "app.domains.seo_config.analytics_models",
    "app.domains.seo_config.positioning_models",
]


def _import_all_models() -> int:
    """Register every declarative model with its metadata, resiliently."""
    imported = 0
    failed: list[str] = []

    import app.domains as domains_pkg

    # Filesystem scan rather than pkgutil.iter_modules: a domain directory
    # without __init__.py is a namespace package that iter_modules does not
    # report, and 23 of them are exactly that -- including services/, whose
    # `appointments` table is one of the ones missing in production.
    candidates: list[str] = []
    for root in domains_pkg.__path__:
        for models_file in sorted(pathlib.Path(root).glob("*/models.py")):
            candidates.append(f"app.domains.{models_file.parent.name}.models")
    candidates.extend(EXTRA_MODEL_MODULES)

    for dotted in candidates:
        try:
            importlib.import_module(dotted)
            imported += 1
        except ModuleNotFoundError:
            continue  # a domain without a models.py is normal
        except Exception as e:  # noqa: BLE001
            failed.append(f"{dotted}: {str(e)[:120]}")

    if failed:
        logger.warning(
            "schema bootstrap: %s model module(s) could not be imported: %s",
            len(failed), "; ".join(failed[:5]),
        )
    logger.info("schema bootstrap: %s model modules registered", imported)
    return imported


#: (table, column) pairs whose Postgres enum type was shared with an unrelated model of the same Python
#: class name, so the column points at the wrong labels. Only these are ever touched.
ENUM_REPAIRS: list[tuple[str, str]] = [("nps_alerts", "status")]


class AlterColumnEnumType(DDLElement):
    """``ALTER TABLE t ALTER COLUMN c TYPE <enum> USING c::text::<enum>``.

    A structured DDL element (identifiers are quoted by the dialect's compiler) rather than an
    interpolated ``text()`` string, so no SQL is assembled by hand.
    """

    inherit_cache = False

    def __init__(self, table_name: str, column_name: str, type_name: str) -> None:
        self.table_name = table_name
        self.column_name = column_name
        self.type_name = type_name


@compiles(AlterColumnEnumType)
def _compile_alter_column_enum_type(element: AlterColumnEnumType, compiler, **kw) -> str:
    quote = compiler.preparer.quote
    column, type_name = quote(element.column_name), quote(element.type_name)
    return f"ALTER TABLE {quote(element.table_name)} ALTER COLUMN {column} TYPE {type_name} USING {column}::text::{type_name}"


def _table_has_rows(sync_conn, table) -> bool:
    return bool(sync_conn.execute(select(exists().select_from(table))).scalar())


async def repair_enum_columns(engine: AsyncEngine) -> dict[str, str]:
    """Point the columns in ``ENUM_REPAIRS`` at the enum type the model now declares.

    ``Table.create(checkfirst=True)`` never alters a table that exists, so changing a model's enum type
    name does nothing for a database that already has the table with the old, wrong type (here:
    ``nps_alerts.status`` created against ``alertstatus`` with someone else's labels, which makes every
    INSERT fail). This is the one place the bootstrap alters anything, so it is deliberately narrow:

    * only the listed columns;
    * only when the column's current type differs from the declared one;
    * only when the table is EMPTY -- with rows there is nothing safe to convert, so it logs and leaves it;
    * PostgreSQL only; one transaction per column; never raises.

    Returns ``{"table.column": "ok" | "repaired" | "skipped-not-empty" | "absent" | "not-declared" | "failed"}``.
    """
    outcome: dict[str, str] = {}
    if engine.dialect.name != "postgresql":
        return outcome

    from sqlalchemy import Enum as SAEnum
    from sqlalchemy import text
    from sqlalchemy.dialects.postgresql import ENUM as PGEnum

    from app.core.database import Base as CoreBase

    for table_name, column_name in ENUM_REPAIRS:
        key = f"{table_name}.{column_name}"
        table = CoreBase.metadata.tables.get(table_name)
        column = table.c.get(column_name) if table is not None else None
        if column is None or not isinstance(column.type, SAEnum) or not column.type.name:
            outcome[key] = "not-declared"
            continue
        wanted = column.type
        try:
            async with engine.begin() as conn:
                current = (await conn.execute(
                    text(
                        "SELECT udt_name FROM information_schema.columns WHERE table_schema = current_schema() "
                        "AND table_name = :t AND column_name = :c"
                    ),
                    {"t": table_name, "c": column_name},
                )).scalar_one_or_none()
                if current is None:
                    outcome[key] = "absent"
                elif current == wanted.name:
                    outcome[key] = "ok"
                elif await conn.run_sync(_table_has_rows, table):
                    outcome[key] = "skipped-not-empty"
                    logger.warning(
                        "schema bootstrap: %s uses enum type %r but the model declares %r and the table has rows; "
                        "left as is (needs a manual migration)", key, current, wanted.name,
                    )
                else:
                    def _alter(sync_conn, table_name=table_name, column_name=column_name, wanted=wanted) -> None:
                        PGEnum(*wanted.enums, name=wanted.name).create(sync_conn, checkfirst=True)
                        sync_conn.execute(AlterColumnEnumType(table_name, column_name, wanted.name))

                    await conn.run_sync(_alter)
                    outcome[key] = "repaired"
                    logger.warning("schema bootstrap: repaired %s (was enum type %r, now %r)", key, current, wanted.name)
        except Exception as e:  # noqa: BLE001 -- a failed repair must not stop the boot
            outcome[key] = "failed"
            logger.warning("schema bootstrap: could not repair %s: %s", key, str(e)[:160])
    return outcome


async def existing_table_names(engine: AsyncEngine) -> set[str] | None:
    """Names of the tables in the current schema, from ONE catalog query.

    Callers use it to skip ``Table.create(checkfirst=True)`` for tables that are
    already there: checkfirst costs several round trips per table on every boot
    (``metadata.create_all(tables=[t], checkfirst=True)`` measured ~85), which
    on a remote database is the difference between seconds and minutes.

    Returns None -- not an empty set -- when the listing is unavailable (not
    Postgres, or the query failed), so callers can tell "nothing exists" from
    "don't know" and fall back to their own per-table check.
    """
    try:
        from sqlalchemy import text

        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = current_schema()"
            ))
            return {row[0] for row in result}
    except Exception as e:  # noqa: BLE001
        logger.warning("schema bootstrap: could not list existing tables: %s", str(e)[:160])
        return None


def ensure_unique_index_names(metadata) -> dict[str, int]:
    """Make every index name unique in ``metadata``, because PostgreSQL index names are per schema.

    Models declare indexes by hand with generic names ("idx_business_metrics", "idx_rep_id", ...)
    and several tables reuse the same one. ``CREATE INDEX`` of the second table then fails with
    ``DuplicateTable`` and the whole table is silently skipped on every boot. Two things are fixed
    in memory, before any DDL:

    * a name shared by different tables gets the table name appended, in every table that uses it
      (tables that already exist keep the index they have; only new tables are created with the new
      names, which cannot clash with the old generic ones);
    * a name declared twice on the same table (``index=True`` plus an explicit ``Index`` on the same
      column) keeps one copy.

    Returns ``{"renamed": n, "dropped": n}``.
    """
    from collections import defaultdict

    owners: dict[str, list] = defaultdict(list)
    for table in metadata.tables.values():
        for index in list(table.indexes):
            if index.name:
                owners[index.name].append((table, index))

    renamed = dropped = 0
    for name, members in owners.items():
        if len(members) < 2:
            continue
        tables = {table.name for table, _ in members}
        if len(tables) == 1:
            table = members[0][0]
            seen: set[tuple[str, ...]] = set()
            for _, index in members:
                key = tuple(column.name for column in index.columns)
                if key in seen:
                    table.indexes.discard(index)
                    dropped += 1
                else:
                    seen.add(key)
            continue
        for table, index in members:
            new_name = f"{name}_{table.name}"
            if len(new_name) > 63:  # PostgreSQL identifier limit; keep it deterministic and unique
                digest = hashlib.sha256(new_name.encode()).hexdigest()[:8]
                new_name = f"{new_name[:54]}_{digest}"
            index.name = new_name
            renamed += 1
    return {"renamed": renamed, "dropped": dropped}


async def ensure_vector_extension(engine: AsyncEngine) -> str:
    """Install the pgvector extension when the server ships it and it is not installed yet.

    ``customer_memories``, ``conversation_memory_chunks``, ``document_chunks`` and
    ``semantic_cache_embeddings`` have ``vector(768)`` columns, so they could never be created
    (``type "vector" does not exist``) and were retried and skipped on every boot. Returns
    ``"installed"``, ``"already"``, ``"unavailable"`` (not Postgres, or the server does not ship
    pgvector) or ``"failed"``; never raises: tables that do not need it must still be created.
    """
    try:
        from sqlalchemy import text

        async with engine.connect() as conn:
            if conn.dialect.name != "postgresql":
                return "unavailable"
            installed = (await conn.execute(text("SELECT 1 FROM pg_extension WHERE extname = 'vector'"))).first()
            if installed:
                return "already"
            available = (await conn.execute(text("SELECT 1 FROM pg_available_extensions WHERE name = 'vector'"))).first()
            if not available:
                logger.info("schema bootstrap: pgvector is not available on this server; vector tables stay skipped")
                return "unavailable"
        async with engine.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        logger.info("✅ schema bootstrap: pgvector extension installed")
        return "installed"
    except Exception as e:  # noqa: BLE001 -- e.g. the role may not be allowed to create extensions
        logger.warning("schema bootstrap: could not install pgvector: %s", str(e)[:160])
        return "failed"


async def ensure_all_tables(engine: AsyncEngine | None = None) -> dict[str, int]:
    """Create anything the ORM declares and the database does not have yet.

    ``engine`` defaults to the application's engine; the test suite passes its
    own so it can reuse this resilient, per-table creation against the test DB.
    """
    from app.core.database import Base as CoreBase

    if engine is None:
        from app.core.database import engine as app_engine

        engine = app_engine

    _import_all_models()
    fixed = ensure_unique_index_names(CoreBase.metadata)
    if fixed["renamed"] or fixed["dropped"]:
        logger.info("schema bootstrap: made index names unique (%s renamed, %s duplicates dropped)", fixed["renamed"], fixed["dropped"])

    # Before the early return below: the steady state (every table present) is exactly where a table
    # that exists with a wrong enum type lives.
    await repair_enum_columns(engine)

    # NOT metadata.sorted_tables: that resolves the whole foreign-key graph up
    # front and raises if any FK points at a table no model declares (there is
    # at least one such dangling reference here), which would take down the
    # entire bootstrap over one bad relationship.
    tables = list(CoreBase.metadata.tables.values())

    # Ask once which tables already exist, instead of paying a round trip per
    # table to rediscover it. In the steady state (everything created) this
    # turns ~450 transactions per boot into a single query, which matters
    # because it runs on every start.
    # (None -> could not list: fall back to per-table checkfirst below.)
    existing: set[str] = await existing_table_names(engine) or set()

    pending = [t for t in tables if t.name not in existing]
    if not pending:
        logger.info("✅ schema bootstrap: %s domain tables already present", len(tables))
        return {"tables": len(tables), "created": 0, "skipped": 0}

    # Tables with vector columns need the extension first.
    await ensure_vector_extension(engine)

    created = 0
    errors: dict[str, str] = {}

    # Several passes, because creating one table at a time means a table whose
    # foreign key targets another can fail simply for going first. Each pass
    # creates whatever became possible in the previous one; when a pass creates
    # nothing new, the remainder is genuinely broken rather than out of order.
    for _ in range(3):
        failed = []
        for table in pending:
            try:
                async with engine.begin() as conn:
                    await conn.run_sync(
                        lambda sync_conn, t=table: t.create(bind=sync_conn, checkfirst=True)
                    )
                created += 1
                errors.pop(table.name, None)
            except Exception as e:  # noqa: BLE001 -- one bad table must not stop the rest
                errors[table.name] = str(e)[:100]
                failed.append(table)
        if len(failed) == len(pending):
            break
        pending = failed
        if not pending:
            break

    if errors:
        logger.warning(
            "schema bootstrap: %s table(s) skipped: %s",
            len(errors), "; ".join(f"{k}: {v}" for k, v in list(errors.items())[:8]),
        )
    logger.info("✅ schema bootstrap: %s/%s domain tables ensured", created, len(tables))
    return {"tables": len(tables), "created": created, "skipped": len(errors)}
