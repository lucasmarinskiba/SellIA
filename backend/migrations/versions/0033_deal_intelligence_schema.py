"""Add deal intelligence schema for Phase 27.

Revision ID: 0033
Revises: 0032
Create Date: 2026-08-12 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0033"
down_revision = "0032"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create deal_stakeholders table
    op.create_table(
        "deal_stakeholders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deal_id", sa.String(255), nullable=False),
        sa.Column("person_id", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("buyer_role", sa.String(50), nullable=False, server_default="influencer"),
        sa.Column("influence_level", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("engagement_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("last_email_open", sa.DateTime(), nullable=True),
        sa.Column("last_call_date", sa.DateTime(), nullable=True),
        sa.Column("email_open_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("meeting_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("message_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(50), nullable=False, server_default="active"),
        sa.Column("identified_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_deal_stakeholders_deal", "deal_stakeholders", ["deal_id"])
    op.create_index("idx_deal_stakeholders_role", "deal_stakeholders", ["buyer_role"])
    op.create_index("idx_deal_stakeholders_engagement", "deal_stakeholders", ["engagement_score"])

    # Create deal_probability_scores table
    op.create_table(
        "deal_probability_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deal_id", sa.String(255), nullable=False, unique=True),
        sa.Column("close_probability", sa.Float(), nullable=False),
        sa.Column("confidence_level", sa.Float(), nullable=True),
        sa.Column("features", postgresql.JSONB(), nullable=True),
        sa.Column("model_version", sa.String(50), nullable=True),
        sa.Column("prediction_date", sa.DateTime(), nullable=False),
        sa.Column("probability_low", sa.Float(), nullable=True),
        sa.Column("probability_high", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_prob_scores_deal", "deal_probability_scores", ["deal_id"])
    op.create_index("idx_prob_scores_probability", "deal_probability_scores", ["close_probability"])

    # Create deal_health_snapshots table
    op.create_table(
        "deal_health_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deal_id", sa.String(255), nullable=False),
        sa.Column("health_score", sa.Integer(), nullable=False),
        sa.Column("health_status", sa.String(20), nullable=False),
        sa.Column("engagement_health", sa.Integer(), nullable=True),
        sa.Column("momentum_health", sa.Integer(), nullable=True),
        sa.Column("buyer_health", sa.Integer(), nullable=True),
        sa.Column("competition_health", sa.Integer(), nullable=True),
        sa.Column("days_since_last_activity", sa.Integer(), nullable=True),
        sa.Column("stakeholder_churn_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("buying_committee_complete", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("economic_buyer_engaged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("recommended_actions", postgresql.JSONB(), nullable=True),
        sa.Column("snapshot_date", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_health_deal", "deal_health_snapshots", ["deal_id"])
    op.create_index("idx_health_status", "deal_health_snapshots", ["health_status"])
    op.create_index("idx_health_date", "deal_health_snapshots", ["snapshot_date"])

    # Create deal_health_alerts table
    op.create_table(
        "deal_health_alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deal_id", sa.String(255), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=True),
        sa.Column("alert_type", sa.String(50), nullable=False),
        sa.Column("severity", sa.String(20), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("recommended_action", sa.Text(), nullable=True),
        sa.Column("action_type", sa.String(50), nullable=True),
        sa.Column("triggered_at", sa.DateTime(), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(), nullable=True),
        sa.Column("action_taken", sa.Boolean(), nullable=False, server_default="false"),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_alerts_deal", "deal_health_alerts", ["deal_id"])
    op.create_index("idx_alerts_user", "deal_health_alerts", ["user_id"])
    op.create_index("idx_alerts_status", "deal_health_alerts", ["resolved_at"])

    # Create stakeholder_engagement_events table
    op.create_table(
        "stakeholder_engagement_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deal_id", sa.String(255), nullable=False),
        sa.Column("person_id", sa.String(255), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("engagement_value", sa.Integer(), nullable=False),
        sa.Column("event_details", postgresql.JSONB(), nullable=True),
        sa.Column("event_timestamp", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_engagement_deal_person",
        "stakeholder_engagement_events",
        ["deal_id", "person_id"],
    )
    op.create_index("idx_engagement_timestamp", "stakeholder_engagement_events", ["event_timestamp"])

    # Create model_predictions_cache table
    op.create_table(
        "model_predictions_cache",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("deal_id", sa.String(255), nullable=False, unique=True),
        sa.Column("prediction_json", postgresql.JSONB(), nullable=False),
        sa.Column("cache_created_at", sa.DateTime(), nullable=False),
        sa.Column("cache_expires_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["deal_id"], ["deals.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_cache_expires", "model_predictions_cache", ["cache_expires_at"])


def downgrade() -> None:
    op.drop_table("model_predictions_cache")
    op.drop_table("stakeholder_engagement_events")
    op.drop_table("deal_health_alerts")
    op.drop_table("deal_health_snapshots")
    op.drop_table("deal_probability_scores")
    op.drop_table("deal_stakeholders")
