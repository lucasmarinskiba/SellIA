"""Add reflection and causal reasoning tables

Revision ID: e5f6g7h8i9j0
Revises: 0ecfa96b7780
Create Date: 2026-05-23 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = 'e5f6g7h8i9j0'
down_revision: Union[str, None] = '0ecfa96b7780'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    if bind is None:
        return False
    inspector = inspect(bind)
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
