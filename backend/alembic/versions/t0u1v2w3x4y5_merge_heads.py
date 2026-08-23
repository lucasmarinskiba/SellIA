"""Merge multiple migration heads into single baseline.

Revision ID: t0u1v2w3x4y5
Revises: 0034_phase_26c_forecasting, 003_add_products_tables, 20260819_phase5b
Create Date: 2026-08-23 17:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 't0u1v2w3x4y5'
down_revision: Union[str, Sequence[str], None] = ('0034_phase_26c_forecasting', '003_add_products_tables', '20260819_phase5b')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge heads - no operations needed."""
    pass


def downgrade() -> None:
    """Downgrade - no operations needed."""
    pass
