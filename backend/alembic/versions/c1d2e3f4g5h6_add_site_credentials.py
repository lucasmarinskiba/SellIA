"""Add site_credentials table

Revision ID: c1d2e3f4g5h6
Revises: b2c3d4e5f6g7
Create Date: 2026-05-22 14:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c1d2e3f4g5h6'
down_revision: Union[str, None] = 'b2c3d4e5f6g7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'site_credentials',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('businesses.id', ondelete='CASCADE'), nullable=True, index=True),
        sa.Column('domain', sa.String(200), nullable=False, index=True),
        sa.Column('platform_name', sa.String(100), nullable=False),
        sa.Column('auth_type', sa.Enum('password', 'api_key', 'oauth', '2fa', name='auth_type'), nullable=False, server_default='password'),
        sa.Column('encrypted_username', sa.Text(), nullable=True),
        sa.Column('encrypted_password', sa.Text(), nullable=True),
        sa.Column('encrypted_api_key', sa.Text(), nullable=True),
        sa.Column('encrypted_api_secret', sa.Text(), nullable=True),
        sa.Column('encrypted_oauth_token', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_successful_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failed_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
    )
    op.create_index('ix_site_credentials_user_domain', 'site_credentials', ['user_id', 'domain'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_site_credentials_user_domain', table_name='site_credentials')
    op.drop_table('site_credentials')
    op.execute("DROP TYPE auth_type")
