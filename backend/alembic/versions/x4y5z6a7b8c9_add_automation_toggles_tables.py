"""Add automation toggles and audit log tables

Revision ID: x4y5z6a7b8c9
Revises: w3x4y5z6a7b8
Create Date: 2026-09-11 15:00:00.000000+00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "x4y5z6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "w3x4y5z6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _u():
    return postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    # Create automation_toggles table
    op.create_table(
        "automation_toggles",
        sa.Column("id", _u(), nullable=False),
        sa.Column("business_id", _u(), nullable=False),
        sa.Column("toggle_key", sa.String(100), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("enabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("disabled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("monthly_limit", sa.Integer(), nullable=True),
        sa.Column("current_month_usage", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_reset_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("changed_by", _u(), nullable=True),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_business_toggle_key", "automation_toggles", ["business_id", "toggle_key"])
    op.create_index("ix_business_category", "automation_toggles", ["business_id", "category"])
    op.create_index("ix_automation_toggles_business_id", "automation_toggles", ["business_id"])

    # Create toggle_audit_logs table
    op.create_table(
        "toggle_audit_logs",
        sa.Column("id", _u(), nullable=False),
        sa.Column("business_id", _u(), nullable=False),
        sa.Column("toggle_id", _u(), nullable=False),
        sa.Column("action", sa.String(20), nullable=False),
        sa.Column("old_value", postgresql.JSONB(), nullable=True),
        sa.Column("new_value", postgresql.JSONB(), nullable=True),
        sa.Column("changed_by_user_id", _u(), nullable=True),
        sa.Column("changed_by_email", sa.String(255), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("leads_affected", sa.Integer(), nullable=True),
        sa.Column("estimated_impact_pct", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["toggle_id"], ["automation_toggles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["changed_by_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_business_toggle_audit", "toggle_audit_logs", ["business_id", "toggle_id"])
    op.create_index("ix_created_at", "toggle_audit_logs", ["created_at"])
    op.create_index("ix_toggle_audit_logs_business_id", "toggle_audit_logs", ["business_id"])


def downgrade() -> None:
    op.drop_index("ix_toggle_audit_logs_business_id", table_name="toggle_audit_logs")
    op.drop_index("ix_created_at", table_name="toggle_audit_logs")
    op.drop_index("ix_business_toggle_audit", table_name="toggle_audit_logs")
    op.drop_table("toggle_audit_logs")

    op.drop_index("ix_automation_toggles_business_id", table_name="automation_toggles")
    op.drop_index("ix_business_category", table_name="automation_toggles")
    op.drop_index("ix_business_toggle_key", table_name="automation_toggles")
    op.drop_table("automation_toggles")
