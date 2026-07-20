"""merge heads

Revision ID: 9b15bf3b57fc
Revises: 95g8b9c0d1e2, 96h9c0d1e2f3
Create Date: 2026-05-21 21:23:53.181237+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b15bf3b57fc'
down_revision: Union[str, None] = ('95g8b9c0d1e2', '96h9c0d1e2f3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
