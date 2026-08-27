"""Add ad-budget autopilot tables

Revision ID: v2w3x4y5z6a7
Revises: u1v2w3x4y5z6
Create Date: 2026-08-27 01:00:00.000000+00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "v2w3x4y5z6a7"
down_revision: Union[str, Sequence[str], None] = "u1v2w3x4y5z6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _uuid():
    return postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "ad_budget_configs",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("business_id", _uuid(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_paused", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("paused_reason", sa.Text(), nullable=True),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("total_daily_budget", sa.Numeric(14, 2), nullable=True),
        sa.Column("optimization_window_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("target_roas", sa.Numeric(8, 3), nullable=False, server_default="2.0"),
        sa.Column("kill_roas", sa.Numeric(8, 3), nullable=False, server_default="0.7"),
        sa.Column("min_channel_share", sa.Numeric(5, 4), nullable=False, server_default="0.1"),
        sa.Column("max_daily_shift_pct", sa.Numeric(5, 4), nullable=False, server_default="0.25"),
        sa.Column("aggressiveness", sa.Numeric(4, 2), nullable=False, server_default="1.5"),
        sa.Column("allow_pause", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("min_data_conversions", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="ARS"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_status", sa.String(24), nullable=True),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_id", name="uq_ad_budget_config_business"),
    )
    op.create_index("ix_ad_budget_configs_business_id", "ad_budget_configs", ["business_id"])

    op.create_table(
        "ad_channels",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("business_id", _uuid(), nullable=False),
        sa.Column("channel_connection_id", _uuid(), nullable=True),
        sa.Column("platform", sa.String(16), nullable=False),
        sa.Column("display_name", sa.String(120), nullable=False),
        sa.Column("current_daily_budget", sa.Numeric(14, 2), nullable=False, server_default="0"),
        sa.Column("min_daily_budget", sa.Numeric(14, 2), nullable=True),
        sa.Column("max_daily_budget", sa.Numeric(14, 2), nullable=True),
        sa.Column("is_managed", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("is_paused", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("campaign_refs", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("attribution_match", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("currency", sa.String(3), nullable=False, server_default="ARS"),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_id", "platform", "display_name",
                            name="uq_ad_channel_business_platform_name"),
    )
    op.create_index("ix_ad_channels_business_id", "ad_channels", ["business_id"])
    op.create_index("ix_ad_channels_business_platform", "ad_channels", ["business_id", "platform"])

    op.create_table(
        "ad_performance_snapshots",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("business_id", _uuid(), nullable=False),
        sa.Column("ad_channel_id", _uuid(), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(16), nullable=False, server_default="ledger"),
        sa.Column("spend", sa.Numeric(16, 2), nullable=False, server_default="0"),
        sa.Column("revenue", sa.Numeric(16, 2), nullable=False, server_default="0"),
        sa.Column("conversions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clicks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("impressions", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("roas", sa.Numeric(10, 4), nullable=False, server_default="0"),
        sa.Column("cpa", sa.Numeric(14, 2), nullable=True),
        sa.Column("recent_roas", sa.Numeric(10, 4), nullable=True),
        sa.Column("captured_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["ad_channel_id"], ["ad_channels.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ad_performance_snapshots_business_id", "ad_performance_snapshots", ["business_id"])
    op.create_index("ix_ad_performance_snapshots_ad_channel_id", "ad_performance_snapshots", ["ad_channel_id"])
    op.create_index("ix_ad_perf_channel_captured", "ad_performance_snapshots", ["ad_channel_id", "captured_at"])

    op.create_table(
        "budget_reallocations",
        sa.Column("id", _uuid(), nullable=False),
        sa.Column("business_id", _uuid(), nullable=False),
        sa.Column("run_id", _uuid(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="recommended"),
        sa.Column("blended_roas", sa.Numeric(10, 4), nullable=True),
        sa.Column("total_budget_before", sa.Numeric(16, 2), nullable=False, server_default="0"),
        sa.Column("total_budget_after", sa.Numeric(16, 2), nullable=False, server_default="0"),
        sa.Column("decisions", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("window_days", sa.Integer(), nullable=False, server_default="14"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("applied_by", _uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_budget_reallocations_business_id", "budget_reallocations", ["business_id"])
    op.create_index("ix_budget_reallocations_business_created", "budget_reallocations", ["business_id", "created_at"])


def downgrade() -> None:
    op.drop_table("budget_reallocations")
    op.drop_table("ad_performance_snapshots")
    op.drop_table("ad_channels")
    op.drop_table("ad_budget_configs")
