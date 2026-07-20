"""Add email_verified to users

Revision ID: 0e797dd2bbe
Revises: 97i0d1e2f3a4
Create Date: 2026-05-22 04:15:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0e797dd2bbe'
down_revision: Union[str, None] = '97i0d1e2f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    op.drop_column('users', 'email_verified')
