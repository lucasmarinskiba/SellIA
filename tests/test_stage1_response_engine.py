"""
Stage 1 Tests: Response Engine, Message Queue, Caching, Latency Tracking

Test Coverage:
- Message queue priority routing
- Response caching
- Latency tracking and SLA compliance
- Batch processing
- Cache eviction (LRU)
"""

import pytest
import asyncio
import time
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.core.response.response_engine import (
    ResponseEngine, Message, MessagePriority, MessageQueue,
    ResponseCache, LatencyTracker, Response, get_response_engine
)


class TestMessage:
    """Test Message data structure"""

    def test_message_creation(self):
        msg = Message(
            id="msg_1",
            content="Hello",
            user_id="user_1",
            channel="whatsapp",
            priority=MessagePriority.HIGH
        )
        assert msg.id == "msg_1"
        assert msg.content == "Hello"
        assert msg.priority == MessagePriority.HIGH

    def test_message_cache_key_generation(self):
        msg1 = Message(
            id="msg_1",
            content="Hello World",
            user_id="user_1",
            channel="whatsapp"
        )
        msg2 = Message(
            id="msg_2",
            content="Hello World",
            user_id="user_1",
            channel="whatsapp"
        )
        # Same content should generate same cache key
        assert msg1.get_cache_key() == msg2.get_cache_key()

        msg3 = Message(
            id="msg_3",
            content="Different",
            user_id="user_1",
            channel="whatsapp"
        )
        # Different content should generate different cache key
        assert msg1.get_cache_key() != msg3.get_cache_key()

    def test_message_different_users_different_keys(self):
        msg1 = Message(
            id="msg_1",
            content="Hello",
            user_id="user_1",
            channel="whatsapp"
        )
        msg2 = Message(
            id="msg_2",
            content="Hello",
            user_id="user_2",
            channel="whatsapp"
        )
        # Different users should generate different cache keys
        assert msg1.get_cache_key() != msg2.get_cache_key()


class TestResponseCache:
    """Test response caching with TTL and LRU eviction"""

    def test_cache_set_and_get(self):
        cache = ResponseCache(max_size=100)
        response = Response(
            id="resp_1",
            message_id="msg_1",
            content="Hello",
            generated_at=datetime.utcnow(),
            latency_ms=100.0
        )

        cache.set("key1", response)
        cached = cache.get("key1")

        assert cached is not None
        assert cached.id == "resp_1"

    def test_cache_miss(self):
        cache = ResponseCache()
        cached = cache.get("nonexistent")
        assert cached is None

    def test_cache_ttl_expiration(self):
        cache = ResponseCache(ttl_seconds=1)
        response = Response(
            id="resp_1",
            message_id="msg_1",
            content="Hello",
            generated_at=datetime.utcnow(),
            latency_ms=100.0
        )

        cache.set("key1", response)
        assert cache.get("key1") is not None

        # Wait for expiration
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_cache_lru_eviction(self):
        cache = ResponseCache(max_size=3, ttl_seconds=3600)
        responses = [
            Response(f"resp_{i}", f"msg_{i}", f"Content {i}",
                    datetime.utcnow(), 10.0)
            for i in range(5)
        ]

        # Add 3 items
        cache.set("key1", responses[0])
        cache.set("key2", responses[1])
        cache.set("key3", responses[2])
        assert cache.stats()["size"] == 3

        # Add 4th item - should evict LRU
        cache.set("key4", responses[3])
        assert cache.stats()["size"] == 3

        # key1 should be evicted
        assert cache.get("key1") is None
        assert cache.get("key4") is not None

    def test_cache_stats(self):
        cache = ResponseCache(max_size=100, ttl_seconds=300)
        stats = cache.stats()

        assert stats["size"] == 0
        assert stats["max_size"] == 100
        assert stats["ttl_seconds"] == 300
        assert stats["utilization"] == 0.0

    def test_cache_clear_expired(self):
        cache = ResponseCache(ttl_seconds=1)
        response = Response(
            id="resp_1",
            message_id="msg_1",
            content="Hello",
            generated_at=datetime.utcnow(),
            latency_ms=100.0
        )

        cache.set("key1", response)
        cache.set("key2", response)

        time.sleep(1.1)
        cleared = cache.clear_expired()

        assert cleared == 2
        assert cache.stats()["size"] == 0


class TestMessageQueue:
    """Test priority-based message queue"""

    @pytest.mark.asyncio
    async def test_message_enqueue(self):
        queue = MessageQueue()
        msg = Message(
            id="msg_1",
            content="Hello",
            user_id="user_1",
            channel="whatsapp"
        )

        result = await queue.enqueue(msg)
        assert result is True
        assert queue.queue_sizes()[MessagePriority.NORMAL.value] == 1

    @pytest.mark.asyncio
    async def test_priority_routing(self):
        queue = MessageQueue()
        messages = [
            Message("msg_1", "Low", "user_1", "whatsapp", MessagePriority.LOW),
            Message("msg_2", "Urgent", "user_1", "whatsapp", MessagePriority.URGENT),
            Message("msg_3", "High", "user_1", "whatsapp", MessagePriority.HIGH),
            Message("msg_4", "Normal", "user_1", "whatsapp", MessagePriority.NORMAL),
        ]

        for msg in messages:
            await queue.enqueue(msg)

        # Get batch should prioritize urgent > high > normal > low
        batch = await queue.get_batch(batch_size=4)
        assert batch[0].priority == MessagePriority.URGENT
        assert batch[1].priority == MessagePriority.HIGH
        assert batch[2].priority == MessagePriority.NORMAL
        assert batch[3].priority == MessagePriority.LOW

    @pytest.mark.asyncio
    async def test_queue_overflow(self):
        queue = MessageQueue(max_queue_size=2)
        msg = Message("msg_1", "Content", "user_1", "whatsapp")

        # Fill queue
        assert await queue.enqueue(msg) is True
        assert await queue.enqueue(msg) is True

        # Should reject third message
        assert await queue.enqueue(msg) is False

    @pytest.mark.asyncio
    async def test_queue_batch_collection(self):
        queue = MessageQueue()

        # Add messages of different priorities
        for i in range(3):
            msg = Message(f"msg_{i}", f"Content {i}", "user_1", "whatsapp",
                         MessagePriority.NORMAL)
            await queue.enqueue(msg)

        msg_high = Message("msg_h", "High", "user_1", "whatsapp",
                          MessagePriority.HIGH)
        await queue.enqueue(msg_high)

        batch = await queue.get_batch(batch_size=2)
        assert len(batch) == 2
        assert batch[0].priority == MessagePriority.HIGH

    def test_queue_stats(self):
        queue = MessageQueue()
        stats = queue.stats()

        assert "queue_sizes" in stats
        assert "total_processed" in stats
        assert stats["total_processed"] == 0


class TestLatencyTracker:
    """Test latency tracking and SLA compliance"""

    def test_latency_recording(self):
        tracker = LatencyTracker(sla_ms=5000)

        # Record compliant latency
        is_compliant = tracker.record(1000.0)
        assert is_compliant is True

        # Record SLA violation
        is_compliant = tracker.record(6000.0)
        assert is_compliant is False
        assert tracker.violations == 1

    def test_sla_compliance_percentage(self):
        tracker = LatencyTracker(sla_ms=5000)

        # Record 10 measurements: 9 compliant, 1 violation
        for i in range(9):
            tracker.record(1000.0 + i * 100)
        tracker.record(6000.0)

        stats = tracker.get_stats()
        assert stats["sla_compliance"] == 0.9
        assert stats["violations"] == 1

    def test_latency_percentiles(self):
        tracker = LatencyTracker()

        # Record measurements
        for i in range(100):
            tracker.record(i * 10.0)

        stats = tracker.get_stats()
        assert stats["min_ms"] == 0
        assert stats["max_ms"] == 990.0
        assert stats["p95_ms"] > 0
        assert stats["p99_ms"] > stats["p95_ms"]

    def test_latency_stats_empty(self):
        tracker = LatencyTracker()
        stats = tracker.get_stats()

        assert stats["avg_ms"] == 0
        assert stats["sla_compliance"] == 1.0
        assert stats["violations"] == 0


class TestResponseEngine:
    """Test main response engine"""

    @pytest.mark.asyncio
    async def test_engine_creation(self):
        engine = ResponseEngine()
        assert engine is not None
        assert engine.cache is not None
        assert engine.queue is not None

    @pytest.mark.asyncio
    async def test_engine_metrics(self):
        engine = ResponseEngine()
        metrics = engine.get_metrics()

        assert "queue" in metrics
        assert "cache" in metrics
        assert "latency" in metrics

    @pytest.mark.asyncio
    async def test_engine_health_check(self):
        engine = ResponseEngine()
        health = await engine.health_check()

        assert health["healthy"] is True
        assert "metrics" in health

    @pytest.mark.asyncio
    async def test_message_processing_latency(self):
        engine = ResponseEngine()

        async def mock_generator(msg):
            await asyncio.sleep(0.01)  # Simulate 10ms processing
            return "Response"

        engine.response_generator = mock_generator

        msg = Message("msg_1", "Hello", "user_1", "whatsapp")
        response = await engine.process_message(msg)

        assert response.latency_ms >= 10.0
        assert response.from_cache is False

    @pytest.mark.asyncio
    async def test_response_caching(self):
        engine = ResponseEngine(cache_enabled=True)

        async def mock_generator(msg):
            return f"Response to {msg.content}"

        engine.response_generator = mock_generator

        msg = Message("msg_1", "Hello", "user_1", "whatsapp")

        # First call - generates
        response1 = await engine.process_message(msg)
        assert response1.from_cache is False

        # Second call - from cache
        response2 = await engine.process_message(msg)
        assert response2.from_cache is True
        assert response1.content == response2.content

    @pytest.mark.asyncio
    async def test_batch_processing(self):
        engine = ResponseEngine()

        async def mock_generator(msg):
            await asyncio.sleep(0.001)
            return f"Response"

        engine.response_generator = mock_generator

        batch = [
            Message(f"msg_{i}", f"Content {i}", "user_1", "whatsapp")
            for i in range(5)
        ]

        responses = await engine.process_batch(batch)
        assert len(responses) == 5
        assert all(isinstance(r, Response) for r in responses)

    @pytest.mark.asyncio
    async def test_batch_error_handling(self):
        engine = ResponseEngine()

        async def failing_generator(msg):
            if "error" in msg.content:
                raise Exception("Generation failed")
            return "Response"

        engine.response_generator = failing_generator

        batch = [
            Message("msg_1", "Normal", "user_1", "whatsapp"),
            Message("msg_2", "error", "user_1", "whatsapp"),
            Message("msg_3", "Normal", "user_1", "whatsapp"),
        ]

        responses = await engine.process_batch(batch)
        assert len(responses) == 2  # Only non-error responses
        assert engine.queue.metrics["total_errors"] == 1

    @pytest.mark.asyncio
    async def test_singleton_instance(self):
        engine1 = get_response_engine()
        engine2 = get_response_engine()
        assert engine1 is engine2


class TestIntegration:
    """Integration tests for Stage 1"""

    @pytest.mark.asyncio
    async def test_full_response_pipeline(self):
        """Test complete pipeline: message -> queue -> cache -> latency tracking"""
        engine = ResponseEngine()

        async def mock_generator(msg):
            await asyncio.sleep(0.001)
            return f"Response to: {msg.content}"

        engine.response_generator = mock_generator

        # Process message
        msg = Message("msg_1", "Hello World", "user_123", "whatsapp",
                     priority=MessagePriority.HIGH)
        response = await engine.process_message(msg)

        # Verify response
        assert response.message_id == "msg_1"
        assert "Hello World" in response.content
        assert response.latency_ms > 0
        assert response.from_cache is False

        # Check metrics
        metrics = engine.get_metrics()
        assert metrics["latency"]["sla_compliance"] >= 0.99
        assert metrics["cache"]["utilization"] > 0

    @pytest.mark.asyncio
    async def test_multi_message_processing(self):
        """Test processing multiple messages with priority"""
        engine = ResponseEngine()

        call_order = []

        async def mock_generator(msg):
            call_order.append(msg.id)
            return "Response"

        engine.response_generator = mock_generator

        # Create batch with mixed priorities
        batch = [
            Message("msg_1", "Low", "user_1", "whatsapp", MessagePriority.LOW),
            Message("msg_2", "Urgent", "user_1", "whatsapp", MessagePriority.URGENT),
            Message("msg_3", "High", "user_1", "whatsapp", MessagePriority.HIGH),
        ]

        # Enqueue all
        for msg in batch:
            await engine.queue.enqueue(msg)

        # Process batch
        messages = await engine.queue.get_batch(batch_size=3)
        responses = await engine.process_batch(messages)

        assert len(responses) == 3
        # First message processed should be urgent
        assert call_order[0] == "msg_2"

    @pytest.mark.asyncio
    async def test_latency_sla_guarantee(self):
        """Verify <5s latency guarantee"""
        engine = ResponseEngine()

        async def mock_generator(msg):
            await asyncio.sleep(0.001)  # 1ms
            return "Response"

        engine.response_generator = mock_generator

        # Process 100 messages
        for i in range(100):
            msg = Message(f"msg_{i}", f"Content {i}", "user_1", "whatsapp")
            response = await engine.process_message(msg)
            # All should be well under 5000ms
            assert response.latency_ms < 100.0

        # Check SLA compliance
        stats = engine.latency_tracker.get_stats()
        assert stats["sla_compliance"] >= 0.99


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
