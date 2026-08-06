"""create_swarm_tables

Revision ID: 98j1e2f3a4b5
Revises: 0e797dd2bbe
Create Date: 2026-05-20 19:45:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable

# revision identifiers, used by Alembic.
revision: str = '98j1e2f3a4b5'
down_revision: Union[str, None] = '0e797dd2bbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    try:
        inspector = inspect(bind)
        return inspector.has_table(table_name)
    except NoInspectionAvailable:
        # Offline mode (alembic --sql): assume table does not exist
        return False


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
