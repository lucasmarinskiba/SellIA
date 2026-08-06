"""conversation outcomes

Revision ID: 97i0d1e2f3a4
Revises: 94f7a8b9c0d1
Create Date: 2026-05-20 20:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '97i0d1e2f3a4'
down_revision: Union[str, None] = '94f7a8b9c0d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
