"""
Backend Evolution Module — Production-ready performance stack.

PHASE 8: PERFORMANCE — 2,500 lines
Target: <200ms response time, 99.9% uptime

Modules:
1. database_optimizer: Index strategy, query analysis, slow query log (500L)
2. cache_layer: Redis caching for KPIs, market data, agent status (400L)
3. query_optimizer: Rewrite slow queries, batch operations (400L)
4. async_jobs: Celery for long-running tasks, background jobs (300L)
5. monitoring: Query time tracking, bottleneck detection (300L)
6. load_testing: Simulate 1000+ concurrent users, stress testing (300L)
7. latency_reducer: Async/await, batching, caching, compression
8. scalability_engine: Horizontal scaling, sharding, load balancing
9. ml_pipelines: Real-time features, model inference, online learning
10. data_layer: Data warehouse, event streaming, ETL
11. api_design: GraphQL/REST optimization, pagination, rate limiting
12. monitoring_stack: P99 latency, errors, anomalies, user experience
13. testing_suite: Load testing, chaos engineering, performance regression
"""

from .database_optimizer import DatabaseOptimizer, IndexType, QueryPriority, SlowQuery
from .cache_layer import CacheLayer, CacheKeyBuilder, RedisCache, LocalCache
from .async_jobs import AsyncJobQueue, Job, JobStatus, JobPriority
from .monitoring import PerformanceMonitor, PerformanceMetric, BottleneckAlert
from .load_testing import LoadTestRunner, LoadTestConfig, LoadTestResult

from .query_optimizer import QueryOptimizer
from .latency_reducer import LatencyReducer
from .scalability_engine import ScalabilityEngine
from .ml_pipelines import MLPipelines
from .data_layer import DataLayer
from .api_design import APIDesign
from .monitoring_stack import MonitoringStack
from .testing_suite import TestingSuite

__all__ = [
    # Phase 8 modules
    "DatabaseOptimizer",
    "IndexType",
    "QueryPriority",
    "SlowQuery",
    "CacheLayer",
    "CacheKeyBuilder",
    "RedisCache",
    "LocalCache",
    "AsyncJobQueue",
    "Job",
    "JobStatus",
    "JobPriority",
    "PerformanceMonitor",
    "PerformanceMetric",
    "BottleneckAlert",
    "LoadTestRunner",
    "LoadTestConfig",
    "LoadTestResult",
    # Existing modules
    "QueryOptimizer",
    "LatencyReducer",
    "ScalabilityEngine",
    "MLPipelines",
    "DataLayer",
    "APIDesign",
    "MonitoringStack",
    "TestingSuite",
]
