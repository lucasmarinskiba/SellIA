"""merge_all_heads

Revision ID: da7167e07273
Revises: 20260521_140000, 92d4e5f6a7b8
Create Date: 2026-05-21 21:16:33.983632+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'da7167e07273'
down_revision: Union[str, None] = ('20260521_140000', '92d4e5f6a7b8')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
