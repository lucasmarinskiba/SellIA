"""rls policies · multi-tenant isolation

Revision ID: 0002_rls
Revises: 0001_init
Create Date: 2026-05-23 00:01:00
"""
from typing import Sequence, Union

from alembic import op


revision: str = "0002_rls"
down_revision: Union[str, None] = "0001_init"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


TABLES = ["deals", "contacts", "conversations", "messages", "channels", "audit_logs"]


def upgrade() -> None:
    for t in TABLES:
        op.execute(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY tenant_isolation ON {t}
                USING (tenant_id::text = current_setting('app.tenant_id', true));
        """)


def downgrade() -> None:
    for t in TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation ON {t};")
        op.execute(f"ALTER TABLE {t} DISABLE ROW LEVEL SECURITY;")
