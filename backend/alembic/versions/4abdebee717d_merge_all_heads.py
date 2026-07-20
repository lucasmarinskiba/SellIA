"""merge all heads

Revision ID: 4abdebee717d
Revises: c1d2e3f4g5h6, d4e5f6g7h8i9, e5f6g7h8i9j0, i0j1k2l3m4n5
Create Date: 2026-05-26 16:29:36.384590+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4abdebee717d'
down_revision: Union[str, None] = ('c1d2e3f4g5h6', 'd4e5f6g7h8i9', 'e5f6g7h8i9j0', 'i0j1k2l3m4n5')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
