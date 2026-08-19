"""add_woocommerce_etsy_facebook_marketplace_channels

Revision ID: r8s9t0u1v2w3
Revises: q7r8s9t0u1v2
Create Date: 2026-08-19 15:30:00.000000+00:00

Adds 'woocommerce', 'etsy' and 'facebook_marketplace' to the channelplatform
Postgres enum used by channel_connections.platform.
"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'r8s9t0u1v2w3'
down_revision: Union[str, None] = 'q7r8s9t0u1v2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE channelplatform ADD VALUE IF NOT EXISTS 'woocommerce'")
        op.execute("ALTER TYPE channelplatform ADD VALUE IF NOT EXISTS 'etsy'")
        op.execute("ALTER TYPE channelplatform ADD VALUE IF NOT EXISTS 'facebook_marketplace'")


def downgrade() -> None:
    # Postgres does not support removing a value from an enum type.
    pass
