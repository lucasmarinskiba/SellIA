"""Database Optimizer — Index strategy, query analysis, slow query log."""

import logging
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class IndexType(Enum):
    """Database index types."""
    B_TREE = "B-tree"
    HASH = "Hash"
    BTREE_FULL_TEXT = "Full-text"
    JSONB = "JSONB"
    BRIN = "BRIN"
    GIN = "GIN"
    GIST = "GIST"


class QueryPriority(Enum):
    """Query priority classification."""
    CRITICAL = "critical"  # <50ms required
    HIGH = "high"  # <200ms required
    NORMAL = "normal"  # <1000ms acceptable
    LOW = "low"  # batch/async operations


@dataclass
class SlowQuery:
    """Slow query log entry."""
    query_hash: str
    query: str
    execution_time_ms: float
    rows_scanned: int
    rows_returned: int
    database: str
    timestamp: datetime
    user_id: Optional[str] = None
    endpoint: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "query_hash": self.query_hash,
            "query": self.query[:500],  # Truncate for storage
            "execution_time_ms": round(self.execution_time_ms, 2),
            "rows_scanned": self.rows_scanned,
            "rows_returned": self.rows_returned,
            "database": self.database,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "endpoint": self.endpoint,
            "error": self.error,
        }


@dataclass
class IndexRecommendation:
    """Index recommendation for a table."""
    table: str
    columns: List[str]
    index_type: IndexType
    selectivity: float  # 0.0-1.0, higher is better
    estimated_improvement_percent: int
    priority: str  # Critical, High, Medium, Low
    creation_sql: str
    estimated_size_mb: float


class DatabaseOptimizer:
    """Optimize database performance through indexes, query analysis, and tuning."""

    # Query time thresholds (milliseconds)
    QUERY_THRESHOLDS = {
        QueryPriority.CRITICAL: 50,
        QueryPriority.HIGH: 200,
        QueryPriority.NORMAL: 1000,
        QueryPriority.LOW: 10000,
    }

    # Slow query log storage (in-memory, could be persisted to Redis)
    _slow_query_log: List[SlowQuery] = []
    _max_log_size = 10000

    def __init__(self):
        """Initialize database optimizer."""
        self.slow_queries: Dict[str, Dict[str, Any]] = {}
        self.index_stats: Dict[str, Dict[str, Any]] = {}
        self.query_cache_stats: Dict[str, Dict[str, Any]] = {}

    async def log_slow_query(
        self,
        query: str,
        execution_time_ms: float,
        rows_scanned: int,
        rows_returned: int,
        user_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Log a slow query execution."""
        import hashlib

        query_hash = hashlib.md5(query.encode()).hexdigest()[:8]

        slow_query = SlowQuery(
            query_hash=query_hash,
            query=query,
            execution_time_ms=execution_time_ms,
            rows_scanned=rows_scanned,
            rows_returned=rows_returned,
            database="postgres",
            timestamp=datetime.utcnow(),
            user_id=user_id,
            endpoint=endpoint,
            error=error,
        )

        # Add to in-memory log
        self._slow_query_log.append(slow_query)

        # Maintain max size
        if len(self._slow_query_log) > self._max_log_size:
            self._slow_query_log = self._slow_query_log[-self._max_log_size :]

        # Track by query hash
        if query_hash not in self.slow_queries:
            self.slow_queries[query_hash] = {
                "query": query[:500],
                "count": 0,
                "total_time_ms": 0.0,
                "avg_time_ms": 0.0,
                "max_time_ms": 0.0,
                "min_time_ms": float("inf"),
                "rows_scanned_total": 0,
                "first_seen": datetime.utcnow(),
                "last_seen": datetime.utcnow(),
            }

        stats = self.slow_queries[query_hash]
        stats["count"] += 1
        stats["total_time_ms"] += execution_time_ms
        stats["avg_time_ms"] = stats["total_time_ms"] / stats["count"]
        stats["max_time_ms"] = max(stats["max_time_ms"], execution_time_ms)
        stats["min_time_ms"] = min(stats["min_time_ms"], execution_time_ms)
        stats["rows_scanned_total"] += rows_scanned
        stats["last_seen"] = datetime.utcnow()

        # Log warning if exceeds threshold
        if execution_time_ms > self.QUERY_THRESHOLDS[QueryPriority.HIGH]:
            logger.warning(
                f"Slow query detected: {query_hash} took {execution_time_ms}ms, "
                f"scanned {rows_scanned} rows, returned {rows_returned}"
            )

    def get_slow_query_report(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get top slow queries by execution time."""
        sorted_queries = sorted(
            self.slow_queries.items(),
            key=lambda x: x[1]["max_time_ms"],
            reverse=True,
        )

        return [
            {
                "query_hash": qh,
                "query": stats["query"],
                "count": stats["count"],
                "avg_time_ms": round(stats["avg_time_ms"], 2),
                "max_time_ms": round(stats["max_time_ms"], 2),
                "min_time_ms": round(stats["min_time_ms"], 2),
                "total_time_ms": round(stats["total_time_ms"], 2),
                "rows_scanned_total": stats["rows_scanned_total"],
                "first_seen": stats["first_seen"].isoformat(),
                "last_seen": stats["last_seen"].isoformat(),
            }
            for qh, stats in sorted_queries[:limit]
        ]

    def get_recent_slow_queries(self, minutes: int = 5, limit: int = 100) -> List[Dict[str, Any]]:
        """Get slow queries from the last N minutes."""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        recent = [
            q for q in self._slow_query_log
            if q.timestamp > cutoff_time
        ]

        # Sort by execution time descending
        recent.sort(key=lambda x: x.execution_time_ms, reverse=True)

        return [q.to_dict() for q in recent[:limit]]

    def analyze_query_performance(
        self,
        query: str,
        execution_time_ms: float,
        rows_scanned: int,
        rows_returned: int,
    ) -> Dict[str, Any]:
        """Analyze a single query's performance."""

        # Calculate efficiency ratio
        if rows_returned > 0:
            efficiency = rows_returned / max(rows_scanned, 1)
        else:
            efficiency = 0.0

        # Determine priority and threshold
        if execution_time_ms < self.QUERY_THRESHOLDS[QueryPriority.CRITICAL]:
            status = "excellent"
            priority = QueryPriority.CRITICAL
        elif execution_time_ms < self.QUERY_THRESHOLDS[QueryPriority.HIGH]:
            status = "good"
            priority = QueryPriority.HIGH
        elif execution_time_ms < self.QUERY_THRESHOLDS[QueryPriority.NORMAL]:
            status = "acceptable"
            priority = QueryPriority.NORMAL
        else:
            status = "slow"
            priority = QueryPriority.LOW

        # Generate recommendations
        recommendations = []
        if rows_scanned > 10000 and efficiency < 0.1:
            recommendations.append("Add composite index on filter columns")
        if execution_time_ms > 1000:
            recommendations.append("Consider query rewrite or pagination")
        if "OR" in query and rows_scanned > 5000:
            recommendations.append("Use UNION instead of OR for better index usage")
        if "SELECT *" in query:
            recommendations.append("Select only needed columns to reduce I/O")

        return {
            "query": query[:200],
            "execution_time_ms": round(execution_time_ms, 2),
            "rows_scanned": rows_scanned,
            "rows_returned": rows_returned,
            "efficiency": round(efficiency, 3),
            "status": status,
            "priority": priority.value,
            "recommendations": recommendations,
        }

    def recommend_indexes(
        self,
        table: str,
        frequent_filters: List[str],
        estimated_row_count: int = 100000,
    ) -> List[IndexRecommendation]:
        """Recommend indexes for frequently filtered columns."""

        recommendations: List[IndexRecommendation] = []

        # Single column indexes
        for column in frequent_filters[:5]:  # Limit to top 5
            selectivity = 0.9 if len(frequent_filters) == 1 else 0.7

            rec = IndexRecommendation(
                table=table,
                columns=[column],
                index_type=IndexType.B_TREE,
                selectivity=selectivity,
                estimated_improvement_percent=50 if selectivity > 0.8 else 30,
                priority="High" if len(frequent_filters) == 1 else "Medium",
                creation_sql=f"CREATE INDEX idx_{table}_{column} ON {table}({column});",
                estimated_size_mb=round((estimated_row_count * 0.01) / 1024, 2),
            )
            recommendations.append(rec)

        # Composite index (if multiple frequent filters)
        if len(frequent_filters) > 1:
            columns_str = ", ".join(frequent_filters[:3])
            columns_list = frequent_filters[:3]

            rec = IndexRecommendation(
                table=table,
                columns=columns_list,
                index_type=IndexType.B_TREE,
                selectivity=0.95,
                estimated_improvement_percent=80,
                priority="Critical",
                creation_sql=f"CREATE INDEX idx_{table}_composite ON {table}({columns_str});",
                estimated_size_mb=round((estimated_row_count * 0.015) / 1024, 2),
            )
            recommendations.append(rec)

        return recommendations

    def estimate_query_plan(self, query: str) -> Dict[str, Any]:
        """Estimate query plan and cost."""

        # This is a simplified version; real implementation would use EXPLAIN ANALYZE

        join_count = query.lower().count("join")
        subquery_count = query.count("SELECT") - 1
        where_count = query.lower().count("where")

        estimated_cost = 100  # Base cost

        # Add cost for joins (expensive)
        estimated_cost += join_count * 50

        # Add cost for subqueries
        estimated_cost += subquery_count * 30

        # Reduce cost for indexes (represented by WHERE clauses)
        if where_count > 0:
            estimated_cost = max(estimated_cost - (where_count * 15), 10)

        return {
            "query": query[:200],
            "estimated_cost": estimated_cost,
            "join_count": join_count,
            "subquery_count": subquery_count,
            "where_conditions": where_count,
            "optimization_potential": "High" if estimated_cost > 200 else "Medium" if estimated_cost > 100 else "Low",
        }

    def suggest_materialized_view(
        self,
        query: str,
        expected_query_frequency: int = 100,  # Per minute
    ) -> Optional[Dict[str, Any]]:
        """Suggest creating a materialized view for expensive queries."""

        # If query is complex and frequent, suggest materialized view
        join_count = query.lower().count("join")
        subquery_count = query.count("SELECT") - 1

        if (join_count >= 2 or subquery_count >= 1) and expected_query_frequency > 50:
            view_name = "mv_optimized_" + str(hash(query))[:8]

            return {
                "recommendation": "Create materialized view",
                "view_name": view_name,
                "creation_sql": f"CREATE MATERIALIZED VIEW {view_name} AS\n{query};",
                "refresh_strategy": "Incremental (trigger on base table updates)",
                "refresh_interval_minutes": 5 if expected_query_frequency > 500 else 15,
                "expected_speedup_percent": 90,
                "storage_requirement_mb": "~100-500 (depends on data)",
            }

        return None

    async def analyze_table_stats(
        self,
        session: AsyncSession,
        table_name: str,
    ) -> Dict[str, Any]:
        """Analyze table statistics."""

        try:
            # Count rows
            row_count_query = text(f"SELECT COUNT(*) as cnt FROM {table_name}")
            result = await session.execute(row_count_query)
            row_count = result.scalar() or 0

            # Get table size
            size_query = text(
                f"SELECT pg_total_relation_size('{table_name}'::regclass) / 1024 / 1024 as size_mb"
            )
            result = await session.execute(size_query)
            size_mb = result.scalar() or 0

            return {
                "table": table_name,
                "row_count": row_count,
                "size_mb": round(size_mb, 2),
                "avg_row_size_bytes": round((size_mb * 1024 * 1024 / max(row_count, 1)), 2),
                "last_analyzed": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Error analyzing table stats for {table_name}: {e}")
            return {
                "table": table_name,
                "error": str(e),
            }

    def get_index_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all tracked indexes."""
        return self.index_stats

    def clear_slow_query_log(self) -> int:
        """Clear slow query log and return number of entries cleared."""
        count = len(self._slow_query_log)
        self._slow_query_log.clear()
        self.slow_queries.clear()
        return count
