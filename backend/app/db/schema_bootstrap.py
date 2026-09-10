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

import importlib
import pathlib

from app.core.logger import get_logger

logger = get_logger(__name__)

#: Model modules that do not live at app/domains/<name>/models.py.
EXTRA_MODEL_MODULES = [
    "app.models.authority_building",
    "app.domains.businesses.location_models",
    "app.domains.agents.llm_usage_models",
    "app.domains.integrations.integration_models",
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


async def ensure_all_tables() -> dict[str, int]:
    """Create anything the ORM declares and the database does not have yet."""
    from app.core.database import Base as CoreBase
    from app.core.database import engine

    _import_all_models()

    # NOT metadata.sorted_tables: that resolves the whole foreign-key graph up
    # front and raises if any FK points at a table no model declares (there is
    # at least one such dangling reference here), which would take down the
    # entire bootstrap over one bad relationship.
    tables = list(CoreBase.metadata.tables.values())

    # Ask once which tables already exist, instead of paying a round trip per
    # table to rediscover it. In the steady state (everything created) this
    # turns ~450 transactions per boot into a single query, which matters
    # because it runs on every start.
    existing: set[str] = set()
    try:
        from sqlalchemy import text

        async with engine.connect() as conn:
            result = await conn.execute(text(
                "SELECT tablename FROM pg_tables WHERE schemaname = current_schema()"
            ))
            existing = {row[0] for row in result}
    except Exception as e:  # noqa: BLE001 -- fall back to per-table checkfirst
        logger.warning("schema bootstrap: could not list existing tables: %s", str(e)[:160])

    pending = [t for t in tables if t.name not in existing]
    if not pending:
        logger.info("✅ schema bootstrap: %s domain tables already present", len(tables))
        return {"tables": len(tables), "created": 0, "skipped": 0}

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
