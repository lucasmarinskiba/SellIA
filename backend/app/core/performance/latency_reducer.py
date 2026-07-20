"""Latency Reducer — Async/await, batching, caching, compression."""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class LatencyReducer:
    """Reduce request latency."""

    @staticmethod
    def analyze_latency_breakdown(
        request_latency_ms: float,
        db_time_ms: float,
        api_time_ms: float,
        processing_time_ms: float,
    ) -> Dict[str, Any]:
        """Analyze where latency comes from."""

        total = db_time_ms + api_time_ms + processing_time_ms
        breakdown = {
            "total_ms": request_latency_ms,
            "db_percentage": round(db_time_ms / total * 100, 1) if total > 0 else 0,
            "api_percentage": round(api_time_ms / total * 100, 1) if total > 0 else 0,
            "processing_percentage": round(processing_time_ms / total * 100, 1) if total > 0 else 0,
            "bottleneck": max(
                [("database", db_time_ms), ("external_api", api_time_ms), ("processing", processing_time_ms)],
                key=lambda x: x[1]
            )[0],
        }

        return breakdown

    @staticmethod
    def recommend_async_operations(
        operations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Identify operations that should be async."""

        recommendations = []

        for op in operations:
            if op.get("blocking", False):
                recommendations.append({
                    "operation": op.get("name"),
                    "expected_speedup": "Remove from critical path",
                    "async_method": "Background job/queue",
                })

        return {
            "async_candidates": recommendations,
            "total_latency_savings_ms": sum(op.get("duration_ms", 0) for op in recommendations),
        }

    @staticmethod
    def compression_strategy() -> Dict[str, Any]:
        """Recommend compression settings."""

        return {
            "gzip_compression": {"enabled": True, "level": 6},
            "brotli_compression": {"enabled": True, "level": 4},
            "min_size_to_compress": 1000,  # bytes
            "expected_size_reduction": "60-80%",
        }

    @staticmethod
    def caching_layers() -> List[Dict[str, Any]]:
        """Multi-layer caching strategy."""

        return [
            {
                "layer": 1,
                "type": "HTTP caching (browser)",
                "strategy": "Set Cache-Control headers",
                "ttl": "1 day",
            },
            {
                "layer": 2,
                "type": "Redis (application)",
                "strategy": "Cache hot queries",
                "ttl": "5 minutes",
            },
            {
                "layer": 3,
                "type": "Database query cache",
                "strategy": "Cache query results",
                "ttl": "1 minute",
            },
            {
                "layer": 4,
                "type": "CDN (edge)",
                "strategy": "Cache static content",
                "ttl": "1 week",
            },
        ]
