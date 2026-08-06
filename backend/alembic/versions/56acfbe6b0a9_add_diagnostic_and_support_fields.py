"""add_diagnostic_and_support_fields

Revision ID: 56acfbe6b0a9
Revises: 5a8ff9a13ae4
Create Date: 2026-05-19 22:45:19.546361+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '56acfbe6b0a9'
down_revision: Union[str, None] = '5a8ff9a13ae4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
