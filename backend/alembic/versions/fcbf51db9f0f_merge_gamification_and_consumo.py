"""merge_gamification_and_consumo

Revision ID: fcbf51db9f0f
Revises: 02eb019f71fe, 78d9e0a2c3f4
Create Date: 2026-05-20 22:51:33.678131+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fcbf51db9f0f'
down_revision: Union[str, None] = ('02eb019f71fe', '78d9e0a2c3f4')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
