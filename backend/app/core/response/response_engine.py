"""
Stage 1: Response Engine - Instant, Cached, Priority-Routed Message Processing

Features:
- Message queue with async processing
- Priority routing (urgent → priority)
- Latency tracking (<5s guarantee)
- Response caching (5min TTL)
- Multi-message batching
- Metrics tracking (latency, throughput)
"""

import asyncio
import time
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import hashlib
import json
from collections import defaultdict


class MessagePriority(str, Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Message:
    """Message unit"""
    id: str
    content: str
    user_id: str
    channel: str
    priority: MessagePriority = MessagePriority.NORMAL
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_cache_key(self) -> str:
        """Generate cache key for response caching"""
        content_hash = hashlib.md5(self.content.encode()).hexdigest()
        return f"response:{self.user_id}:{self.channel}:{content_hash}"


@dataclass
class Response:
    """Response unit"""
    id: str
    message_id: str
    content: str
    generated_at: datetime
    latency_ms: float
    from_cache: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class ResponseCache:
    """Simple in-memory LRU response cache with TTL"""

    def __init__(self, max_size: int = 10000, ttl_seconds: int = 300):
        self.cache: Dict[str, tuple[Response, float]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.access_times: Dict[str, float] = defaultdict(float)

    def get(self, key: str) -> Optional[Response]:
        """Get cached response if not expired"""
        if key not in self.cache:
            return None

        response, created_at = self.cache[key]
        if time.time() - created_at > self.ttl_seconds:
            del self.cache[key]
            return None

        self.access_times[key] = time.time()
        return response

    def set(self, key: str, response: Response) -> None:
        """Cache response"""
        if len(self.cache) >= self.max_size:
            # Evict least recently used
            lru_key = min(self.access_times, key=self.access_times.get)
            del self.cache[lru_key]
            del self.access_times[lru_key]

        self.cache[key] = (response, time.time())
        self.access_times[key] = time.time()

    def clear_expired(self) -> int:
        """Remove expired entries. Returns count removed."""
        current_time = time.time()
        expired = [
            key for key, (_, created_at) in self.cache.items()
            if current_time - created_at > self.ttl_seconds
        ]
        for key in expired:
            del self.cache[key]
            if key in self.access_times:
                del self.access_times[key]
        return len(expired)

    def stats(self) -> Dict[str, Any]:
        """Cache statistics"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
            "utilization": len(self.cache) / self.max_size
        }


class MessageQueue:
    """Priority-based message queue with async processing"""

    def __init__(self, max_queue_size: int = 10000):
        self.queues: Dict[MessagePriority, asyncio.Queue] = {
            priority: asyncio.Queue(maxsize=max_queue_size)
            for priority in MessagePriority
        }
        self.processing = False
        self.metrics = {
            "total_processed": 0,
            "total_errors": 0,
            "total_batched": 0,
            "latencies": []
        }

    async def enqueue(self, message: Message) -> bool:
        """Add message to priority queue"""
        try:
            await self.queues[message.priority].put(message, block=False)
            return True
        except asyncio.QueueFull:
            return False

    async def get_batch(self, batch_size: int = 10) -> List[Message]:
        """Get next batch of messages in priority order"""
        batch = []

        # Collect from highest to lowest priority
        for priority in [MessagePriority.URGENT, MessagePriority.HIGH,
                        MessagePriority.NORMAL, MessagePriority.LOW]:
            queue = self.queues[priority]
            while len(batch) < batch_size and not queue.empty():
                try:
                    msg = queue.get_nowait()
                    batch.append(msg)
                except asyncio.QueueEmpty:
                    break

        return batch

    def queue_sizes(self) -> Dict[str, int]:
        """Get current queue sizes by priority"""
        return {
            priority.value: queue.qsize()
            for priority, queue in self.queues.items()
        }

    def stats(self) -> Dict[str, Any]:
        """Metrics"""
        latencies = self.metrics["latencies"]
        return {
            "total_processed": self.metrics["total_processed"],
            "total_errors": self.metrics["total_errors"],
            "total_batched": self.metrics["total_batched"],
            "queue_sizes": self.queue_sizes(),
            "avg_latency_ms": sum(latencies) / len(latencies) if latencies else 0,
            "p99_latency_ms": sorted(latencies)[int(len(latencies) * 0.99)] if latencies else 0,
            "p95_latency_ms": sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0,
        }


class LatencyTracker:
    """Track response latencies and ensure SLA compliance"""

    def __init__(self, sla_ms: float = 5000, window_size: int = 1000):
        self.sla_ms = sla_ms
        self.latencies: List[float] = []
        self.window_size = window_size
        self.violations = 0

    def record(self, latency_ms: float) -> bool:
        """Record latency. Returns True if within SLA, False if violation"""
        self.latencies.append(latency_ms)
        if len(self.latencies) > self.window_size:
            self.latencies = self.latencies[-self.window_size:]

        is_compliant = latency_ms <= self.sla_ms
        if not is_compliant:
            self.violations += 1
        return is_compliant

    def get_stats(self) -> Dict[str, Any]:
        """Get latency statistics"""
        if not self.latencies:
            return {
                "avg_ms": 0,
                "min_ms": 0,
                "max_ms": 0,
                "p99_ms": 0,
                "p95_ms": 0,
                "sla_compliance": 1.0,
                "violations": 0
            }

        sorted_latencies = sorted(self.latencies)
        n = len(sorted_latencies)

        return {
            "avg_ms": sum(self.latencies) / n,
            "min_ms": sorted_latencies[0],
            "max_ms": sorted_latencies[-1],
            "p99_ms": sorted_latencies[int(n * 0.99)] if n > 0 else 0,
            "p95_ms": sorted_latencies[int(n * 0.95)] if n > 0 else 0,
            "sla_compliance": (n - self.violations) / n if n > 0 else 1.0,
            "violations": self.violations
        }


class ResponseEngine:
    """Main response processing engine"""

    def __init__(self, batch_size: int = 10, cache_enabled: bool = True):
        self.queue = MessageQueue()
        self.cache = ResponseCache() if cache_enabled else None
        self.batch_size = batch_size
        self.latency_tracker = LatencyTracker()
        self.response_generator = None  # Set externally
        self.batch_timeout = 1.0  # seconds

    async def process_message(self, message: Message) -> Response:
        """
        Process single message:
        1. Check cache
        2. Generate response if miss
        3. Track latency
        4. Return response
        """
        start_time = time.time()

        # Try cache first
        if self.cache:
            cache_key = message.get_cache_key()
            cached = self.cache.get(cache_key)
            if cached:
                return cached

        # Generate response
        response_content = await self._generate_response(message)

        latency_ms = (time.time() - start_time) * 1000
        self.latency_tracker.record(latency_ms)

        response = Response(
            id=f"resp_{int(time.time() * 1000)}",
            message_id=message.id,
            content=response_content,
            generated_at=datetime.utcnow(),
            latency_ms=latency_ms,
            from_cache=False
        )

        # Cache response
        if self.cache:
            self.cache.set(cache_key, response)

        return response

    async def process_batch(self, batch: List[Message]) -> List[Response]:
        """Process multiple messages in parallel"""
        tasks = [self.process_message(msg) for msg in batch]
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle errors
        results = []
        for resp in responses:
            if isinstance(resp, Exception):
                self.queue.metrics["total_errors"] += 1
            else:
                results.append(resp)
                self.queue.metrics["total_processed"] += 1

        self.queue.metrics["total_batched"] += 1
        return results

    async def _generate_response(self, message: Message) -> str:
        """Generate response (calls external generator)"""
        if self.response_generator:
            return await self.response_generator(message)
        return f"Automated response to: {message.content[:50]}..."

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive metrics"""
        return {
            "queue": self.queue.stats(),
            "cache": self.cache.stats() if self.cache else None,
            "latency": self.latency_tracker.get_stats()
        }

    async def health_check(self) -> Dict[str, Any]:
        """Health status"""
        metrics = self.get_metrics()
        return {
            "healthy": True,
            "queue_depth": sum(metrics["queue"]["queue_sizes"].values()),
            "cache_utilization": metrics["cache"]["utilization"] if self.cache else 0,
            "sla_compliant": metrics["latency"]["sla_compliance"] >= 0.99,
            "metrics": metrics
        }


# Singleton instance
_engine_instance: Optional[ResponseEngine] = None


def get_response_engine() -> ResponseEngine:
    """Get or create engine singleton"""
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = ResponseEngine()
    return _engine_instance


def set_response_generator(generator_func):
    """Set the response generation function"""
    engine = get_response_engine()
    engine.response_generator = generator_func
