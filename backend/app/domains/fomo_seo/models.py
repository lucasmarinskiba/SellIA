"""FOMO+SEO integrated models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text, ForeignKey, func, Float, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class FOMOSEOCopy(Base):
    """Generated copy optimized for both FOMO psychology + SEO."""
    __tablename__ = "fomo_seo_copy"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    product_id: Mapped[UUID | None] = mapped_column(ForeignKey("products.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    meta_description: Mapped[str] = mapped_column(String(160))  # Google meta description limit
    short_description: Mapped[str] = mapped_column(String(500))
    long_description: Mapped[str] = mapped_column(Text)
    bullet_points: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    call_to_action: Mapped[str] = mapped_column(String(255))

    # FOMO elements
    urgency_trigger: Mapped[str | None] = mapped_column(String(100), nullable=True)  # limited_stock, ending_soon, best_seller, etc.
    social_proof_element: Mapped[str | None] = mapped_column(String(255), nullable=True)
    scarcity_message: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # SEO metrics
    keywords_targeted: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    keyword_density_score: Mapped[float] = mapped_column(default=0)  # 0-100
    readability_score: Mapped[float] = mapped_column(default=0)  # 0-100
    seo_score: Mapped[float] = mapped_column(default=0)  # 0-100

    # Performance
    ctr_score: Mapped[float] = mapped_column(default=0)  # Click-through rate potential (0-100)
    conversion_score: Mapped[float] = mapped_column(default=0)  # Conversion potential (0-100)

    platform: Mapped[str] = mapped_column(String(50))  # amazon, ebay, shopify, etc.
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft, active, archived
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class A_B_TestCopy(Base):
    """A/B test variants of FOMO+SEO copy."""
    __tablename__ = "fomo_seo_ab_tests"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    copy_id: Mapped[UUID] = mapped_column(ForeignKey("fomo_seo_copy.id", ondelete="CASCADE"))

    variant_a_title: Mapped[str] = mapped_column(String(255))
    variant_b_title: Mapped[str] = mapped_column(String(255))
    variant_a_description: Mapped[str] = mapped_column(String(500))
    variant_b_description: Mapped[str] = mapped_column(String(500))

    # Results
    variant_a_impressions: Mapped[int] = mapped_column(default=0)
    variant_a_clicks: Mapped[int] = mapped_column(default=0)
    variant_a_conversions: Mapped[int] = mapped_column(default=0)
    variant_a_ctr: Mapped[float] = mapped_column(default=0)
    variant_a_conversion_rate: Mapped[float] = mapped_column(default=0)

    variant_b_impressions: Mapped[int] = mapped_column(default=0)
    variant_b_clicks: Mapped[int] = mapped_column(default=0)
    variant_b_conversions: Mapped[int] = mapped_column(default=0)
    variant_b_ctr: Mapped[float] = mapped_column(default=0)
    variant_b_conversion_rate: Mapped[float] = mapped_column(default=0)

    winner: Mapped[str | None] = mapped_column(String(10), nullable=True)  # A, B, or None
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CopyPerformanceMetric(Base):
    """Track copy performance over time."""
    __tablename__ = "fomo_seo_performance"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    copy_id: Mapped[UUID] = mapped_column(ForeignKey("fomo_seo_copy.id", ondelete="CASCADE"))

    metric_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    impressions: Mapped[int] = mapped_column(default=0)
    clicks: Mapped[int] = mapped_column(default=0)
    ctr: Mapped[float] = mapped_column(default=0)
    conversions: Mapped[int] = mapped_column(default=0)
    conversion_rate: Mapped[float] = mapped_column(default=0)
    avg_position: Mapped[float] = mapped_column(default=0)

    tracked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


FOMO_SEO_TABLES = [FOMOSEOCopy.__table__, A_B_TestCopy.__table__, CopyPerformanceMetric.__table__]
