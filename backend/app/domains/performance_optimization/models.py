"""Phase 5: Performance Optimization - Query, Cache, Index Strategy."""
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Float, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.core.database import Base


class PerformanceMetrics(Base):
    __tablename__ = "performance_metrics"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Request metrics
    total_requests = Column(Integer, default=0)
    total_errors = Column(Integer, default=0)
    error_rate = Column(Float, default=0)  # 0-1

    # Latency metrics (milliseconds)
    avg_response_time_ms = Column(Float, default=0)
    p50_latency_ms = Column(Float, default=0)
    p95_latency_ms = Column(Float, default=0)
    p99_latency_ms = Column(Float, default=0)

    # Throughput
    requests_per_second = Column(Float, default=0)
    successful_requests_per_second = Column(Float, default=0)

    # Database metrics
    db_connection_pool_utilization = Column(Float, default=0)  # 0-1
    db_active_connections = Column(Integer, default=0)
    db_avg_query_time_ms = Column(Float, default=0)
    slow_queries_count = Column(Integer, default=0)  # queries > 1s

    # Cache metrics
    cache_hit_rate = Column(Float, default=0)  # 0-1
    cache_size_mb = Column(Float, default=0)
    cache_evictions = Column(Integer, default=0)

    # Memory & CPU
    memory_usage_mb = Column(Float, default=0)
    cpu_usage_percent = Column(Float, default=0)

    # Overall health (0-100)
    performance_score = Column(Integer, default=100)

    metric_period = Column(String(20), default="last_hour")  # last_hour, last_day, last_week
    measured_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))


class SlowQuery(Base):
    __tablename__ = "slow_queries"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Query details
    query_signature = Column(String(255), nullable=False)  # parameterized query
    query_text = Column(Text, nullable=True)
    execution_count = Column(Integer, default=1)

    # Performance
    avg_execution_time_ms = Column(Float, default=0)
    max_execution_time_ms = Column(Float, default=0)
    min_execution_time_ms = Column(Float, default=0)
    total_execution_time_ms = Column(Float, default=0)

    # Resource usage
    avg_rows_affected = Column(Integer, default=0)
    avg_rows_examined = Column(Integer, default=0)  # for diagnosis

    # Optimization
    optimization_status = Column(String(20), default="unoptimized")  # "unoptimized", "indexed", "refactored", "cached"
    recommended_optimization = Column(Text, nullable=True)
    index_recommendation = Column(String(255), nullable=True)  # e.g., "CREATE INDEX idx_user_email ON users(email)"
    optimization_impact = Column(Float, default=0)  # estimated % improvement

    # Urgency (0-100)
    optimization_urgency = Column(Integer, default=50)

    first_seen_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    last_seen_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))


class IndexRecommendation(Base):
    __tablename__ = "index_recommendations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Index definition
    table_name = Column(String(100), nullable=False)
    column_names = Column(JSONB, default=list)  # ["email", "created_at"]
    index_type = Column(String(20), default="btree")  # "btree", "hash", "gin", "gist"

    # Impact analysis
    estimated_queries_improved = Column(Integer, default=0)
    estimated_improvement_percent = Column(Float, default=0)  # 0-100

    # Query patterns
    affected_query_patterns = Column(JSONB, default=list)
    slow_query_ids = Column(JSONB, default=list)

    # Status
    status = Column(String(20), default="recommended")  # "recommended", "implemented", "rejected"
    implementation_priority = Column(Integer, default=50)  # 0-100

    # Size impact
    estimated_index_size_mb = Column(Float, default=0)
    maintenance_cost = Column(String(20), default="low")  # "low", "medium", "high"

    recommended_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    implemented_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))


class CacheStrategy(Base):
    __tablename__ = "cache_strategies"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Cache config
    cache_type = Column(String(50), default="redis")  # "redis", "memcached", "in_memory"
    ttl_seconds = Column(Integer, default=3600)  # time-to-live
    max_size_mb = Column(Float, default=256)

    # What to cache
    cache_patterns = Column(JSONB, default=list)  # ["user_*", "business_*", "product_*"]
    excluded_patterns = Column(JSONB, default=list)  # patterns to NOT cache

    # Performance
    hit_rate = Column(Float, default=0)  # 0-1
    miss_rate = Column(Float, default=0)  # 0-1
    eviction_rate = Column(Float, default=0)

    # Impact
    latency_improvement_percent = Column(Float, default=0)  # % reduction in response time
    cpu_reduction_percent = Column(Float, default=0)
    db_load_reduction_percent = Column(Float, default=0)

    # Freshness (stale-while-revalidate)
    stale_cache_ttl_seconds = Column(Integer, default=60)
    revalidation_interval_seconds = Column(Integer, default=3600)

    status = Column(String(20), default="proposed")  # "proposed", "active", "disabled"

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))


class QueryOptimization(Base):
    __tablename__ = "query_optimizations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False, index=True)

    # Problem
    problem_type = Column(String(50), nullable=False)  # "n_plus_one", "missing_index", "subquery_inefficient", "join_redundant"
    affected_query = Column(Text, nullable=True)
    problem_description = Column(Text, nullable=True)

    # Solution
    solution = Column(Text, nullable=False)
    solution_type = Column(String(50), nullable=False)  # "index", "query_refactor", "caching", "denormalization"

    # Impact
    current_execution_time_ms = Column(Float, default=0)
    estimated_optimized_time_ms = Column(Float, default=0)
    improvement_percent = Column(Float, default=0)  # (current - estimated) / current * 100

    # Status
    status = Column(String(20), default="identified")  # "identified", "proposed", "implemented", "verified"
    implementation_complexity = Column(String(20), default="medium")  # "low", "medium", "high"

    # Verification
    performance_verified = Column(Boolean, default=False)
    verified_improvement_percent = Column(Float, nullable=True)

    identified_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    implemented_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))
