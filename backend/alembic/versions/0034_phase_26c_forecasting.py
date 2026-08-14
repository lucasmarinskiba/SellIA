"""Phase 26c: Deal Intelligence & Forecasting.

Revision ID: 0034_phase_26c_forecasting
Revises: 0033_phase_26_collaboration
Create Date: 2026-08-14 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0034_phase_26c_forecasting"
down_revision = "0033_phase_26_collaboration"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "deal_scores",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("deal_id", sa.String(255), nullable=False, unique=True),
        sa.Column("seller_id", sa.String(255), nullable=False),
        sa.Column("win_probability", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("confidence_level", sa.Float(), nullable=False, server_default="0"),
        sa.Column("stage_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("engagement_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("proposal_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("competition_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("timing_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("is_at_risk", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("risk_reason", sa.Text(), nullable=True),
        sa.Column("days_since_last_contact", sa.Float(), nullable=True),
        sa.Column("score_trend", sa.String(20), nullable=False, server_default="stable"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_deal_score", "deal_scores", ["seller_id", "win_probability"])
    op.create_index("idx_at_risk", "deal_scores", ["seller_id", "is_at_risk"])

    op.create_table(
        "forecast_snapshots",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("seller_id", sa.String(255), nullable=False),
        sa.Column("forecast_date", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("total_pipeline_value", sa.Float(), nullable=False, server_default="0"),
        sa.Column("weighted_pipeline", sa.Float(), nullable=False, server_default="0"),
        sa.Column("projected_revenue_30d", sa.Float(), nullable=False, server_default="0"),
        sa.Column("projected_revenue_60d", sa.Float(), nullable=False, server_default="0"),
        sa.Column("projected_revenue_90d", sa.Float(), nullable=False, server_default="0"),
        sa.Column("confidence_level", sa.Float(), nullable=False, server_default="0"),
        sa.Column("accuracy_vs_actual", sa.Float(), nullable=True),
        sa.Column("deal_breakdown", postgresql.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_forecast_seller", "forecast_snapshots", ["seller_id", "forecast_date"])

    op.create_table(
        "win_loss_analysis",
        sa.Column("id", sa.String(36), nullable=False),
        sa.Column("deal_id", sa.String(255), nullable=False),
        sa.Column("seller_id", sa.String(255), nullable=False),
        sa.Column("outcome", sa.String(20), nullable=False),
        sa.Column("final_value", sa.Float(), nullable=True),
        sa.Column("primary_reason", sa.String(255), nullable=False),
        sa.Column("secondary_reasons", sa.Text(), nullable=True),
        sa.Column("actions_taken", sa.Text(), nullable=True),
        sa.Column("days_to_close", sa.Float(), nullable=True),
        sa.Column("teachable_moments", sa.Text(), nullable=True),
        sa.Column("competitor_mentioned", sa.String(255), nullable=True),
        sa.Column("price_was_factor", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("timing_was_factor", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_win_loss", "win_loss_analysis", ["seller_id", "outcome"])


def downgrade() -> None:
    op.drop_index("idx_win_loss", table_name="win_loss_analysis")
    op.drop_table("win_loss_analysis")
    op.drop_index("idx_forecast_seller", table_name="forecast_snapshots")
    op.drop_table("forecast_snapshots")
    op.drop_index("idx_at_risk", table_name="deal_scores")
    op.drop_index("idx_deal_score", table_name="deal_scores")
    op.drop_table("deal_scores")
