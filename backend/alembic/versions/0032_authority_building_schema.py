"""Add authority building tables (Phase 3: E-E-A-T signals).

Revision ID: 0032_authority_building
Revises: 0031_platform_credentials
Create Date: 2026-08-14 16:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0032_authority_building"
down_revision = "0031_platform_credentials"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "testimonials",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seller_id", sa.String(255), nullable=False),
        sa.Column("customer_name", sa.String(255), nullable=False),
        sa.Column("customer_avatar", sa.String(500), nullable=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("video_url", sa.String(500), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("metrics", sa.Text(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_seller_testimonials", "testimonials", ["seller_id", "is_verified"])
    op.create_index("idx_featured", "testimonials", ["seller_id", "is_featured"])

    op.create_table(
        "awards",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seller_id", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("issuer", sa.String(255), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("badge_url", sa.String(500), nullable=True),
        sa.Column("certificate_url", sa.String(500), nullable=True),
        sa.Column("awarded_date", sa.DateTime(), nullable=False),
        sa.Column("valid_until", sa.DateTime(), nullable=True),
        sa.Column("verification_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_seller_awards", "awards", ["seller_id", "is_active"])
    op.create_index("idx_category", "awards", ["category", "awarded_date"])

    op.create_table(
        "platform_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seller_id", sa.String(255), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("platform_review_id", sa.String(255), nullable=True),
        sa.Column("reviewer_name", sa.String(255), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("review_text", sa.Text(), nullable=False),
        sa.Column("review_date", sa.DateTime(), nullable=False),
        sa.Column("is_verified_purchase", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("helpful_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("seller_response", sa.Text(), nullable=True),
        sa.Column("response_date", sa.DateTime(), nullable=True),
        sa.Column("is_flagged", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_seller_reviews", "platform_reviews", ["seller_id", "rating"])
    op.create_index("idx_platform_reviews", "platform_reviews", ["platform", "review_date"])

    op.create_table(
        "trust_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("seller_id", sa.String(255), nullable=False),
        sa.Column("score_date", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("review_rating_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("review_count_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("response_rate_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("verification_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("longevity_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("trust_score", sa.Float(), nullable=False, server_default="0"),
        sa.Column("rank_tier", sa.String(50), nullable=False, server_default="bronze"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_trust_seller", "trust_scores", ["seller_id", "score_date"])

    op.create_table(
        "seller_bios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("seller_id", sa.String(255), nullable=False, unique=True),
        sa.Column("full_name", sa.String(255), nullable=False),
        sa.Column("bio", sa.Text(), nullable=False),
        sa.Column("years_in_business", sa.Integer(), nullable=False),
        sa.Column("specialties", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("website_url", sa.String(500), nullable=True),
        sa.Column("media_appearances", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("certification_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_seller_bio", "seller_bios", ["seller_id"])


def downgrade() -> None:
    op.drop_index("idx_seller_bio", table_name="seller_bios")
    op.drop_table("seller_bios")
    op.drop_index("idx_trust_seller", table_name="trust_scores")
    op.drop_table("trust_scores")
    op.drop_index("idx_platform_reviews", table_name="platform_reviews")
    op.drop_index("idx_seller_reviews", table_name="platform_reviews")
    op.drop_table("platform_reviews")
    op.drop_index("idx_category", table_name="awards")
    op.drop_index("idx_seller_awards", table_name="awards")
    op.drop_table("awards")
    op.drop_index("idx_featured", table_name="testimonials")
    op.drop_index("idx_seller_testimonials", table_name="testimonials")
    op.drop_table("testimonials")
