"""proactive outreach engine

Revision ID: 99k2f3a4b5c6
Revises: 0e797dd2bbe
Create Date: 2026-05-20 20:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '99k2f3a4b5c6'
down_revision: Union[str, None] = '0e797dd2bbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
