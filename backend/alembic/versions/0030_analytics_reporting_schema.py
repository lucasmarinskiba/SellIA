"""Create analytics & reporting schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '0030'
down_revision = '0029'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE SCHEMA IF NOT EXISTS analytics')

    # Custom dashboards
    op.create_table(
        'dashboards',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('widgets', JSONB, nullable=False),
        sa.Column('layout', sa.String(50)),
        sa.Column('is_default', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        schema='analytics',
    )

    # Scheduled reports
    op.create_table(
        'scheduled_reports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('query', sa.Text, nullable=False),
        sa.Column('schedule', sa.String(50), nullable=False),
        sa.Column('recipients', JSONB, nullable=False),
        sa.Column('format', sa.String(20)),
        sa.Column('last_run', sa.DateTime),
        sa.Column('next_run', sa.DateTime),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='analytics',
    )

    # Report executions
    op.create_table(
        'report_executions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('report_id', UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('row_count', sa.Integer),
        sa.Column('file_url', sa.String(500)),
        sa.Column('error', sa.Text),
        sa.Column('executed_at', sa.DateTime, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='analytics',
    )

    # Metrics snapshots
    op.create_table(
        'metrics_snapshots',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('metric_date', sa.Date, nullable=False),
        sa.Column('metrics', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='analytics',
    )

    # Data exports
    op.create_table(
        'data_exports',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('format', sa.String(20), nullable=False),
        sa.Column('filters', JSONB),
        sa.Column('file_url', sa.String(500)),
        sa.Column('row_count', sa.Integer),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('expires_at', sa.DateTime),
        schema='analytics',
    )

    # BI connections
    op.create_table(
        'bi_connections',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('provider', sa.String(50), nullable=False),
        sa.Column('config', JSONB, nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('last_sync', sa.DateTime),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='analytics',
    )

    # Create indexes
    op.create_index('idx_dashboards_user_id', 'dashboards', ['user_id'], schema='analytics')
    op.create_index('idx_scheduled_reports_user_id', 'scheduled_reports', ['user_id'], schema='analytics')
    op.create_index('idx_metrics_snapshots_user_id', 'metrics_snapshots', ['user_id'], schema='analytics')
    op.create_index('idx_data_exports_user_id', 'data_exports', ['user_id'], schema='analytics')


def downgrade():
    op.execute('DROP SCHEMA IF EXISTS analytics CASCADE')
