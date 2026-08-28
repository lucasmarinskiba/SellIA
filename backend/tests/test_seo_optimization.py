"""SEO Optimization tests."""

import pytest
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.domains.seo_optimization.service import (
    TitleOptimizationService,
    MetaOptimizationService,
    ContentOptimizationService,
    OptimizationTaskService,
)
from app.domains.seo_optimization.models import (
    TitleOptimization,
    MetaOptimization,
    ContentOptimization,
    OptimizationTask,
    SEO_OPTIMIZATION_TABLES,
)


@pytest.fixture
async def db():
    """SQLite in-memory database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session_maker() as session:
        yield session
    await engine.dispose()


class TestTitleOptimization:
    async def test_generate_title_variants(self, db: AsyncSession):
        """Generate 3 title variants with CTR projections."""
        biz_id = UUID("12345678-1234-5678-1234-567812345678")
        svc = TitleOptimizationService(db)
        variants = await svc.generate_title_variants(
            biz_id,
            "https://example.com/page",
            "Old Title",
            "keyword"
        )
        assert variants.variant_a is not None
        assert variants.variant_b is not None
        assert variants.variant_c is not None
        assert variants.variant_a_projected_ctr > 0
        assert variants.variant_b_projected_ctr > variants.variant_a_projected_ctr

    async def test_select_variant(self, db: AsyncSession):
        """Select best variant."""
        biz_id = UUID("12345678-1234-5678-1234-567812345678")
        svc = TitleOptimizationService(db)
        variants = await svc.generate_title_variants(
            biz_id,
            "https://example.com/page",
            "Old Title",
            "keyword"
        )
        selected = await svc.select_variant(variants.id, "b")
        assert selected.selected_variant == selected.variant_b


class TestMetaOptimization:
    async def test_generate_meta_variants(self, db: AsyncSession):
        """Generate 2 meta variants with CTA."""
        biz_id = UUID("12345678-1234-5678-1234-567812345678")
        svc = MetaOptimizationService(db)
        variants = await svc.generate_meta_variants(
            biz_id,
            "https://example.com/page",
            "Old meta",
            "keyword",
            "Learn more"
        )
        assert variants.variant_a is not None
        assert variants.variant_b is not None
        assert len(variants.variant_a) <= 160
        assert len(variants.variant_b) <= 160
        assert variants.variant_b_projected_ctr > variants.variant_a_projected_ctr


class TestContentOptimization:
    async def test_analyze_content(self, db: AsyncSession):
        """Analyze content and generate recommendations."""
        biz_id = UUID("12345678-1234-5678-1234-567812345678")
        svc = ContentOptimizationService(db)
        analysis = await svc.analyze_content(
            biz_id,
            "https://example.com/page",
            "keyword",
            1500,
            0.3,
            65.0
        )
        assert analysis.word_count == 1500
        assert analysis.recommended_word_count > 1500
        assert analysis.recommendations is not None
        assert "add_h2" in analysis.recommendations
        assert analysis.engagement_score >= 0


class TestOptimizationTask:
    async def test_create_task(self, db: AsyncSession):
        """Create optimization task."""
        biz_id = UUID("12345678-1234-5678-1234-567812345678")
        svc = OptimizationTaskService(db)
        task = await svc.create_task(
            biz_id,
            "https://example.com/page",
            "title_rewrite",
            "high"
        )
        assert task.status == "pending"
        assert task.task_type == "title_rewrite"
        assert task.priority == "high"

    async def test_execute_task(self, db: AsyncSession):
        """Execute optimization task."""
        biz_id = UUID("12345678-1234-5678-1234-567812345678")
        svc = OptimizationTaskService(db)
        task = await svc.create_task(
            biz_id,
            "https://example.com/page",
            "title_rewrite",
            "high"
        )
        executed = await svc.execute_task(task.id, "user@example.com")
        assert executed.status == "in_progress"
        assert executed.applied_at is not None
        assert executed.applied is True

    async def test_track_results(self, db: AsyncSession):
        """Track optimization results."""
        biz_id = UUID("12345678-1234-5678-1234-567812345678")
        svc = OptimizationTaskService(db)
        task = await svc.create_task(
            biz_id,
            "https://example.com/page",
            "title_rewrite",
            "high"
        )
        await svc.execute_task(task.id, "user@example.com")
        result = await svc.track_results(task.id, 15, 8, 25.0)
        assert result.rank_improvement == 7
        assert result.traffic_change_pct == 25.0
        assert result.status == "completed"

    async def test_list_pending_tasks(self, db: AsyncSession):
        """List pending optimization tasks."""
        biz_id = UUID("12345678-1234-5678-1234-567812345678")
        svc = OptimizationTaskService(db)
        task1 = await svc.create_task(
            biz_id,
            "https://example.com/page1",
            "title_rewrite",
            "high"
        )
        task2 = await svc.create_task(
            biz_id,
            "https://example.com/page2",
            "meta_optimize",
            "medium"
        )
        pending = await svc.list_pending_tasks(biz_id)
        assert len(pending) == 2

    async def test_impact_dashboard(self, db: AsyncSession):
        """Get optimization impact dashboard."""
        biz_id = UUID("12345678-1234-5678-1234-567812345678")
        svc = OptimizationTaskService(db)
        task = await svc.create_task(
            biz_id,
            "https://example.com/page",
            "title_rewrite",
            "high"
        )
        await svc.execute_task(task.id, "user@example.com")
        await svc.track_results(task.id, 15, 8, 25.0)
        dashboard = await svc.impact_dashboard(biz_id)
        assert dashboard["completed_tasks"] == 1
        assert dashboard["total_rank_improvement"] == 7
        assert dashboard["avg_traffic_lift_pct"] == 25.0
