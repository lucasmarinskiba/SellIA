"""create_battlecards

Revision ID: 93e5f6a7b8c9
Revises: 16a3957a8fbe
Create Date: 2026-05-20 19:45:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision: str = '93e5f6a7b8c9'
down_revision: Union[str, None] = '16a3957a8fbe'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
