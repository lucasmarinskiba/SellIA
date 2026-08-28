"""SEO Auto-Optimization models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, Text, ForeignKey, func, Boolean, Float, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OptimizationTask(Base):
    """Automatic SEO optimization task."""
    __tablename__ = "seo_optimization_tasks"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    page_url: Mapped[str] = mapped_column(String(500))
    task_type: Mapped[str] = mapped_column(String(50))  # title_rewrite, meta_optimize, keyword_inject, speed_improve, structure_enhance
    priority: Mapped[str] = mapped_column(String(20))  # critical, high, medium, low
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, in_progress, completed, failed

    # Current values
    current_title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    current_meta: Mapped[str | None] = mapped_column(String(160), nullable=True)
    current_h1: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Proposed optimizations
    proposed_title: Mapped[str] = mapped_column(String(255))
    proposed_meta: Mapped[str] = mapped_column(String(160))
    proposed_h1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    proposed_changes: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Impact prediction
    potential_impact: Mapped[str] = mapped_column(String(20))  # high, medium, low
    estimated_traffic_lift_pct: Mapped[float] = mapped_column(default=0.0)

    # Execution
    applied: Mapped[bool] = mapped_column(default=False)
    applied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    applied_by: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Results tracking
    pre_optimization_rank: Mapped[int | None] = mapped_column(nullable=True)
    post_optimization_rank: Mapped[int | None] = mapped_column(nullable=True)
    rank_improvement: Mapped[int] = mapped_column(default=0)
    traffic_change_pct: Mapped[float] = mapped_column(default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class TitleOptimization(Base):
    """Title tag optimization strategies."""
    __tablename__ = "seo_title_optimization"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    page_url: Mapped[str] = mapped_column(String(500))

    current_title: Mapped[str] = mapped_column(String(255))
    keyword_target: Mapped[str] = mapped_column(String(255))
    modifier_words: Mapped[list | None] = mapped_column(JSONB, nullable=True)  # ["2024", "Guide", "Best"]

    variant_a: Mapped[str] = mapped_column(String(255))
    variant_b: Mapped[str] = mapped_column(String(255))
    variant_c: Mapped[str] = mapped_column(String(255))

    selected_variant: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Metrics
    current_ctr: Mapped[float] = mapped_column(default=0.0)
    variant_a_projected_ctr: Mapped[float] = mapped_column(default=0.0)
    variant_b_projected_ctr: Mapped[float] = mapped_column(default=0.0)
    variant_c_projected_ctr: Mapped[float] = mapped_column(default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class MetaOptimization(Base):
    """Meta description optimization."""
    __tablename__ = "seo_meta_optimization"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    page_url: Mapped[str] = mapped_column(String(500))

    current_meta: Mapped[str] = mapped_column(String(160))
    keyword_target: Mapped[str] = mapped_column(String(255))
    call_to_action: Mapped[str] = mapped_column(String(100))  # "Learn more", "Free trial", "Shop now"

    variant_a: Mapped[str] = mapped_column(String(160))
    variant_b: Mapped[str] = mapped_column(String(160))

    selected_variant: Mapped[str | None] = mapped_column(String(160), nullable=True)

    # Metrics
    current_ctr: Mapped[float] = mapped_column(default=0.0)
    variant_a_projected_ctr: Mapped[float] = mapped_column(default=0.0)
    variant_b_projected_ctr: Mapped[float] = mapped_column(default=0.0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContentOptimization(Base):
    """Content optimization strategies."""
    __tablename__ = "seo_content_optimization"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    page_url: Mapped[str] = mapped_column(String(500))

    keyword_target: Mapped[str] = mapped_column(String(255))
    current_keyword_density: Mapped[float] = mapped_column(default=0.0)
    optimal_keyword_density: Mapped[float] = mapped_column(default=1.5)

    recommendations: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Example: {"add_h2": ["Best SEO Tools", "How to Rank"], "add_internal_links": 3}

    word_count: Mapped[int] = mapped_column(default=0)
    recommended_word_count: Mapped[int] = mapped_column(default=0)

    readability_score: Mapped[float] = mapped_column(default=0.0)  # 0-100
    engagement_score: Mapped[float] = mapped_column(default=0.0)

    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, approved, applied

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


SEO_OPTIMIZATION_TABLES = [
    OptimizationTask.__table__,
    TitleOptimization.__table__,
    MetaOptimization.__table__,
    ContentOptimization.__table__,
]
