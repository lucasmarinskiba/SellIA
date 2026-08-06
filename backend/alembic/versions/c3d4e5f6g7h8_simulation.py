"""Add simulation tables

Revision ID: c3d4e5f6g7h8
Revises: 9c15d6e7f8g9, 9d16e7f8g0h1
Create Date: 2026-05-20 19:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable

# revision identifiers, used by Alembic.
revision: str = 'c3d4e5f6g7h8'
down_revision: Union[str, None] = ('a1b2c3d4e5f6', '9d16e7f8g0h1')
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
