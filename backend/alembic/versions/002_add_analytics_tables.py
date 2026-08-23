"""Add analytics tables for Tier 3

Revision ID: 002_add_analytics_tables
Revises: 001_add_websites_and_domains
Create Date: 2026-08-17 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_analytics_tables'
down_revision = '001_websites_domains'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ENUM for event types
    event_type_enum = postgresql.ENUM(
        'PAGE_VIEW', 'CONVERSION', 'FORM_SUBMIT', 'BUTTON_CLICK', 'SCROLL', 'TIME_ON_PAGE',
        name='eventtype',
        create_type=True
    )
    event_type_enum.create(op.get_bind(), checkfirst=True)

    # analytics_events table
    op.create_table(
        'analytics_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('website_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', event_type_enum, nullable=False),
        sa.Column('event_name', sa.String(255), nullable=True),
        sa.Column('page_url', sa.String(2048), nullable=False),
        sa.Column('page_title', sa.String(255), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('browser', sa.String(100), nullable=True),
        sa.Column('scroll_depth', sa.Integer(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['website_id'], ['websites.id'], name=op.f('fk_analytics_events_website_id')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_analytics_events'))
    )

    # Indexes for analytics_events
    op.create_index('ix_analytics_events_website_id_created_at', 'analytics_events',
                    ['website_id', 'created_at'], postgresql_using='btree')
    op.create_index('ix_analytics_events_event_type_created_at', 'analytics_events',
                    ['event_type', 'created_at'], postgresql_using='btree')
    op.create_index('ix_analytics_events_session_id', 'analytics_events',
                    ['session_id'], postgresql_using='btree')

    # conversions table
    op.create_table(
        'conversions',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('website_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversion_type', sa.String(255), nullable=False),
        sa.Column('conversion_value', sa.Numeric(10, 2), nullable=True),
        sa.Column('session_id', sa.String(255), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_page', sa.String(2048), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['website_id'], ['websites.id'], name=op.f('fk_conversions_website_id')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_conversions'))
    )

    # Indexes for conversions
    op.create_index('ix_conversions_website_id_created_at', 'conversions',
                    ['website_id', 'created_at'], postgresql_using='btree')
    op.create_index('ix_conversions_conversion_type', 'conversions',
                    ['conversion_type'], postgresql_using='btree')


def downgrade() -> None:
    op.drop_index('ix_conversions_conversion_type', table_name='conversions')
    op.drop_index('ix_conversions_website_id_created_at', table_name='conversions')
    op.drop_table('conversions')

    op.drop_index('ix_analytics_events_session_id', table_name='analytics_events')
    op.drop_index('ix_analytics_events_event_type_created_at', table_name='analytics_events')
    op.drop_index('ix_analytics_events_website_id_created_at', table_name='analytics_events')
    op.drop_table('analytics_events')

    # Drop ENUM
    event_type_enum = postgresql.ENUM(
        'PAGE_VIEW', 'CONVERSION', 'FORM_SUBMIT', 'BUTTON_CLICK', 'SCROLL', 'TIME_ON_PAGE',
        name='eventtype'
    )
    event_type_enum.drop(op.get_bind())
