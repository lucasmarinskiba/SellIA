"""add_unified_customers

Revision ID: 16a3957a8fbe
Revises: fcbf51db9f0f
Create Date: 2026-05-21 12:15:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '16a3957a8fbe'
down_revision: Union[str, None] = '20260521_120000'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'unified_customers',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('display_name', sa.String(length=200), nullable=True),
        sa.Column('master_email', sa.String(length=255), nullable=True),
        sa.Column('master_phone', sa.String(length=50), nullable=True),
        sa.Column('identity_map', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('first_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_lifetime_value', sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column('buying_frequency_days', sa.Integer(), nullable=True),
        sa.Column('preferred_platforms', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('rfm_segment', sa.String(length=30), nullable=True),
        sa.Column('last_purchase_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('total_purchases', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_unified_customers_business_id'), 'unified_customers', ['business_id'], unique=False)
    op.create_index(op.f('ix_unified_customers_master_email'), 'unified_customers', ['master_email'], unique=False)
    op.create_index(op.f('ix_unified_customers_master_phone'), 'unified_customers', ['master_phone'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_unified_customers_master_phone'), table_name='unified_customers')
    op.drop_index(op.f('ix_unified_customers_master_email'), table_name='unified_customers')
    op.drop_index(op.f('ix_unified_customers_business_id'), table_name='unified_customers')
    op.drop_table('unified_customers')
