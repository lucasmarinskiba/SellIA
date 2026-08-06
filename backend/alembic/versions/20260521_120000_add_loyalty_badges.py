"""add_customer_loyalty_badges

Revision ID: 20260521_120000
Revises: social_sellers_20250521
Create Date: 2026-05-21 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260521_120000'
down_revision: Union[str, None] = 'social_sellers_20250521'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass

def downgrade() -> None:
    pass
