"""Phase 5: Performance Optimization Service - Query, Cache, Index Strategy."""
from typing import List, Dict, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.domains.performance_optimization.models import (
    PerformanceMetrics,
    SlowQuery,
    IndexRecommendation,
    CacheStrategy,
    QueryOptimization,
)


class PerformanceOptimizationService:
    @staticmethod
    async def record_performance_metrics(
        db: AsyncSession,
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
    ) -> dict:
        """Record system performance metrics."""
        error_rate = total_errors / total_requests if total_requests > 0 else 0

        # Calculate performance score (0-100)
        score = 100
        if error_rate > 0.01:
            score -= 20  # errors
        if avg_response_time_ms > 500:
            score -= 15  # slow
        if cache_hit_rate < 0.5:
            score -= 10  # poor cache
        if memory_usage_mb > 1000:
            score -= 5  # high memory

        metrics = PerformanceMetrics(
            business_id=business_id,
            total_requests=total_requests,
            total_errors=total_errors,
            error_rate=error_rate,
            avg_response_time_ms=avg_response_time_ms,
            p95_latency_ms=p95_latency_ms,
            p99_latency_ms=p99_latency_ms,
            requests_per_second=requests_per_second,
            db_avg_query_time_ms=db_avg_query_time_ms,
            cache_hit_rate=cache_hit_rate,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
            performance_score=max(0, score),
        )
        db.add(metrics)
        await db.commit()
        await db.refresh(metrics)

        return {
            "performance_score": metrics.performance_score,
            "error_rate": round(error_rate * 100, 2),
            "avg_response_time_ms": avg_response_time_ms,
            "cache_hit_rate": round(cache_hit_rate * 100, 2),
        }

    @staticmethod
    async def identify_slow_queries(
        db: AsyncSession,
        business_id: UUID,
        query_signature: str,
        avg_execution_time_ms: float,
        execution_count: int = 1,
        max_execution_time_ms: float = 0,
    ) -> dict:
        """Log and analyze slow query."""
        result = await db.execute(
            select(SlowQuery).where(
                (SlowQuery.business_id == business_id)
                & (SlowQuery.query_signature == query_signature)
            )
        )
        slow_query = result.scalar()

        if not slow_query:
            slow_query = SlowQuery(
                business_id=business_id,
                query_signature=query_signature,
                avg_execution_time_ms=avg_execution_time_ms,
                max_execution_time_ms=max_execution_time_ms,
                min_execution_time_ms=avg_execution_time_ms,
                execution_count=execution_count,
            )
            db.add(slow_query)
        else:
            # Update existing record
            slow_query.execution_count += execution_count
            slow_query.total_execution_time_ms += avg_execution_time_ms * execution_count
            slow_query.avg_execution_time_ms = slow_query.total_execution_time_ms / slow_query.execution_count
            slow_query.max_execution_time_ms = max(slow_query.max_execution_time_ms, max_execution_time_ms)
            slow_query.last_seen_at = datetime.now(timezone.utc)

        # Auto-suggest optimization if query is > 1 second
        if avg_execution_time_ms > 1000:
            slow_query.optimization_urgency = 80
            if "SELECT" in query_signature and "JOIN" in query_signature:
                slow_query.recommended_optimization = "Consider adding composite index on join columns"
                slow_query.optimization_impact = 0.4  # 40% improvement expected
            elif "SELECT" in query_signature:
                slow_query.recommended_optimization = "Consider adding index on WHERE clause columns"
                slow_query.optimization_impact = 0.3

        await db.commit()
        await db.refresh(slow_query)

        return {
            "query_signature": slow_query.query_signature,
            "avg_execution_time_ms": round(slow_query.avg_execution_time_ms, 2),
            "execution_count": slow_query.execution_count,
            "optimization_urgency": slow_query.optimization_urgency,
            "recommended_optimization": slow_query.recommended_optimization,
        }

    @staticmethod
    async def recommend_indexes(
        db: AsyncSession,
        business_id: UUID,
        table_name: str,
        column_names: List[str],
        estimated_queries_improved: int = 0,
        estimated_improvement_percent: float = 0,
    ) -> dict:
        """Recommend database index."""
        result = await db.execute(
            select(IndexRecommendation).where(
                (IndexRecommendation.business_id == business_id)
                & (IndexRecommendation.table_name == table_name)
            )
        )
        existing = result.scalar()

        if existing:
            return {
                "status": "already_recommended",
                "table": table_name,
                "columns": column_names,
            }

        # Estimate index size (rough: 10% of table data per index)
        index_size_mb = len(column_names) * 10

        recommendation = IndexRecommendation(
            business_id=business_id,
            table_name=table_name,
            column_names=column_names,
            estimated_queries_improved=estimated_queries_improved,
            estimated_improvement_percent=estimated_improvement_percent,
            estimated_index_size_mb=index_size_mb,
            implementation_priority=min(100, estimated_queries_improved * 10),
        )

        if estimated_improvement_percent > 50:
            recommendation.maintenance_cost = "low"
        elif estimated_improvement_percent > 20:
            recommendation.maintenance_cost = "medium"
        else:
            recommendation.maintenance_cost = "high"

        db.add(recommendation)
        await db.commit()
        await db.refresh(recommendation)

        return {
            "table": table_name,
            "columns": column_names,
            "estimated_improvement_percent": estimated_improvement_percent,
            "estimated_index_size_mb": round(index_size_mb, 2),
            "maintenance_cost": recommendation.maintenance_cost,
            "priority": recommendation.implementation_priority,
        }

    @staticmethod
    async def configure_cache_strategy(
        db: AsyncSession,
        business_id: UUID,
        cache_type: str = "redis",
        ttl_seconds: int = 3600,
        max_size_mb: float = 256,
        cache_patterns: List[str] = None,
    ) -> dict:
        """Configure caching strategy."""
        result = await db.execute(
            select(CacheStrategy).where(CacheStrategy.business_id == business_id)
        )
        strategy = result.scalar()

        if not strategy:
            strategy = CacheStrategy(business_id=business_id)
            db.add(strategy)

        strategy.cache_type = cache_type
        strategy.ttl_seconds = ttl_seconds
        strategy.max_size_mb = max_size_mb
        strategy.cache_patterns = cache_patterns or ["user_*", "business_*", "product_*"]
        strategy.status = "active"

        # Estimate impact
        strategy.latency_improvement_percent = 35  # typical 35% latency reduction
        strategy.cpu_reduction_percent = 20
        strategy.db_load_reduction_percent = 40

        await db.commit()
        await db.refresh(strategy)

        return {
            "cache_type": strategy.cache_type,
            "ttl_seconds": strategy.ttl_seconds,
            "max_size_mb": strategy.max_size_mb,
            "patterns": strategy.cache_patterns,
            "estimated_latency_improvement_percent": strategy.latency_improvement_percent,
            "estimated_db_load_reduction_percent": strategy.db_load_reduction_percent,
        }

    @staticmethod
    async def identify_optimization_opportunities(
        db: AsyncSession,
        business_id: UUID,
    ) -> dict:
        """Scan for N+1 queries, missing indexes, etc."""
        # Get all slow queries
        slow_result = await db.execute(
            select(SlowQuery).where(
                (SlowQuery.business_id == business_id)
                & (SlowQuery.optimization_status == "unoptimized")
            )
        )
        slow_queries = slow_result.scalars().all()

        opportunities = []

        for query in slow_queries[:5]:
            # Detect N+1 pattern
            if "SELECT" in query.query_signature and query.execution_count > 100:
                opportunities.append({
                    "type": "n_plus_one",
                    "description": f"Query executed {query.execution_count} times - potential N+1",
                    "improvement_percent": 60,
                    "complexity": "medium",
                })

            # Detect missing index
            if query.avg_execution_time_ms > 1000:
                opportunities.append({
                    "type": "missing_index",
                    "description": f"Slow query ({query.avg_execution_time_ms}ms avg) - add index",
                    "improvement_percent": query.optimization_impact * 100 if query.optimization_impact else 30,
                    "complexity": "low",
                })

        # Add cache opportunity
        result = await db.execute(
            select(CacheStrategy).where(CacheStrategy.business_id == business_id)
        )
        cache = result.scalar()

        if not cache or cache.hit_rate < 0.5:
            opportunities.append({
                "type": "cache_strategy",
                "description": "Implement or improve caching layer",
                "improvement_percent": 35,
                "complexity": "medium",
            })

        return {
            "business_id": business_id,
            "opportunities": opportunities[:5],
            "total_improvement_potential": sum([o["improvement_percent"] for o in opportunities]),
            "recommendation": f"Implement {len(opportunities)} optimizations for ~{sum([o['improvement_potential'] for o in opportunities])}% improvement",
        }

    @staticmethod
    async def get_performance_report(
        db: AsyncSession,
        business_id: UUID,
    ) -> dict:
        """Get comprehensive performance report."""
        # Latest metrics
        result = await db.execute(
            select(PerformanceMetrics)
            .where(PerformanceMetrics.business_id == business_id)
            .order_by(PerformanceMetrics.created_at.desc())
            .limit(1)
        )
        latest = result.scalar()

        # Critical items
        slow_result = await db.execute(
            select(SlowQuery).where(
                (SlowQuery.business_id == business_id)
                & (SlowQuery.optimization_urgency > 70)
            )
        )
        critical_queries = slow_result.scalars().all()

        # Recommendations
        index_result = await db.execute(
            select(IndexRecommendation).where(
                (IndexRecommendation.business_id == business_id)
                & (IndexRecommendation.status == "recommended")
            )
        )
        pending_indexes = index_result.scalars().all()

        return {
            "business_id": business_id,
            "performance_score": latest.performance_score if latest else 100,
            "avg_response_time_ms": round(latest.avg_response_time_ms, 2) if latest else 0,
            "error_rate": round(latest.error_rate * 100, 2) if latest else 0,
            "cache_hit_rate": round(latest.cache_hit_rate * 100, 2) if latest else 0,
            "critical_slow_queries": len(critical_queries),
            "pending_index_recommendations": len(pending_indexes),
            "next_actions": [
                f"Optimize {len(critical_queries)} critical queries" if critical_queries else None,
                f"Implement {len(pending_indexes)} recommended indexes" if pending_indexes else None,
                "Configure caching strategy" if not latest or latest.cache_hit_rate < 0.5 else None,
            ],
        }
