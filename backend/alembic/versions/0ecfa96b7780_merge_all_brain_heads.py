"""merge_all_brain_heads

Revision ID: 0ecfa96b7780
Revises: 98j1e2f3a4b5, 99k2f3a4b5c6, 9a03g4b5c6d7, 9b14h5c6d7e8, b2c3d4e5f6g7
Create Date: 2026-05-23 00:52:32.694172+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0ecfa96b7780'
down_revision: Union[str, None] = ('98j1e2f3a4b5', '99k2f3a4b5c6', '9a03g4b5c6d7', '9b14h5c6d7e8', 'b2c3d4e5f6g7')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
