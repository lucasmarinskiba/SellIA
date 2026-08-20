"""Phase 5: Performance Optimization Endpoints."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Optional, List
from app.core.database import get_db
from app.domains.performance_optimization.service import PerformanceOptimizationService


router = APIRouter(prefix="/api/v1/performance-optimization", tags=["performance-optimization"])


@router.post("/record-metrics")
async def record_metrics(
    business_id: UUID,
    total_requests: int = 0,
    total_errors: int = 0,
    avg_response_time_ms: float = 0,
    p95_latency_ms: float = 0,
    p99_latency_ms: float = 0,
    requests_per_second: float = 0,
    db_avg_query_time_ms: float = 0,
    cache_hit_rate: float = 0,
    memory_usage_mb: float = 0,
    cpu_usage_percent: float = 0,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Record system performance metrics."""
    result = await PerformanceOptimizationService.record_performance_metrics(
        db,
        business_id,
        total_requests,
        total_errors,
        avg_response_time_ms,
        p95_latency_ms,
        p99_latency_ms,
        requests_per_second,
        db_avg_query_time_ms,
        cache_hit_rate,
        memory_usage_mb,
        cpu_usage_percent,
    )
    return result


@router.post("/identify-slow-query")
async def identify_slow_query(
    business_id: UUID,
    query_signature: str,
    avg_execution_time_ms: float,
    execution_count: int = 1,
    max_execution_time_ms: Optional[float] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Identify and log slow query."""
    result = await PerformanceOptimizationService.identify_slow_queries(
        db,
        business_id,
        query_signature,
        avg_execution_time_ms,
        execution_count,
        max_execution_time_ms or avg_execution_time_ms,
    )
    return result


@router.post("/recommend-index")
async def recommend_index(
    business_id: UUID,
    table_name: str,
    column_names: List[str],
    estimated_queries_improved: int = 0,
    estimated_improvement_percent: float = 0,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Recommend database index."""
    result = await PerformanceOptimizationService.recommend_indexes(
        db,
        business_id,
        table_name,
        column_names,
        estimated_queries_improved,
        estimated_improvement_percent,
    )
    return result


@router.post("/configure-cache")
async def configure_cache(
    business_id: UUID,
    cache_type: str = "redis",
    ttl_seconds: int = 3600,
    max_size_mb: float = 256,
    cache_patterns: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Configure caching strategy."""
    result = await PerformanceOptimizationService.configure_cache_strategy(
        db,
        business_id,
        cache_type,
        ttl_seconds,
        max_size_mb,
        cache_patterns,
    )
    return result


@router.get("/opportunities")
async def find_opportunities(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Identify optimization opportunities."""
    result = await PerformanceOptimizationService.identify_optimization_opportunities(
        db,
        business_id,
    )
    return result


@router.get("/report")
async def get_report(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get comprehensive performance report."""
    result = await PerformanceOptimizationService.get_performance_report(
        db,
        business_id,
    )
    return result
