"""Phase 5B: Add offline conversion tracking tables

Revision ID: 20260819_phase5b
Revises: 20260819_phase5a
Create Date: 2026-08-19 14:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20260819_phase5b'
down_revision: Union[str, None] = '20260819_phase5a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create offline conversion tracking tables."""

    # Create VisitType enum
    visit_type_enum = postgresql.ENUM(
        'WALK_IN', 'QR_SCAN', 'SCHEDULED_DEMO', 'SCHEDULED_TOUR',
        'SCHEDULED_APPOINTMENT', 'MANUAL_CHECKIN', 'GEOFENCE_ENTRY',
        name='visittype',
        create_type=True
    )
    visit_type_enum.create(op.get_bind(), checkfirst=True)

    # Create DemographicSource enum
    demographic_source_enum = postgresql.ENUM(
        'PHONE_MATCH', 'EMAIL_MATCH', 'GPS_MATCH', 'QR_DATA',
        'MANUAL_ENTRY', 'GEOFENCE',
        name='demographicsource',
        create_type=True
    )
    demographic_source_enum.create(op.get_bind(), checkfirst=True)

    # Create offline_conversions table
    op.create_table(
        'offline_conversions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('visit_type', postgresql.ENUM('WALK_IN', 'QR_SCAN', 'SCHEDULED_DEMO', 'SCHEDULED_TOUR',
                                                'SCHEDULED_APPOINTMENT', 'MANUAL_CHECKIN', 'GEOFENCE_ENTRY',
                                                name='visittype'),
                 nullable=False, server_default='WALK_IN'),
        sa.Column('visitor_phone', sa.String(20), nullable=True),
        sa.Column('visitor_email', sa.String(255), nullable=True),
        sa.Column('visitor_name', sa.String(255), nullable=True),
        sa.Column('visitor_latitude', sa.Float(), nullable=True),
        sa.Column('visitor_longitude', sa.Float(), nullable=True),
        sa.Column('visitor_ip_address', sa.String(50), nullable=True),
        sa.Column('demographic_source', postgresql.ENUM('PHONE_MATCH', 'EMAIL_MATCH', 'GPS_MATCH', 'QR_DATA',
                                                        'MANUAL_ENTRY', 'GEOFENCE',
                                                        name='demographicsource'),
                 nullable=True),
        sa.Column('confidence_score', sa.DECIMAL(3, 2), nullable=False, server_default='0'),
        sa.Column('entry_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('exit_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('dwell_minutes', sa.Integer(), nullable=True),
        sa.Column('purchased', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('purchase_amount', sa.DECIMAL(14, 2), nullable=True),
        sa.Column('contact_collected', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('order_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('staff_notes', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indices for offline_conversions
    op.create_index('idx_offline_conversions_business_date', 'offline_conversions', ['business_id', 'created_at'])
    op.create_index('idx_offline_conversions_location_date', 'offline_conversions', ['location_id', 'created_at'])
    op.create_index('idx_offline_conversions_phone', 'offline_conversions', ['visitor_phone'])
    op.create_index('idx_offline_conversions_email', 'offline_conversions', ['visitor_email'])
    op.create_index('idx_offline_conversions_conversation', 'offline_conversions', ['conversation_id'])

    # Create geo_proximity_events table
    op.create_table(
        'geo_proximity_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('visitor_phone', sa.String(20), nullable=True),
        sa.Column('visitor_email', sa.String(255), nullable=True),
        sa.Column('user_latitude', sa.Float(), nullable=False),
        sa.Column('user_longitude', sa.Float(), nullable=False),
        sa.Column('distance_km', sa.Float(), nullable=False),
        sa.Column('trigger_name', sa.String(100), nullable=False),
        sa.Column('automation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('automation_triggered', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('automation_executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indices for geo_proximity_events
    op.create_index('idx_proximity_events_business_date', 'geo_proximity_events', ['business_id', 'created_at'])
    op.create_index('idx_proximity_events_location_date', 'geo_proximity_events', ['location_id', 'created_at'])
    op.create_index('idx_proximity_events_trigger', 'geo_proximity_events', ['trigger_name'])

    # Create location_visit_metrics table
    op.create_table(
        'location_visit_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('business_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('location_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('metric_date', sa.String(10), nullable=False),
        sa.Column('total_visits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('walk_in_visits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('qr_scans', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('scheduled_visits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('visitors_converted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_purchase_value', sa.DECIMAL(14, 2), nullable=False, server_default='0'),
        sa.Column('avg_purchase_value', sa.DECIMAL(14, 2), nullable=False, server_default='0'),
        sa.Column('avg_dwell_minutes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('contact_collection_rate', sa.DECIMAL(5, 4), nullable=False, server_default='0'),
        sa.Column('hourly_visits_json', postgresql.JSON(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Indices for location_visit_metrics
    op.create_index('idx_location_metrics_business_date', 'location_visit_metrics', ['business_id', 'metric_date'])
    op.create_index('idx_location_metrics_location_date', 'location_visit_metrics', ['location_id', 'metric_date'])


def downgrade() -> None:
    """Revert changes."""

    # Drop indices
    op.drop_index('idx_location_metrics_location_date', table_name='location_visit_metrics')
    op.drop_index('idx_location_metrics_business_date', table_name='location_visit_metrics')
    op.drop_index('idx_proximity_events_trigger', table_name='geo_proximity_events')
    op.drop_index('idx_proximity_events_location_date', table_name='geo_proximity_events')
    op.drop_index('idx_proximity_events_business_date', table_name='geo_proximity_events')
    op.drop_index('idx_offline_conversions_conversation', table_name='offline_conversions')
    op.drop_index('idx_offline_conversions_email', table_name='offline_conversions')
    op.drop_index('idx_offline_conversions_phone', table_name='offline_conversions')
    op.drop_index('idx_offline_conversions_location_date', table_name='offline_conversions')
    op.drop_index('idx_offline_conversions_business_date', table_name='offline_conversions')

    # Drop tables
    op.drop_table('location_visit_metrics')
    op.drop_table('geo_proximity_events')
    op.drop_table('offline_conversions')

    # Drop enums
    visit_type_enum = postgresql.ENUM('WALK_IN', 'QR_SCAN', 'SCHEDULED_DEMO', 'SCHEDULED_TOUR',
                                      'SCHEDULED_APPOINTMENT', 'MANUAL_CHECKIN', 'GEOFENCE_ENTRY',
                                      name='visittype')
    visit_type_enum.drop(op.get_bind(), checkfirst=True)

    demographic_source_enum = postgresql.ENUM('PHONE_MATCH', 'EMAIL_MATCH', 'GPS_MATCH', 'QR_DATA',
                                              'MANUAL_ENTRY', 'GEOFENCE',
                                              name='demographicsource')
    demographic_source_enum.drop(op.get_bind(), checkfirst=True)
