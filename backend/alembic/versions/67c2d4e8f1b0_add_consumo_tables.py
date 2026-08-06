"""add_consumo_tables

Revision ID: 67c2d4e8f1b0
Revises: 56acfbe6b0a9
Create Date: 2026-05-20 09:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '67c2d4e8f1b0'
down_revision: Union[str, None] = '56acfbe6b0a9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
