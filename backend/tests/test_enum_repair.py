"""nps_alerts.status pointed at the wrong Postgres enum type.

``app.domains.alerts.models`` and ``app.domains.feedback.feedback_alert_models`` both define an
``AlertStatus``; an enum type is named after the Python class by default, so both used the type
``alertstatus``. Whichever table was created first fixed its labels (UNREAD/READ/DISMISSED), and every
INSERT into ``nps_alerts`` failed with ``invalid input value for enum alertstatus: "ACTIVE"``.

The model now declares its own type (``nps_alert_status``); ``repair_enum_columns`` fixes databases that
already have the table with the old one. Needs PostgreSQL (the ``db_session`` fixture).
"""

from sqlalchemy import text
from sqlalchemy.dialects import postgresql

from app.db import schema_bootstrap
from app.db.schema_bootstrap import repair_enum_columns
from app.domains.feedback.feedback_alert_models import NPSAlert

KEY = "nps_alerts.status"


async def _udt(engine) -> str:
    async with engine.connect() as conn:
        return (await conn.execute(text(
            "SELECT udt_name FROM information_schema.columns WHERE table_name = 'nps_alerts' AND column_name = 'status'"
        ))).scalar_one()


async def _break(engine) -> None:
    """Recreate what the old model produced: the column on the other model's type."""
    async with engine.begin() as conn:
        await conn.execute(text(
            "ALTER TABLE nps_alerts ALTER COLUMN status TYPE alertstatus USING status::text::alertstatus"
        ))


def test_the_alter_statement_is_compiled_and_quoted_by_the_dialect() -> None:
    """No Postgres needed: the DDL is a structured element, so identifiers go through the dialect's quoting."""
    plain = schema_bootstrap.AlterColumnEnumType("nps_alerts", "status", "nps_alert_status")
    odd = schema_bootstrap.AlterColumnEnumType("Weird Table", 'we"ird', "Mixed Case")
    dialect = postgresql.dialect()

    assert str(plain.compile(dialect=dialect)) == (
        "ALTER TABLE nps_alerts ALTER COLUMN status TYPE nps_alert_status "
        "USING status::text::nps_alert_status"
    )
    assert str(odd.compile(dialect=dialect)) == (
        'ALTER TABLE "Weird Table" ALTER COLUMN "we""ird" TYPE "Mixed Case" '
        'USING "we""ird"::text::"Mixed Case"'
    )


def test_model_has_its_own_enum_type() -> None:
    assert NPSAlert.__table__.c.status.type.name == "nps_alert_status"


async def test_a_fresh_database_gets_the_right_type(db_session) -> None:
    """The test database is built by ensure_all_tables: no repair needed, and the labels are ours."""
    engine = db_session.bind

    assert await _udt(engine) == "nps_alert_status"
    assert await repair_enum_columns(engine) == {KEY: "ok"}
    async with engine.connect() as conn:
        assert (await conn.execute(text("SELECT 'ACTIVE'::nps_alert_status::text"))).scalar_one() == "ACTIVE"


async def test_an_empty_table_on_the_wrong_type_is_repaired(db_session) -> None:
    engine = db_session.bind
    await _break(engine)
    assert await _udt(engine) == "alertstatus"

    assert await repair_enum_columns(engine) == {KEY: "repaired"}

    assert await _udt(engine) == "nps_alert_status"
    async with engine.connect() as conn:
        labels = (await conn.execute(text(
            "SELECT array_agg(e.enumlabel ORDER BY e.enumsortorder) FROM pg_enum e "
            "JOIN pg_type t ON t.oid = e.enumtypid WHERE t.typname = 'alertstatus'"
        ))).scalar_one()
    assert labels == ["UNREAD", "READ", "DISMISSED"]  # the other model's type is left alone
    assert await repair_enum_columns(engine) == {KEY: "ok"}  # idempotent


async def test_a_table_with_rows_is_never_touched(db_session, monkeypatch) -> None:
    engine = db_session.bind
    await _break(engine)
    monkeypatch.setattr(schema_bootstrap, "_table_has_rows", lambda sync_conn, table: True)
    try:
        assert await repair_enum_columns(engine) == {KEY: "skipped-not-empty"}
        assert await _udt(engine) == "alertstatus"
    finally:
        monkeypatch.undo()
        await repair_enum_columns(engine)  # leave the shared test database healthy
    assert await _udt(engine) == "nps_alert_status"


async def test_ensure_all_tables_runs_the_repair_on_the_early_return_path(db_session, monkeypatch) -> None:
    """The steady state returns early ("already present"); the repair has to run before that.

    The early return is forced instead of relying on the database's state: whether any table is pending
    depends on what the shared test database happens to contain.
    """
    from app.core.database import Base

    engine = db_session.bind
    await _break(engine)

    async def everything_exists(_engine) -> set[str]:
        return set(Base.metadata.tables)

    monkeypatch.setattr(schema_bootstrap, "existing_table_names", everything_exists)

    result = await schema_bootstrap.ensure_all_tables(engine)

    assert result == {"tables": len(Base.metadata.tables), "created": 0, "skipped": 0}  # it did return early
    assert await _udt(engine) == "nps_alert_status"
