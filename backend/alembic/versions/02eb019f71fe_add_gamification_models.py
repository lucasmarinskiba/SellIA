"""add_gamification_models

Revision ID: 02eb019f71fe
Revises: 69a2f112522c
Create Date: 2026-05-12 16:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '02eb019f71fe'
down_revision: Union[str, None] = '69a2f112522c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
