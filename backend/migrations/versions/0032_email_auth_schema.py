"""Add email verification and account approval schema.

Revision ID: 0032
Revises: 0031
Create Date: 2026-08-12 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0032"
down_revision = "0031"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create email_verification_tokens table
    op.create_table(
        "email_verification_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("token", sa.String(255), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("verified_at", sa.DateTime(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("verification_attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_email_verification_token",
        "email_verification_tokens",
        ["token"],
    )
    op.create_index(
        "idx_email_verification_user",
        "email_verification_tokens",
        ["user_id"],
    )
    op.create_index(
        "idx_email_verification_email",
        "email_verification_tokens",
        ["email"],
    )

    # Create account_approvals table
    op.create_table(
        "account_approvals",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("role", sa.String(255), nullable=True),
        sa.Column("requested_at", sa.DateTime(), nullable=False),
        sa.Column("requested_by", sa.String(255), nullable=True),
        sa.Column("approval_status", sa.String(50), nullable=False, server_default="pending"),
        sa.Column("approved_by", sa.String(255), nullable=True),
        sa.Column("approved_at", sa.DateTime(), nullable=True),
        sa.Column("approval_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("auto_approved", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("auto_approval_rule", sa.String(50), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_approvals_user",
        "account_approvals",
        ["user_id"],
    )
    op.create_index(
        "idx_approvals_status",
        "account_approvals",
        ["approval_status"],
    )
    op.create_index(
        "idx_approvals_requested_at",
        "account_approvals",
        ["requested_at"],
    )

    # Create approval_audit_log table
    op.create_table(
        "approval_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("approval_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("action", sa.String(50), nullable=False),
        sa.Column("actor_id", sa.String(255), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("action_timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["approval_id"], ["account_approvals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_audit_approval",
        "approval_audit_log",
        ["approval_id"],
    )

    # Create email_templates table
    op.create_table(
        "email_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("template_name", sa.String(255), nullable=False, unique=True),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_email_templates_name",
        "email_templates",
        ["template_name"],
    )

    # Insert default email templates
    op.execute(
        """
        INSERT INTO email_templates (id, template_name, subject, body, created_at, updated_at)
        VALUES
            (gen_random_uuid(), 'email_verification', 'Verify your SellIA email address',
             '<h2>Welcome to SellIA!</h2><p>Click the link below to verify your email address:</p><p><a href="{{verification_url}}">Verify Email</a></p><p>This link expires in 24 hours.</p>',
             NOW(), NOW()),
            (gen_random_uuid(), 'approval_requested', 'New SellIA account approval needed',
             '<p>New user account pending approval:</p><p><strong>Name:</strong> {{full_name}}</p><p><strong>Email:</strong> {{email}}</p><p><strong>Company:</strong> {{company}}</p><p><a href="{{approval_url}}">Review & Approve</a></p>',
             NOW(), NOW()),
            (gen_random_uuid(), 'approval_approved', 'Your SellIA account is approved!',
             '<h2>Welcome to SellIA!</h2><p>Hi {{full_name}},</p><p>Your account has been approved and is ready to use.</p><p><a href="{{login_url}}">Log in to SellIA</a></p>',
             NOW(), NOW()),
            (gen_random_uuid(), 'approval_rejected', 'SellIA account approval - update needed',
             '<p>Hi {{full_name}},</p><p>Your account approval requires additional information:</p><p><strong>Reason:</strong> {{rejection_reason}}</p><p>Please contact us at {{support_email}} for assistance.</p>',
             NOW(), NOW());
        """
    )

    # Add columns to users table for email verification & approval tracking
    op.add_column("users", sa.Column("email_verified", sa.Boolean(), server_default="false"))
    op.add_column("users", sa.Column("verified_at", sa.DateTime(), nullable=True))
    op.add_column("users", sa.Column("account_approved", sa.Boolean(), server_default="false"))
    op.add_column("users", sa.Column("approval_status", sa.String(50), server_default="pending"))


def downgrade() -> None:
    # Drop columns from users table
    op.drop_column("users", "approval_status")
    op.drop_column("users", "account_approved")
    op.drop_column("users", "verified_at")
    op.drop_column("users", "email_verified")

    # Drop tables
    op.drop_table("email_templates")
    op.drop_table("approval_audit_log")
    op.drop_table("account_approvals")
    op.drop_table("email_verification_tokens")
