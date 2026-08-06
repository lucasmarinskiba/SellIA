"""multimedia_agents

Revision ID: i0j1k2l3m4n5
Revises: f6g7h8i9j0k1, c1d2e3f4g5h6, d4e5f6g7h8i9, e5f6g7h8i9j0
Create Date: 2026-05-26 11:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect
from sqlalchemy.exc import NoInspectionAvailable

# revision identifiers, used by Alembic.
revision: str = 'i0j1k2l3m4n5'
down_revision: Union[str, None] = 'h9i0j1k2l3m4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(table_name: str) -> bool:
    bind = op.get_bind()
    try:
        inspector = inspect(bind)
        return inspector.has_table(table_name)
    except NoInspectionAvailable:
        return False


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
