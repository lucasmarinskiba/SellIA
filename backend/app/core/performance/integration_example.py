"""
Integration Example — How to use PHASE 8 Performance modules in FastAPI.

This file demonstrates production-ready integration patterns for:
- Database optimization
- Caching strategies
- Async job processing
- Performance monitoring
- Load testing
"""

import time
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.performance import (
    DatabaseOptimizer,
    CacheLayer,
    AsyncJobQueue,
    PerformanceMonitor,
    LoadTestRunner,
    LoadTestConfig,
    JobPriority,
)

logger = logging.getLogger(__name__)

# ============================================================================
# INITIALIZATION
# ============================================================================

def setup_performance_stack(app: FastAPI, redis_client: Optional[Any] = None) -> Dict[str, Any]:
    """
    Set up the complete performance stack.

    This function should be called during FastAPI startup to initialize
    all performance monitoring and optimization modules.

    Example:
        @app.on_event("startup")
        async def startup():
            app.state.performance = setup_performance_stack(app, redis_client)
            await app.state.performance["job_queue"].start_workers()
    """

    # Initialize performance modules
    db_optimizer = DatabaseOptimizer()
    cache_layer = CacheLayer(redis_client=redis_client)
    job_queue = AsyncJobQueue(worker_count=4, max_queue_size=10000)
    monitor = PerformanceMonitor(max_history=10000)
    load_test_runner = LoadTestRunner()

    performance_stack = {
        "db_optimizer": db_optimizer,
        "cache": cache_layer,
        "job_queue": job_queue,
        "monitor": monitor,
        "load_tester": load_test_runner,
    }

    logger.info("Performance stack initialized")
    return performance_stack


# ============================================================================
# MIDDLEWARE FOR AUTOMATIC PERFORMANCE TRACKING
# ============================================================================

async def performance_tracking_middleware(app: FastAPI, performance: Dict[str, Any]):
    """
    Middleware to automatically track endpoint performance.

    Example:
        @app.middleware("http")
        async def track_performance(request, call_next):
            await performance_tracking_middleware(app, app.state.performance)
    """

    async def middleware(request, call_next):
        start_time = time.time()
        endpoint = request.url.path
        method = request.method

        try:
            response = await call_next(request)
        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000
            performance["monitor"].record_endpoint_time(
                endpoint=endpoint,
                method=method,
                response_time_ms=response_time_ms,
                status_code=500,
            )
            raise

        response_time_ms = (time.time() - start_time) * 1000
        performance["monitor"].record_endpoint_time(
            endpoint=endpoint,
            method=method,
            response_time_ms=response_time_ms,
            status_code=response.status_code,
        )

        return response

    return middleware


# ============================================================================
# EXAMPLE: DATABASE OPTIMIZATION
# ============================================================================

async def get_agents_with_optimization(
    db: AsyncSession = Depends(get_db),
    cache: CacheLayer = Depends(lambda: Depends(get_cache_layer)),
    db_optimizer: DatabaseOptimizer = Depends(lambda: Depends(get_db_optimizer)),
) -> list:
    """
    Example endpoint that uses caching and database optimization.
    """

    # Check cache first
    cached_agents = await cache.get_kpi("system", "all_agents")
    if cached_agents is not None:
        logger.info("Cache hit for all_agents")
        return cached_agents

    # Cache miss - execute query and track performance
    start_time = time.time()

    # TODO: Replace with actual query
    agents = []
    # agents = await db.query(Agent).all()

    execution_time_ms = (time.time() - start_time) * 1000

    # Log slow query if needed
    if execution_time_ms > 100:
        await db_optimizer.log_slow_query(
            query="SELECT * FROM agents",
            execution_time_ms=execution_time_ms,
            rows_scanned=len(agents) * 10,  # Estimate
            rows_returned=len(agents),
            endpoint="/api/agents",
        )

    # Cache result
    await cache.cache_kpi(
        agent_id="system",
        metric_name="all_agents",
        value=agents,
        ttl_seconds=1800,  # 30 minutes
    )

    return agents


# ============================================================================
# EXAMPLE: ASYNC JOB PROCESSING
# ============================================================================

async def enqueue_agent_import(
    file_path: str,
    user_id: str,
    job_queue: AsyncJobQueue = Depends(lambda: Depends(get_job_queue)),
    background_tasks: BackgroundTasks = Depends(),
) -> Dict[str, str]:
    """
    Example: Enqueue long-running import task.

    POST /api/agents/import
    {
        "file_path": "/uploads/agents.csv"
    }
    """

    # Enqueue the job with high priority
    job = job_queue.enqueue(
        task=process_agent_csv_import,
        name=f"import_agents_{user_id}",
        args=(file_path, user_id),
        priority=JobPriority.HIGH,
        timeout_seconds=3600,  # 1 hour timeout
    )

    logger.info(f"Enqueued import job: {job.id}")

    return {
        "job_id": job.id,
        "status": "queued",
        "message": "Agent import started in background"
    }


async def get_import_status(
    job_id: str,
    job_queue: AsyncJobQueue = Depends(lambda: Depends(get_job_queue)),
) -> Dict[str, Any]:
    """
    GET /api/jobs/{job_id}

    Check status of a background job.
    """

    job_status = job_queue.get_job_status(job_id)

    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")

    return job_status


async def process_agent_csv_import(file_path: str, user_id: str) -> None:
    """Background task to import agents from CSV."""
    # TODO: Implement actual import logic
    logger.info(f"Processing import for user {user_id}: {file_path}")


# ============================================================================
# EXAMPLE: PERFORMANCE MONITORING
# ============================================================================

async def get_performance_dashboard(
    monitor: PerformanceMonitor = Depends(lambda: Depends(get_monitor)),
) -> Dict[str, Any]:
    """
    GET /api/performance/dashboard

    Get comprehensive performance report.
    """

    report = monitor.get_performance_report()

    return {
        "timestamp": datetime.utcnow().isoformat(),
        "health": report["health"],
        "top_metrics": report["top_metrics"],
        "bottlenecks": report["detected_bottlenecks"],
        "recent_alerts": report["recent_alerts"][:10],
        "recommendations": report["recommendations"],
    }


async def get_slow_queries(
    db_optimizer: DatabaseOptimizer = Depends(lambda: Depends(get_db_optimizer)),
    limit: int = 50,
) -> Dict[str, Any]:
    """
    GET /api/performance/slow-queries?limit=50

    Get top slow queries.
    """

    slow_queries = db_optimizer.get_slow_query_report(limit=limit)

    return {
        "count": len(slow_queries),
        "queries": slow_queries,
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# EXAMPLE: LOAD TESTING
# ============================================================================

async def run_load_test(
    concurrent_users: int = 100,
    duration_seconds: int = 60,
    load_tester: LoadTestRunner = Depends(lambda: Depends(get_load_tester)),
) -> Dict[str, Any]:
    """
    POST /api/testing/load-test

    Run a load test against the API.

    {
        "concurrent_users": 100,
        "duration_seconds": 60
    }
    """

    # Configuration
    config = LoadTestConfig(
        name=f"load_test_{datetime.utcnow().timestamp()}",
        target_function=simulate_api_request,
        concurrent_users=concurrent_users,
        requests_per_second=concurrent_users * 10,
        duration_seconds=duration_seconds,
        ramp_up_seconds=10,
        ramp_down_seconds=10,
    )

    # Request generator
    def request_gen():
        return {
            "endpoint": "/api/agents/search",
            "method": "POST",
            "params": {"query": "test"}
        }

    # Run test
    result = await load_tester.run_load_test(config, request_gen)

    return result.to_dict()


async def simulate_api_request(**kwargs) -> Dict[str, Any]:
    """Simulate an API request for load testing."""
    # In real scenario, make actual HTTP request
    await asyncio.sleep(0.05)  # Simulate 50ms response
    return {"status": "success"}


# ============================================================================
# DEPENDENCY INJECTION HELPERS
# ============================================================================

async def get_cache_layer() -> CacheLayer:
    """Get cache layer from app state."""
    # In real app: return request.app.state.performance["cache"]
    pass


async def get_db_optimizer() -> DatabaseOptimizer:
    """Get database optimizer from app state."""
    # In real app: return request.app.state.performance["db_optimizer"]
    pass


async def get_job_queue() -> AsyncJobQueue:
    """Get job queue from app state."""
    # In real app: return request.app.state.performance["job_queue"]
    pass


async def get_monitor() -> PerformanceMonitor:
    """Get performance monitor from app state."""
    # In real app: return request.app.state.performance["monitor"]
    pass


async def get_load_tester() -> LoadTestRunner:
    """Get load test runner from app state."""
    # In real app: return request.app.state.performance["load_tester"]
    pass


# ============================================================================
# EXAMPLE ROUTES
# ============================================================================

def setup_performance_routes(app: FastAPI) -> None:
    """Set up performance monitoring routes."""

    @app.get("/health/performance")
    async def health_check(
        monitor: PerformanceMonitor = Depends(get_monitor),
    ) -> Dict[str, Any]:
        """Health check including performance metrics."""
        health = monitor.get_system_health()
        return {
            "status": "ok" if health["status"] == "healthy" else "degraded",
            "performance": health,
        }

    @app.get("/api/performance/metrics")
    async def get_metrics(
        metric_name: str,
        limit: int = 100,
        monitor: PerformanceMonitor = Depends(get_monitor),
    ) -> Dict[str, Any]:
        """Get specific performance metric."""
        stats = monitor.get_metric_stats(metric_name)
        recent = monitor.get_recent_metrics(metric_name, limit)

        return {
            "metric": metric_name,
            "stats": stats,
            "recent": recent,
        }

    @app.get("/api/performance/cache-stats")
    async def get_cache_stats(
        cache: CacheLayer = Depends(get_cache_layer),
    ) -> Dict[str, Any]:
        """Get cache statistics."""
        return cache.get_stats()

    @app.get("/api/performance/queue-status")
    async def get_queue_status(
        job_queue: AsyncJobQueue = Depends(get_job_queue),
    ) -> Dict[str, Any]:
        """Get job queue status."""
        return {
            "queue": job_queue.get_queue_status(),
            "stats": job_queue.get_stats(),
        }

    @app.post("/api/testing/load-test")
    async def create_load_test(
        concurrent_users: int = 100,
        duration: int = 60,
    ) -> Dict[str, Any]:
        """Run load test."""
        return await run_load_test(concurrent_users, duration)


# ============================================================================
# MAIN APPLICATION SETUP
# ============================================================================

def create_app() -> FastAPI:
    """Create FastAPI application with performance stack."""

    app = FastAPI(title="Vendedor Automático API")

    # Initialize performance stack on startup
    @app.on_event("startup")
    async def startup():
        import redis
        # Initialize Redis client (or None for local cache only)
        try:
            redis_client = redis.asyncio.from_url("redis://localhost:6379")
        except Exception as e:
            logger.warning(f"Redis unavailable, using local cache: {e}")
            redis_client = None

        app.state.performance = setup_performance_stack(app, redis_client)
        await app.state.performance["job_queue"].start_workers()
        logger.info("Performance stack started")

    # Shutdown
    @app.on_event("shutdown")
    async def shutdown():
        if hasattr(app.state, "performance"):
            await app.state.performance["job_queue"].stop_workers()
            logger.info("Performance stack stopped")

    # Set up routes
    setup_performance_routes(app)

    return app


if __name__ == "__main__":
    import asyncio
    import uvicorn

    app = create_app()

    # Run with: uvicorn app.main:app --reload
    uvicorn.run(app, host="0.0.0.0", port=8000)
