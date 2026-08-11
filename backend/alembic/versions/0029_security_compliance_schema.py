"""Create security & compliance schema."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision = '0029'
down_revision = '0028'
branch_labels = None
depends_on = None


def upgrade():
    op.execute('CREATE SCHEMA IF NOT EXISTS security')

    # Audit log (all user actions)
    op.create_table(
        'audit_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('resource_type', sa.String(100)),
        sa.Column('resource_id', sa.String(255)),
        sa.Column('ip_address', sa.String(50)),
        sa.Column('user_agent', sa.String(500)),
        sa.Column('changes', JSONB),
        sa.Column('status', sa.String(50)),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        schema='security',
    )

    # Access control (role-based)
    op.create_table(
        'roles',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), unique=True, nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('permissions', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='security',
    )

    op.create_table(
        'role_assignments',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('role_id', UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_by', sa.String(255)),
        sa.Column('assigned_at', sa.DateTime, nullable=False),
        schema='security',
    )

    # Encryption keys
    op.create_table(
        'encryption_keys',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('key_id', sa.String(100), unique=True, nullable=False),
        sa.Column('key_type', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
        sa.Column('rotated_at', sa.DateTime),
        schema='security',
    )

    # Data retention policies
    op.create_table(
        'data_retention_policies',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('resource_type', sa.String(100), nullable=False),
        sa.Column('retention_days', sa.Integer, nullable=False),
        sa.Column('auto_delete', sa.Boolean, default=False),
        sa.Column('anonymize', sa.Boolean, default=False),
        sa.Column('created_at', sa.DateTime, nullable=False),
        schema='security',
    )

    # GDPR consent tracking
    op.create_table(
        'gdpr_consents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('consent_type', sa.String(100), nullable=False),
        sa.Column('consent_given', sa.Boolean, nullable=False),
        sa.Column('consent_date', sa.DateTime, nullable=False),
        sa.Column('ip_address', sa.String(50)),
        sa.Column('user_agent', sa.String(500)),
        schema='security',
    )

    # Security incidents
    op.create_table(
        'security_incidents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('incident_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('affected_users', sa.Integer),
        sa.Column('details', JSONB),
        sa.Column('resolved', sa.Boolean, default=False),
        sa.Column('detected_at', sa.DateTime, nullable=False),
        sa.Column('resolved_at', sa.DateTime),
        schema='security',
    )

    # Compliance status
    op.create_table(
        'compliance_status',
        sa.Column('id', UUID(as_uuid=True), primary_key=True),
        sa.Column('framework', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('last_audit_date', sa.DateTime),
        sa.Column('next_audit_date', sa.DateTime),
        sa.Column('findings', JSONB),
        sa.Column('updated_at', sa.DateTime, nullable=False),
        schema='security',
    )

    # Create indexes
    op.create_index('idx_audit_log_user_id', 'audit_log', ['user_id'], schema='security')
    op.create_index('idx_audit_log_timestamp', 'audit_log', ['timestamp'], schema='security')
    op.create_index('idx_role_assignments_user_id', 'role_assignments', ['user_id'], schema='security')
    op.create_index('idx_gdpr_consents_user_id', 'gdpr_consents', ['user_id'], schema='security')
    op.create_index('idx_security_incidents_severity', 'security_incidents', ['severity'], schema='security')


def downgrade():
    op.execute('DROP SCHEMA IF EXISTS security CASCADE')
