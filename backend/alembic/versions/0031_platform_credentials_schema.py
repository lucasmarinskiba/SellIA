"""Add platform credentials table for OAuth integration.

Revision ID: 0031_platform_credentials
Revises: 0030_analytics_reporting_schema
Create Date: 2026-08-14 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0031_platform_credentials"
down_revision = "0030"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "platform_credentials",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seller_id", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("access_token", sa.Text(), nullable=False),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expiry", sa.DateTime(), nullable=True),
        sa.Column("seller_username", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_sync_at", sa.DateTime(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_seller_platform",
        "platform_credentials",
        ["seller_id", "platform"],
        unique=False,
    )
    op.create_index(
        "idx_active_credentials",
        "platform_credentials",
        ["seller_id", "is_active"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_active_credentials", table_name="platform_credentials")
    op.drop_index("idx_seller_platform", table_name="platform_credentials")
    op.drop_table("platform_credentials")
