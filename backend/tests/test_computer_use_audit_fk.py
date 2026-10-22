"""computer_use_audit_logs must be creatable on PostgreSQL.

The table was never created in production: its foreign keys were VARCHAR(36) columns pointing at UUID keys,
which PostgreSQL rejects ("incompatible types"), so the bootstrap skipped the table every boot. This checks
the compiled DDL and the column types directly, without a database.
"""

from sqlalchemy import ForeignKeyConstraint
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.schema import CreateTable

from app.domains.computer_use import (
    models as _sessions,  # noqa: F401  (registers computer_use_sessions)
)
from app.domains.computer_use.models_audit_log import ComputerUseAuditLog
from app.domains.users import models as _users  # noqa: F401  (registers users)


def test_every_foreign_key_matches_the_type_of_the_key_it_points_at() -> None:
    table = ComputerUseAuditLog.__table__
    foreign_keys = [c for c in table.constraints if isinstance(c, ForeignKeyConstraint)]
    assert foreign_keys, "the table lost its foreign keys"
    for fk in foreign_keys:
        for local, remote in zip(fk.columns, fk.elements, strict=True):
            target = remote.column
            assert isinstance(local.type, UUID) and isinstance(target.type, UUID), (
                f"{table.name}.{local.name} ({local.type}) -> {target.table.name}.{target.name} ({target.type}): "
                "PostgreSQL refuses a foreign key between different types"
            )


def test_the_audit_table_compiles_to_postgres_ddl() -> None:
    ddl = str(CreateTable(ComputerUseAuditLog.__table__).compile(dialect=postgresql.dialect()))

    assert "user_id UUID" in ddl and "session_id UUID" in ddl and "approved_by_user_id UUID" in ddl
