"""Phase 26: Team Collaboration Hub - Real-time comments, approvals, handoffs.

Revision ID: 0033_phase_26_collaboration
Revises: 0032_authority_building
Create Date: 2026-08-14 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = "0033_phase_26_collaboration"
down_revision = "0032_authority_building"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deal_comments",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("deal_id", sa.String(255), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("user_name", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("mentions", sa.String(500), nullable=True),
        sa.Column("is_internal", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_deal_comments", "deal_comments", ["deal_id", "created_at"])

    op.create_table(
        "approval_chains",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("action_id", sa.String(255), nullable=False),
        sa.Column("action_type", sa.String(50), nullable=False),
        sa.Column("requester_id", sa.String(255), nullable=False),
        sa.Column("requester_name", sa.String(255), nullable=False),
        sa.Column("approval_steps", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("decision_by", sa.String(255), nullable=True),
        sa.Column("decision_at", sa.DateTime(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_approval_action", "approval_chains", ["action_id"])
    op.create_index("idx_approval_status", "approval_chains", ["status", "created_at"])

    op.create_table(
        "handoffs",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("deal_id", sa.String(255), nullable=False),
        sa.Column("from_user_id", sa.String(255), nullable=False),
        sa.Column("from_user_name", sa.String(255), nullable=False),
        sa.Column("to_user_id", sa.String(255), nullable=False),
        sa.Column("to_user_name", sa.String(255), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("context", sa.Text(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("accepted_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_handoff_deal", "handoffs", ["deal_id", "created_at"])
    op.create_index("idx_handoff_user", "handoffs", ["to_user_id", "status"])

    op.create_table(
        "team_notifications",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("related_deal_id", sa.String(255), nullable=True),
        sa.Column("related_user_id", sa.String(255), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_notif_user",
        "team_notifications",
        ["user_id", "is_read", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_notif_user", table_name="team_notifications")
    op.drop_table("team_notifications")
    op.drop_index("idx_handoff_user", table_name="handoffs")
    op.drop_index("idx_handoff_deal", table_name="handoffs")
    op.drop_table("handoffs")
    op.drop_index("idx_approval_status", table_name="approval_chains")
    op.drop_index("idx_approval_action", table_name="approval_chains")
    op.drop_table("approval_chains")
    op.drop_index("idx_deal_comments", table_name="deal_comments")
    op.drop_table("deal_comments")
