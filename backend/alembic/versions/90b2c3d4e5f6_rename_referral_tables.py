"""rename_referral_tables

Revision ID: 90b2c3d4e5f6
Revises: 89a1b2c3d4e5
Create Date: 2026-05-21 12:20:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '90b2c3d4e5f6'
down_revision: Union[str, None] = '89a1b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
