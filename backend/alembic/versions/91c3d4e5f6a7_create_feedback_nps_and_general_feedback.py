"""create_feedback_nps_and_general_feedback

Revision ID: 91c3d4e5f6a7
Revises: 90b2c3d4e5f6
Create Date: 2026-05-21 12:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '91c3d4e5f6a7'
down_revision: Union[str, None] = '90b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
