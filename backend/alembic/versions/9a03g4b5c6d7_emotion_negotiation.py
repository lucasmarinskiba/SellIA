"""Add emotion and negotiation tables

Revision ID: 9a03g4b5c6d7
Revises: 0e797dd2bbe, a1b2c3d4e5f6
Create Date: 2026-05-22 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '9a03g4b5c6d7'
down_revision: Union[str, Sequence[str], None] = ('0e797dd2bbe', 'a1b2c3d4e5f6')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
