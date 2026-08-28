"""SEO Auto-Optimization API."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.cache import cached
from app.domains.seo_optimization.service import (
    TitleOptimizationService,
    MetaOptimizationService,
    ContentOptimizationService,
    OptimizationTaskService,
)
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/seo-optimization", tags=["SEO Optimization"])


@router.post("/titles/generate")
async def generate_title_variants(
    business_id: UUID,
    page_url: str = Query(...),
    current_title: str = Query(...),
    keyword_target: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate title tag variants."""
    svc = TitleOptimizationService(db)
    variants = await svc.generate_title_variants(
        business_id, page_url, current_title, keyword_target
    )
    return {
        "optimization_id": variants.id,
        "variant_a": variants.variant_a,
        "variant_a_ctr": variants.variant_a_projected_ctr,
        "variant_b": variants.variant_b,
        "variant_b_ctr": variants.variant_b_projected_ctr,
        "variant_c": variants.variant_c,
        "variant_c_ctr": variants.variant_c_projected_ctr,
        "best_variant": "b",  # Usually wins
    }


@router.post("/meta/generate")
async def generate_meta_variants(
    business_id: UUID,
    page_url: str = Query(...),
    current_meta: str = Query(...),
    keyword_target: str = Query(...),
    cta: str = Query(default="Learn more"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate meta description variants."""
    svc = MetaOptimizationService(db)
    variants = await svc.generate_meta_variants(
        business_id, page_url, current_meta, keyword_target, cta
    )
    return {
        "optimization_id": variants.id,
        "variant_a": variants.variant_a,
        "variant_a_ctr": variants.variant_a_projected_ctr,
        "variant_b": variants.variant_b,
        "variant_b_ctr": variants.variant_b_projected_ctr,
        "recommended": "variant_b",
    }


@router.post("/content/analyze")
async def analyze_content(
    business_id: UUID,
    page_url: str = Query(...),
    keyword_target: str = Query(...),
    word_count: int = Query(...),
    keyword_density: float = Query(...),
    readability: float = Query(default=60.0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Analyze content and generate recommendations."""
    svc = ContentOptimizationService(db)
    analysis = await svc.analyze_content(
        business_id,
        page_url,
        keyword_target,
        word_count,
        keyword_density,
        readability,
    )
    return {
        "optimization_id": analysis.id,
        "recommendations": analysis.recommendations,
        "recommended_word_count": analysis.recommended_word_count,
        "engagement_score": analysis.engagement_score,
    }


@router.post("/tasks")
async def create_optimization_task(
    business_id: UUID,
    page_url: str = Query(...),
    task_type: str = Query(...),
    priority: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create optimization task."""
    svc = OptimizationTaskService(db)
    task = await svc.create_task(business_id, page_url, task_type, priority)
    return {
        "task_id": task.id,
        "status": task.status,
        "priority": task.priority,
        "estimated_impact": task.potential_impact,
    }


@router.get("/tasks/pending")
@cached(ttl_seconds=300, key_prefix="pending_tasks")
async def list_pending_tasks(
    business_id: UUID,
    priority: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List pending optimization tasks (cached 5min)."""
    svc = OptimizationTaskService(db)
    tasks = await svc.list_pending_tasks(business_id, priority)
    return {
        "total_pending": len(tasks),
        "tasks": [
            {
                "task_id": t.id,
                "type": t.task_type,
                "priority": t.priority,
                "page": t.page_url,
                "impact": t.potential_impact,
            }
            for t in tasks
        ],
    }


@router.patch("/tasks/{task_id}/execute")
async def execute_task(
    business_id: UUID,
    task_id: UUID,
    executed_by: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Execute optimization task."""
    svc = OptimizationTaskService(db)
    task = await svc.execute_task(task_id, executed_by)
    return {
        "task_id": task.id,
        "status": task.status,
        "applied_at": task.applied_at,
    }


@router.patch("/tasks/{task_id}/results")
async def track_results(
    business_id: UUID,
    task_id: UUID,
    pre_rank: int = Query(...),
    post_rank: int = Query(...),
    traffic_change_pct: float = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Track optimization results."""
    svc = OptimizationTaskService(db)
    task = await svc.track_results(task_id, pre_rank, post_rank, traffic_change_pct)
    return {
        "task_id": task.id,
        "rank_improvement": task.rank_improvement,
        "traffic_lift_pct": task.traffic_change_pct,
        "status": task.status,
    }


@router.get("/dashboard")
@cached(ttl_seconds=3600, key_prefix="opt_dashboard")
async def optimization_dashboard(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get optimization impact dashboard (cached 1h)."""
    svc = OptimizationTaskService(db)
    dashboard = await svc.impact_dashboard(business_id)
    return dashboard
