"""Create users table

Revision ID: 20260823_create_users_table
Revises: db3251228ebb
Create Date: 2026-08-23 17:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '20260823_create_users_table'
down_revision: Union[str, None] = 'db3251228ebb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('email_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_failed_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('totp_secret', sa.String(), nullable=True),
        sa.Column('is_2fa_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_device_fingerprint', sa.String(64), nullable=True),
        sa.Column('country_code', sa.String(2), nullable=False, server_default='AR'),
        sa.Column('detected_country', sa.String(2), nullable=True),
        sa.Column('preferred_currency', sa.String(3), nullable=False, server_default='ARS'),
        sa.Column('timezone', sa.String(50), nullable=False, server_default='America/Argentina/Buenos_Aires'),
        sa.Column('tax_id', sa.String(), nullable=True),
        sa.Column('billing_address', postgresql.JSONB(), nullable=False, server_default='{}'),
        sa.Column('payment_methods', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
