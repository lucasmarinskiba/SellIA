"""SEO Auto-Optimization services."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.seo_optimization.models import (
    OptimizationTask,
    TitleOptimization,
    MetaOptimization,
    ContentOptimization,
)

logger = get_logger(__name__)


class TitleOptimizationService:
    """Generate optimized title tags."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_title_variants(
        self,
        business_id: uuid.UUID,
        page_url: str,
        current_title: str,
        keyword_target: str,
        modifiers: Optional[list[str]] = None,
    ) -> TitleOptimization:
        """Generate title tag variants."""
        modifiers = modifiers or ["2024", "Guide", "Best"]

        # Generate variants using simple rules
        variant_a = f"{keyword_target} - {modifiers[0]} Guide"
        variant_b = f"Best {keyword_target} | {modifiers[1]} Edition"
        variant_c = f"{keyword_target}: Complete {modifiers[2]} Guide"

        # Project CTR based on formulas
        base_ctr = 2.5
        a_ctr = base_ctr * 1.15  # +15% for year indicator
        b_ctr = base_ctr * 1.25  # +25% for "Best" superlative
        c_ctr = base_ctr * 1.18  # +18% for structure

        optimization = TitleOptimization(
            business_id=business_id,
            page_url=page_url,
            current_title=current_title,
            keyword_target=keyword_target,
            modifier_words=modifiers,
            variant_a=variant_a,
            variant_b=variant_b,
            variant_c=variant_c,
            current_ctr=base_ctr,
            variant_a_projected_ctr=a_ctr,
            variant_b_projected_ctr=b_ctr,
            variant_c_projected_ctr=c_ctr,
        )
        self.db.add(optimization)
        await self.db.commit()
        logger.info(f"Title variants generated for {page_url}")
        return optimization

    async def select_variant(
        self,
        optimization_id: uuid.UUID,
        variant: str,  # a, b, or c
    ) -> TitleOptimization:
        """Select best variant."""
        optimization = (
            await self.db.execute(
                select(TitleOptimization).where(TitleOptimization.id == optimization_id)
            )
        ).scalar_one_or_none()
        if not optimization:
            raise ValueError(f"Optimization {optimization_id} not found")

        if variant == "a":
            optimization.selected_variant = optimization.variant_a
        elif variant == "b":
            optimization.selected_variant = optimization.variant_b
        elif variant == "c":
            optimization.selected_variant = optimization.variant_c

        await self.db.commit()
        return optimization


class MetaOptimizationService:
    """Generate optimized meta descriptions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_meta_variants(
        self,
        business_id: uuid.UUID,
        page_url: str,
        current_meta: str,
        keyword_target: str,
        call_to_action: str = "Learn more",
    ) -> MetaOptimization:
        """Generate meta description variants."""
        # Max 160 chars
        variant_a = f"Discover everything about {keyword_target}. Expert guide with tips & best practices. {call_to_action}."[:160]
        variant_b = f"Get the complete {keyword_target} guide. Proven strategies for success. Start free trial today. {call_to_action}."[:160]

        # Project CTR
        base_ctr = 2.0
        a_ctr = base_ctr * 1.20
        b_ctr = base_ctr * 1.35  # CTA + urgency usually wins

        optimization = MetaOptimization(
            business_id=business_id,
            page_url=page_url,
            current_meta=current_meta,
            keyword_target=keyword_target,
            call_to_action=call_to_action,
            variant_a=variant_a,
            variant_b=variant_b,
            current_ctr=base_ctr,
            variant_a_projected_ctr=a_ctr,
            variant_b_projected_ctr=b_ctr,
        )
        self.db.add(optimization)
        await self.db.commit()
        logger.info(f"Meta variants generated for {page_url}")
        return optimization


class ContentOptimizationService:
    """Generate content optimization recommendations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def analyze_content(
        self,
        business_id: uuid.UUID,
        page_url: str,
        keyword_target: str,
        current_word_count: int,
        current_density: float,
        readability_score: float = 60.0,
    ) -> ContentOptimization:
        """Analyze and recommend content optimizations."""
        recommendations = {"add_h2": [], "add_internal_links": 0}

        # Keyword density too low?
        if current_density < 0.5:
            recommendations["add_h2"] = ["How to Use", "Benefits", "Best Practices"]
            recommendations["add_internal_links"] = 2

        # Word count recommendations
        recommended_wc = max(2000, current_word_count * 1.3) if current_word_count < 2000 else current_word_count

        optimization = ContentOptimization(
            business_id=business_id,
            page_url=page_url,
            keyword_target=keyword_target,
            current_keyword_density=current_density,
            word_count=current_word_count,
            recommended_word_count=int(recommended_wc),
            readability_score=readability_score,
            engagement_score=min(100, readability_score + 15),
            recommendations=recommendations,
        )
        self.db.add(optimization)
        await self.db.commit()
        logger.info(f"Content optimization generated for {page_url}")
        return optimization


class OptimizationTaskService:
    """Manage optimization task execution."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_task(
        self,
        business_id: uuid.UUID,
        page_url: str,
        task_type: str,
        priority: str,
        proposed_title: Optional[str] = None,
        proposed_meta: Optional[str] = None,
        estimated_impact: str = "medium",
        impact_pct: float = 0.0,
    ) -> OptimizationTask:
        """Create optimization task."""
        task = OptimizationTask(
            business_id=business_id,
            page_url=page_url,
            task_type=task_type,
            priority=priority,
            proposed_title=proposed_title or "",
            proposed_meta=proposed_meta or "",
            potential_impact=estimated_impact,
            estimated_traffic_lift_pct=impact_pct,
        )
        self.db.add(task)
        await self.db.commit()
        logger.info(f"Optimization task created: {task_type} for {page_url}")
        return task

    async def execute_task(
        self,
        task_id: uuid.UUID,
        applied_by: str,
    ) -> OptimizationTask:
        """Execute optimization task."""
        task = (
            await self.db.execute(
                select(OptimizationTask).where(OptimizationTask.id == task_id)
            )
        ).scalar_one_or_none()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.status = "in_progress"
        task.applied_at = datetime.now(timezone.utc)
        task.applied_by = applied_by
        task.applied = True
        await self.db.commit()
        logger.info(f"Optimization task executed: {task.task_type}")
        return task

    async def track_results(
        self,
        task_id: uuid.UUID,
        pre_rank: int,
        post_rank: int,
        traffic_change: float,
    ) -> OptimizationTask:
        """Track optimization results."""
        task = (
            await self.db.execute(
                select(OptimizationTask).where(OptimizationTask.id == task_id)
            )
        ).scalar_one_or_none()
        if not task:
            raise ValueError(f"Task {task_id} not found")

        task.pre_optimization_rank = pre_rank
        task.post_optimization_rank = post_rank
        task.rank_improvement = pre_rank - post_rank  # positive = better
        task.traffic_change_pct = traffic_change
        task.status = "completed"
        task.executed_at = datetime.now(timezone.utc)
        await self.db.commit()
        logger.info(f"Task results tracked: rank improvement={task.rank_improvement}, traffic={traffic_change}%")
        return task

    async def list_pending_tasks(
        self,
        business_id: uuid.UUID,
        priority: Optional[str] = None,
    ) -> list[OptimizationTask]:
        """List pending optimization tasks."""
        query = select(OptimizationTask).where(
            and_(
                OptimizationTask.business_id == business_id,
                OptimizationTask.status == "pending",
            )
        )
        if priority:
            query = query.where(OptimizationTask.priority == priority)
        query = query.order_by(OptimizationTask.priority)
        return (await self.db.execute(query)).scalars().all()

    async def impact_dashboard(self, business_id: uuid.UUID) -> dict:
        """Get optimization impact dashboard."""
        tasks = (
            await self.db.execute(
                select(OptimizationTask).where(
                    and_(
                        OptimizationTask.business_id == business_id,
                        OptimizationTask.status == "completed",
                    )
                )
            )
        ).scalars().all()

        total_tasks = len(tasks)
        total_rank_improvement = sum(t.rank_improvement for t in tasks if t.rank_improvement)
        avg_traffic_lift = sum(t.traffic_change_pct for t in tasks) / total_tasks if tasks else 0

        return {
            "completed_tasks": total_tasks,
            "total_rank_improvement": total_rank_improvement,
            "avg_traffic_lift_pct": avg_traffic_lift,
            "tasks_by_type": self._group_by_type(tasks),
        }

    def _group_by_type(self, tasks: list[OptimizationTask]) -> dict:
        """Group tasks by type."""
        grouped = {}
        for task in tasks:
            if task.task_type not in grouped:
                grouped[task.task_type] = 0
            grouped[task.task_type] += 1
        return grouped
