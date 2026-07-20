"""Load Testing — Simulate 1000+ concurrent users, stress testing, capacity planning."""

import asyncio
import logging
import time
import random
from typing import Dict, List, Any, Optional, Callable, Coroutine
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import statistics

logger = logging.getLogger(__name__)


class LoadTestPhase(Enum):
    """Load test phases."""
    RAMP_UP = "ramp_up"  # Gradually increase load
    STEADY_STATE = "steady_state"  # Maintain constant load
    SPIKE = "spike"  # Sudden spike
    RAMP_DOWN = "ramp_down"  # Gradually decrease load
    COMPLETED = "completed"


@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    request_id: str
    endpoint: str
    method: str
    response_time_ms: float
    status_code: int
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "response_time_ms": round(self.response_time_ms, 2),
            "status_code": self.status_code,
            "success": self.success,
            "error_message": self.error_message,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class LoadTestResult:
    """Results of a load test."""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    min_response_time_ms: float
    max_response_time_ms: float
    avg_response_time_ms: float
    median_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    requests_per_second: float
    error_rate_percent: float
    concurrent_users: int
    test_duration_seconds: float
    started_at: datetime
    completed_at: datetime
    bottlenecks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "test_name": self.test_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "min_response_time_ms": round(self.min_response_time_ms, 2),
            "max_response_time_ms": round(self.max_response_time_ms, 2),
            "avg_response_time_ms": round(self.avg_response_time_ms, 2),
            "median_response_time_ms": round(self.median_response_time_ms, 2),
            "p95_response_time_ms": round(self.p95_response_time_ms, 2),
            "p99_response_time_ms": round(self.p99_response_time_ms, 2),
            "requests_per_second": round(self.requests_per_second, 2),
            "error_rate_percent": round(self.error_rate_percent, 2),
            "concurrent_users": self.concurrent_users,
            "test_duration_seconds": round(self.test_duration_seconds, 2),
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat(),
            "bottlenecks": self.bottlenecks,
        }


class LoadTestConfig:
    """Configuration for load testing."""

    def __init__(
        self,
        name: str,
        target_function: Callable[..., Coroutine],
        concurrent_users: int = 10,
        requests_per_second: int = 100,
        duration_seconds: int = 60,
        ramp_up_seconds: int = 10,
        ramp_down_seconds: int = 10,
    ):
        """Initialize load test config."""
        self.name = name
        self.target_function = target_function
        self.concurrent_users = concurrent_users
        self.requests_per_second = requests_per_second
        self.duration_seconds = duration_seconds
        self.ramp_up_seconds = ramp_up_seconds
        self.ramp_down_seconds = ramp_down_seconds


class LoadTestRunner:
    """Run load tests against endpoints."""

    def __init__(self):
        """Initialize load test runner."""
        self.results: Dict[str, LoadTestResult] = {}
        self.running_tests: Dict[str, bool] = {}

    async def run_load_test(
        self,
        config: LoadTestConfig,
        request_generator: Callable[[], Dict[str, Any]],
    ) -> LoadTestResult:
        """Run a load test."""

        logger.info(f"Starting load test: {config.name}")
        logger.info(f"  Concurrent users: {config.concurrent_users}")
        logger.info(f"  RPS: {config.requests_per_second}")
        logger.info(f"  Duration: {config.duration_seconds}s")

        start_time = datetime.utcnow()
        metrics: List[RequestMetrics] = []

        # Create user tasks
        user_tasks = [
            asyncio.create_task(
                self._user_session(
                    config,
                    request_generator,
                    user_id=i,
                    metrics=metrics,
                )
            )
            for i in range(config.concurrent_users)
        ]

        # Run for specified duration
        try:
            await asyncio.wait_for(
                asyncio.gather(*user_tasks),
                timeout=config.duration_seconds + config.ramp_down_seconds + 5,
            )
        except asyncio.TimeoutError:
            pass
        finally:
            # Cancel remaining tasks
            for task in user_tasks:
                if not task.done():
                    task.cancel()

        end_time = datetime.utcnow()
        test_duration = (end_time - start_time).total_seconds()

        # Analyze results
        result = self._analyze_results(
            config,
            metrics,
            start_time,
            end_time,
            test_duration,
        )

        self.results[config.name] = result
        logger.info(f"Load test completed: {config.name}")
        logger.info(f"  Total requests: {result.total_requests}")
        logger.info(f"  Error rate: {result.error_rate_percent:.2f}%")
        logger.info(f"  Avg response time: {result.avg_response_time_ms:.2f}ms")

        return result

    async def _user_session(
        self,
        config: LoadTestConfig,
        request_generator: Callable[[], Dict[str, Any]],
        user_id: int,
        metrics: List[RequestMetrics],
    ) -> None:
        """Simulate a single user session."""

        start_time = datetime.utcnow()
        end_time = start_time + timedelta(seconds=config.duration_seconds)
        request_interval = 1.0 / (config.requests_per_second / config.concurrent_users)

        # Ramp-up phase
        ramp_up_end = start_time + timedelta(seconds=config.ramp_up_seconds)

        while datetime.utcnow() < end_time:
            now = datetime.utcnow()

            # Ramp-up: gradually increase frequency
            if now < ramp_up_end:
                phase = LoadTestPhase.RAMP_UP
                progress = (now - start_time).total_seconds() / config.ramp_up_seconds
                actual_interval = request_interval / max(progress, 0.1)
            else:
                phase = LoadTestPhase.STEADY_STATE
                actual_interval = request_interval

            # Send request
            try:
                request_data = request_generator()
                response_time = await self._send_request(
                    config,
                    request_data,
                    user_id,
                )

                metrics.append(response_time)

            except Exception as e:
                logger.error(f"Request error in user {user_id}: {e}")

            # Wait before next request
            await asyncio.sleep(actual_interval)

    async def _send_request(
        self,
        config: LoadTestConfig,
        request_data: Dict[str, Any],
        user_id: int,
    ) -> RequestMetrics:
        """Send a single request."""

        import uuid

        start_time = time.time()

        try:
            result = await config.target_function(**request_data)
            response_time_ms = (time.time() - start_time) * 1000
            status_code = 200

            return RequestMetrics(
                request_id=str(uuid.uuid4()),
                endpoint=request_data.get("endpoint", "unknown"),
                method=request_data.get("method", "GET"),
                response_time_ms=response_time_ms,
                status_code=status_code,
                success=True,
            )

        except Exception as e:
            response_time_ms = (time.time() - start_time) * 1000

            return RequestMetrics(
                request_id=str(uuid.uuid4()),
                endpoint=request_data.get("endpoint", "unknown"),
                method=request_data.get("method", "GET"),
                response_time_ms=response_time_ms,
                status_code=500,
                success=False,
                error_message=str(e),
            )

    def _analyze_results(
        self,
        config: LoadTestConfig,
        metrics: List[RequestMetrics],
        started_at: datetime,
        completed_at: datetime,
        test_duration: float,
    ) -> LoadTestResult:
        """Analyze load test results."""

        if not metrics:
            return LoadTestResult(
                test_name=config.name,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                min_response_time_ms=0,
                max_response_time_ms=0,
                avg_response_time_ms=0,
                median_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                requests_per_second=0,
                error_rate_percent=0,
                concurrent_users=config.concurrent_users,
                test_duration_seconds=test_duration,
                started_at=started_at,
                completed_at=completed_at,
            )

        response_times = [m.response_time_ms for m in metrics]
        successful = sum(1 for m in metrics if m.success)
        failed = len(metrics) - successful

        sorted_times = sorted(response_times)
        p95_idx = int(len(sorted_times) * 0.95)
        p99_idx = int(len(sorted_times) * 0.99)

        rps = len(metrics) / test_duration if test_duration > 0 else 0
        error_rate = (failed / len(metrics) * 100) if metrics else 0

        # Detect bottlenecks
        bottlenecks = self._detect_bottlenecks(
            response_times,
            error_rate,
            rps,
        )

        return LoadTestResult(
            test_name=config.name,
            total_requests=len(metrics),
            successful_requests=successful,
            failed_requests=failed,
            min_response_time_ms=min(response_times),
            max_response_time_ms=max(response_times),
            avg_response_time_ms=statistics.mean(response_times),
            median_response_time_ms=statistics.median(response_times),
            p95_response_time_ms=sorted_times[p95_idx] if p95_idx < len(sorted_times) else 0,
            p99_response_time_ms=sorted_times[p99_idx] if p99_idx < len(sorted_times) else 0,
            requests_per_second=rps,
            error_rate_percent=error_rate,
            concurrent_users=config.concurrent_users,
            test_duration_seconds=test_duration,
            started_at=started_at,
            completed_at=completed_at,
            bottlenecks=bottlenecks,
        )

    def _detect_bottlenecks(
        self,
        response_times: List[float],
        error_rate: float,
        rps: float,
    ) -> List[str]:
        """Detect bottlenecks in load test results."""

        bottlenecks = []

        # High P99 latency
        p99 = sorted(response_times)[int(len(response_times) * 0.99)]
        if p99 > 1000:
            bottlenecks.append(f"High P99 latency: {p99:.0f}ms")

        # High error rate
        if error_rate > 1:
            bottlenecks.append(f"High error rate: {error_rate:.2f}%")

        # Low throughput
        if rps < 10:
            bottlenecks.append(f"Low throughput: {rps:.2f} RPS")

        # High variance
        if len(response_times) > 10:
            std_dev = statistics.stdev(response_times)
            if std_dev > statistics.mean(response_times) * 0.5:
                bottlenecks.append(f"High latency variance: {std_dev:.0f}ms")

        return bottlenecks

    def get_test_results(self, test_name: str) -> Optional[Dict[str, Any]]:
        """Get results for a test."""

        if test_name not in self.results:
            return None

        return self.results[test_name].to_dict()

    def get_all_results(self) -> Dict[str, Dict[str, Any]]:
        """Get all test results."""

        return {
            name: result.to_dict()
            for name, result in self.results.items()
        }

    def compare_results(self, test_name_1: str, test_name_2: str) -> Dict[str, Any]:
        """Compare two test results."""

        result1 = self.results.get(test_name_1)
        result2 = self.results.get(test_name_2)

        if not result1 or not result2:
            return {"error": "Test results not found"}

        return {
            "test_1": test_name_1,
            "test_2": test_name_2,
            "avg_response_time_change_percent": (
                (result2.avg_response_time_ms - result1.avg_response_time_ms) /
                result1.avg_response_time_ms * 100
                if result1.avg_response_time_ms > 0 else 0
            ),
            "error_rate_change_percent": result2.error_rate_percent - result1.error_rate_percent,
            "throughput_change_percent": (
                (result2.requests_per_second - result1.requests_per_second) /
                result1.requests_per_second * 100
                if result1.requests_per_second > 0 else 0
            ),
            "p99_latency_change_percent": (
                (result2.p99_response_time_ms - result1.p99_response_time_ms) /
                result1.p99_response_time_ms * 100
                if result1.p99_response_time_ms > 0 else 0
            ),
        }
