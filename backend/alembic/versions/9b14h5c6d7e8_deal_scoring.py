"""deal scoring

Revision ID: 9b14h5c6d7e8
Revises: 97i0d1e2f3a4
Create Date: 2026-05-20 21:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '9b14h5c6d7e8'
down_revision: Union[str, None] = '97i0d1e2f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
