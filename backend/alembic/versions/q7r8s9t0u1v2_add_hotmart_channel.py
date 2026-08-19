"""add_hotmart_channel_platform

Revision ID: q7r8s9t0u1v2
Revises: p6q7r8s9t0u1
Create Date: 2026-08-19 15:00:00.000000+00:00

Adds 'hotmart' as a new value to the channelplatform Postgres enum used by
channel_connections.platform. ALTER TYPE ... ADD VALUE cannot run inside a
transaction block in Postgres, so autocommit is required for this step.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'q7r8s9t0u1v2'
down_revision: Union[str, None] = 'p6q7r8s9t0u1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE channelplatform ADD VALUE IF NOT EXISTS 'hotmart'")


def downgrade() -> None:
    # Postgres does not support removing a value from an enum type.
    # No-op: the 'hotmart' value remains but is simply unused after downgrade.
    pass
