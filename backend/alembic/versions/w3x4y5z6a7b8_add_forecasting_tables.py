"""Add demand-forecasting tables

Revision ID: w3x4y5z6a7b8
Revises: v2w3x4y5z6a7
Create Date: 2026-08-27 02:00:00.000000+00:00
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "w3x4y5z6a7b8"
down_revision: Union[str, Sequence[str], None] = "v2w3x4y5z6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _u():
    return postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "forecast_series",
        sa.Column("id", _u(), nullable=False),
        sa.Column("business_id", _u(), nullable=False),
        sa.Column("series_key", sa.String(200), nullable=False),
        sa.Column("level", sa.String(16), nullable=False),
        sa.Column("target", sa.String(16), nullable=False),
        sa.Column("grain", sa.String(10), nullable=False, server_default="daily"),
        sa.Column("key", sa.String(200), nullable=True),
        sa.Column("label", sa.String(200), nullable=True),
        sa.Column("country", sa.String(2), nullable=False, server_default="AR"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("intermittent", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("adi", sa.Numeric(10, 3), nullable=True),
        sa.Column("zero_share", sa.Numeric(6, 4), nullable=True),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_wape", sa.Numeric(10, 3), nullable=True),
        sa.Column("last_mase", sa.Numeric(10, 4), nullable=True),
        sa.Column("extra_data", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("business_id", "series_key", name="uq_forecast_series_business_key"),
    )
    op.create_index("ix_forecast_series_business_id", "forecast_series", ["business_id"])
    op.create_index("ix_forecast_series_business_active", "forecast_series", ["business_id", "is_active"])

    op.create_table(
        "forecast_runs",
        sa.Column("id", _u(), nullable=False),
        sa.Column("series_id", _u(), nullable=False),
        sa.Column("business_id", _u(), nullable=False),
        sa.Column("run_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("origin_date", sa.Date(), nullable=False),
        sa.Column("horizon", sa.Integer(), nullable=False),
        sa.Column("grain", sa.String(10), nullable=False, server_default="daily"),
        sa.Column("status", sa.String(10), nullable=False, server_default="ok"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("model_weights", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("chosen_models", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("backtest_summary", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("n_history", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wape_backtest", sa.Numeric(10, 3), nullable=True),
        sa.Column("mase_backtest", sa.Numeric(10, 4), nullable=True),
        sa.Column("pinball_backtest", sa.Numeric(14, 4), nullable=True),
        sa.Column("coverage_backtest", sa.Numeric(6, 4), nullable=True),
        sa.Column("total_forecast", sa.Numeric(18, 2), nullable=True),
        sa.Column("reconciled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["series_id"], ["forecast_series.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_forecast_runs_series_id", "forecast_runs", ["series_id"])
    op.create_index("ix_forecast_runs_business_id", "forecast_runs", ["business_id"])
    op.create_index("ix_forecast_runs_business_run_at", "forecast_runs", ["business_id", "run_at"])
    op.create_index("ix_forecast_runs_series_run_at", "forecast_runs", ["series_id", "run_at"])

    op.create_table(
        "forecast_points",
        sa.Column("id", _u(), nullable=False),
        sa.Column("run_id", _u(), nullable=False),
        sa.Column("series_id", _u(), nullable=False),
        sa.Column("business_id", _u(), nullable=False),
        sa.Column("target_date", sa.Date(), nullable=False),
        sa.Column("horizon_step", sa.Integer(), nullable=False),
        sa.Column("yhat", sa.Numeric(18, 4), nullable=False),
        sa.Column("q10", sa.Numeric(18, 4), nullable=True),
        sa.Column("q50", sa.Numeric(18, 4), nullable=True),
        sa.Column("q90", sa.Numeric(18, 4), nullable=True),
        sa.Column("quantiles", postgresql.JSONB(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["run_id"], ["forecast_runs.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["series_id"], ["forecast_series.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("run_id", "target_date", name="uq_forecast_point_run_date"),
    )
    op.create_index("ix_forecast_points_run_id", "forecast_points", ["run_id"])
    op.create_index("ix_forecast_points_series_id", "forecast_points", ["series_id"])
    op.create_index("ix_forecast_points_business_id", "forecast_points", ["business_id"])
    op.create_index("ix_forecast_points_target_date", "forecast_points", ["target_date"])
    op.create_index("ix_forecast_points_series_date", "forecast_points", ["series_id", "target_date"])

    op.create_table(
        "forecast_accuracy",
        sa.Column("id", _u(), nullable=False),
        sa.Column("series_id", _u(), nullable=False),
        sa.Column("business_id", _u(), nullable=False),
        sa.Column("run_id", _u(), nullable=True),
        sa.Column("evaluated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_start", sa.Date(), nullable=False),
        sa.Column("window_end", sa.Date(), nullable=False),
        sa.Column("horizon_bucket", sa.String(16), nullable=False),
        sa.Column("n", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("wape", sa.Numeric(10, 3), nullable=True),
        sa.Column("mape", sa.Numeric(10, 3), nullable=True),
        sa.Column("mase", sa.Numeric(10, 4), nullable=True),
        sa.Column("bias", sa.Numeric(10, 4), nullable=True),
        sa.Column("rmse", sa.Numeric(18, 4), nullable=True),
        sa.Column("coverage", sa.Numeric(6, 4), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["series_id"], ["forecast_series.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["business_id"], ["businesses.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["run_id"], ["forecast_runs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_forecast_accuracy_series_id", "forecast_accuracy", ["series_id"])
    op.create_index("ix_forecast_accuracy_business_id", "forecast_accuracy", ["business_id"])
    op.create_index("ix_forecast_accuracy_series_eval", "forecast_accuracy", ["series_id", "evaluated_at"])


def downgrade() -> None:
    op.drop_table("forecast_accuracy")
    op.drop_table("forecast_points")
    op.drop_table("forecast_runs")
    op.drop_table("forecast_series")
