"""Phase 5A: Add locations table and localization_model to businesses

Revision ID: 20260819_phase5a
Revises: (auto)
Create Date: 2026-08-19 12:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260819_phase5a'
down_revision: Union[str, None] = 'o5p6q7r8s9t0_full_baseline'  # Last migration
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create locations table and add localization_model to businesses."""

    # Add localization_model enum type
    localization_model_enum = postgresql.ENUM(
        'ONLINE_ONLY', 'HYBRID_LIGHT', 'HYBRID_HEAVY', 'OFFLINE_FIRST',
        name='localizationmodel',
        create_type=True
    )
    localization_model_enum.create(op.get_bind(), checkfirst=True)

    # Add localization_model column to businesses table
    op.add_column('businesses',
                  sa.Column('localization_model',
                           postgresql.ENUM('ONLINE_ONLY', 'HYBRID_LIGHT', 'HYBRID_HEAVY', 'OFFLINE_FIRST',
                                         name='localizationmodel'),
                           nullable=False,
                           server_default='ONLINE_ONLY',
                           comment='Business model classification for online/offline mix'))

    # Create locations table
    op.create_table(
        'locations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('address', sa.String(500), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('state_province', sa.String(100), nullable=True),
        sa.Column('postal_code', sa.String(20), nullable=True),
        sa.Column('country_code', sa.String(2), nullable=False, server_default='AR'),
        sa.Column('latitude', sa.Float(), nullable=False),
        sa.Column('longitude', sa.Float(), nullable=False),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('website_url', sa.String(500), nullable=True),
        sa.Column('google_maps_url', sa.String(1000), nullable=True),
        sa.Column('gmb_id', sa.String(255), nullable=True),
        sa.Column('hours_json', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('capacity', sa.String(100), nullable=True),
        sa.Column('wheelchair_accessible', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('parking_available', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('has_wifi', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allows_walk_ins', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allows_appointments', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allows_pickups', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('allows_demos', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('service_radius_km', sa.Float(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indices
    op.create_index('idx_locations_business_active', 'locations', ['business_id', 'is_active'])
    op.create_index('idx_locations_city', 'locations', ['city'])
    op.create_index('idx_locations_gmb', 'locations', ['gmb_id'])
    op.create_index('idx_business_localization', 'businesses', ['localization_model'])


def downgrade() -> None:
    """Revert changes."""

    # Drop indices
    op.drop_index('idx_business_localization', table_name='businesses')
    op.drop_index('idx_locations_gmb', table_name='locations')
    op.drop_index('idx_locations_city', table_name='locations')
    op.drop_index('idx_locations_business_active', table_name='locations')

    # Drop locations table
    op.drop_table('locations')

    # Drop localization_model column
    op.drop_column('businesses', 'localization_model')

    # Drop enum type
    localization_model_enum = postgresql.ENUM(
        'ONLINE_ONLY', 'HYBRID_LIGHT', 'HYBRID_HEAVY', 'OFFLINE_FIRST',
        name='localizationmodel'
    )
    localization_model_enum.drop(op.get_bind(), checkfirst=True)
