"""baseline_users_businesses

Revision ID: l2m3n4o5p6q7
Revises: db3251228ebb
Create Date: 2026-08-05 19:20:00.000000+00:00

The 43 migrations that follow the (empty) initial_migration all assume
`users` and `businesses` already exist — neither table was ever actually
captured by an Alembic migration (likely created once via
Base.metadata.create_all() in an early dev environment and never backfilled
into the migration history). This baseline fills that gap so a fresh
database can build the full schema from scratch. Generated via
alembic.autogenerate.produce_migrations against the real ORM models,
scoped to just these two tables.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import Text
import app.core.encrypted_types


# revision identifiers, used by Alembic.
revision: str = 'l2m3n4o5p6q7'
down_revision: Union[str, None] = 'db3251228ebb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('users',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('hashed_password', sa.String(length=255), nullable=False),
    sa.Column('full_name', sa.String(length=255), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('email_verified', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.Column('failed_login_attempts', sa.Integer(), nullable=False),
    sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_failed_login', sa.DateTime(timezone=True), nullable=True),
    sa.Column('totp_secret', app.core.encrypted_types.EncryptedString(), nullable=True),
    sa.Column('is_2fa_enabled', sa.Boolean(), nullable=False),
    sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('last_device_fingerprint', sa.String(length=64), nullable=True),
    sa.Column('country_code', sa.String(length=2), nullable=False),
    sa.Column('detected_country', sa.String(length=2), nullable=True),
    sa.Column('preferred_currency', sa.String(length=3), nullable=False),
    sa.Column('timezone', sa.String(length=50), nullable=False),
    sa.Column('tax_id', app.core.encrypted_types.EncryptedString(), nullable=True),
    sa.Column('billing_address', app.core.encrypted_types.EncryptedJSONB(), nullable=False),
    sa.Column('payment_methods', app.core.encrypted_types.EncryptedJSONB(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('businesses',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('type', sa.Enum('SERVICES', 'GOODS', 'DIGITAL', 'MIXED', name='businesstype'), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('config', postgresql.JSONB(astext_type=Text()), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_businesses_user_id'), 'businesses', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_businesses_user_id'), table_name='businesses')
    op.drop_table('businesses')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
