"""business documents

Revision ID: 96h9c0d1e2f3
Revises: da7167e07273
Create Date: 2026-05-21 15:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '96h9c0d1e2f3'
down_revision: Union[str, Sequence[str], None] = 'da7167e07273'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
