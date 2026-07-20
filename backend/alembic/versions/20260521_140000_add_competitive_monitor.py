"""add competitive monitor

Revision ID: 20260521_140000
Revises: 16a3957a8fbe
Create Date: 2025-05-21 14:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '20260521_140000'
down_revision = '16a3957a8fbe'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('competitive_monitors',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('competitor_name', sa.String(length=200), nullable=False),
        sa.Column('competitor_url', sa.Text(), nullable=False),
        sa.Column('products_to_track', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('last_scraped_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_snapshot', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_competitive_monitors_business_id'), 'competitive_monitors', ['business_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_competitive_monitors_business_id'), table_name='competitive_monitors')
    op.drop_table('competitive_monitors')
