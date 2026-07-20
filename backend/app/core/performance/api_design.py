"""API Design — Optimization, pagination, rate limiting."""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class APIDesign:
    """Optimize API design."""

    @staticmethod
    def cursor_based_pagination(
        total_items: int,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """Cursor-based pagination (more efficient than offset)."""

        return {
            "strategy": "Cursor-based",
            "page_size": page_size,
            "cursor_field": "id",
            "total_pages": (total_items + page_size - 1) // page_size,
            "advantages": ["Fast", "Handles concurrent changes", "No offset computation"],
        }

    @staticmethod
    def rate_limiting_strategy() -> Dict[str, Any]:
        """Rate limiting configuration."""

        return {
            "global_limit": "10000 req/min",
            "per_user_limit": "1000 req/min",
            "per_api_key_limit": "10000 req/min",
            "burst_allowance": "10x limit for 10 seconds",
            "algorithm": "Token bucket",
            "response_header": "X-RateLimit-Remaining",
        }

    @staticmethod
    def response_compression() -> Dict[str, Any]:
        """Response compression settings."""

        return {
            "algorithms": ["gzip", "brotli"],
            "min_size": 1000,  # bytes
            "compression_level": 6,
            "expected_ratio": "60-80% reduction",
        }

    @staticmethod
    def cache_headers_strategy() -> Dict[str, Any]:
        """HTTP caching headers."""

        return {
            "static_content": "Cache-Control: public, max-age=31536000",
            "api_response": "Cache-Control: private, max-age=300",
            "user_data": "Cache-Control: private, no-cache",
            "etag_support": True,
            "vary_headers": ["Accept-Encoding", "Authorization"],
        }

    @staticmethod
    def rest_vs_graphql() -> Dict[str, Any]:
        """Comparison and hybrid approach."""

        return {
            "rest_endpoints": ["GET /users", "POST /orders", "PATCH /users/{id}"],
            "graphql_endpoint": "POST /graphql",
            "strategy": "REST for simple queries, GraphQL for complex joins",
            "benefits": ["Over-fetching reduction", "Under-fetching reduction"],
        }
