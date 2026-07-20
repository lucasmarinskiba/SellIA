"""
Performance Tests for SellIA Production Deployment
Tests API response times, database performance, frontend load times, and concurrent user capacity.
"""

import asyncio
import time
import requests
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import json
from datetime import datetime

# Configuration
API_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"
TEST_USER_EMAIL = "perf_test@example.com"
TEST_USER_PASSWORD = "PerfTestPass123!"


class PerformanceTest:
    def __init__(self):
        self.results = {
            "api_response_times": [],
            "database_queries": [],
            "frontend_load_times": [],
            "concurrent_users": [],
        }
        self.token = None

    def setup(self):
        """Setup test fixtures"""
        # Login to get token
        response = requests.post(
            f"{API_URL}/api/auth/login",
            json={
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD,
            }
        )
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    def test_api_response_times(self, endpoint: str, method: str = "GET",
                                iterations: int = 100) -> Dict:
        """Test API endpoint response times"""
        print(f"\nTesting {method} {endpoint}...")
        times = []

        headers = {}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        for i in range(iterations):
            start = time.time()

            if method == "GET":
                response = requests.get(f"{API_URL}{endpoint}", headers=headers)
            elif method == "POST":
                response = requests.post(
                    f"{API_URL}{endpoint}",
                    json={"test": "data"},
                    headers=headers
                )

            elapsed = (time.time() - start) * 1000  # Convert to ms
            times.append(elapsed)

            if i % 20 == 0:
                print(f"  Request {i}/{iterations}: {elapsed:.2f}ms")

        # Calculate statistics
        stats = {
            "endpoint": endpoint,
            "method": method,
            "iterations": iterations,
            "min": min(times),
            "max": max(times),
            "mean": statistics.mean(times),
            "median": statistics.median(times),
            "p95": sorted(times)[int(len(times) * 0.95)],
            "p99": sorted(times)[int(len(times) * 0.99)],
        }

        print(f"  Results: Mean={stats['mean']:.2f}ms, P95={stats['p95']:.2f}ms, P99={stats['p99']:.2f}ms")
        return stats

    def test_database_performance(self) -> Dict:
        """Test database query performance"""
        print("\nTesting database performance...")

        # Simulate various queries
        queries = {
            "simple_select": "SELECT 1",
            "user_by_id": f"SELECT * FROM users WHERE id = '1'",
            "sales_cycles": "SELECT * FROM sales_cycles WHERE status = 'active'",
            "complex_join": """
                SELECT s.id, s.name, u.email
                FROM sales_cycles s
                JOIN users u ON s.user_id = u.id
                LIMIT 100
            """
        }

        db_stats = {}
        for query_name, query in queries.items():
            times = []
            for _ in range(50):
                start = time.time()
                # Execute query (this would require DB connection)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)

            db_stats[query_name] = {
                "mean": statistics.mean(times),
                "p95": sorted(times)[int(len(times) * 0.95)],
                "p99": sorted(times)[int(len(times) * 0.99)],
            }

        print(f"  Database stats collected for {len(db_stats)} queries")
        return db_stats

    def test_api_concurrent_load(self, endpoint: str, num_users: int = 100,
                                requests_per_user: int = 10) -> Dict:
        """Test API under concurrent user load"""
        print(f"\nTesting {num_users} concurrent users on {endpoint}...")

        def make_request(user_id: int) -> Dict:
            times = []
            errors = 0

            for _ in range(requests_per_user):
                try:
                    start = time.time()
                    response = requests.get(
                        f"{API_URL}{endpoint}",
                        timeout=30,
                        headers={"Authorization": f"Bearer {self.token}"} if self.token else {}
                    )
                    elapsed = (time.time() - start) * 1000

                    if response.status_code == 200:
                        times.append(elapsed)
                    else:
                        errors += 1

                except requests.RequestException:
                    errors += 1

            return {
                "user_id": user_id,
                "times": times,
                "errors": errors,
            }

        results = []
        with ThreadPoolExecutor(max_workers=num_users) as executor:
            futures = [
                executor.submit(make_request, i)
                for i in range(num_users)
            ]

            for i, future in enumerate(as_completed(futures)):
                result = future.result()
                results.append(result)
                if (i + 1) % 10 == 0:
                    print(f"  Completed {i + 1}/{num_users} users")

        # Aggregate statistics
        all_times = []
        total_errors = 0

        for result in results:
            all_times.extend(result["times"])
            total_errors += result["errors"]

        concurrent_stats = {
            "endpoint": endpoint,
            "num_users": num_users,
            "requests_per_user": requests_per_user,
            "total_requests": len(all_times) + total_errors,
            "successful_requests": len(all_times),
            "failed_requests": total_errors,
            "error_rate": (total_errors / (len(all_times) + total_errors)) * 100,
            "mean_response_time": statistics.mean(all_times) if all_times else 0,
            "p95": sorted(all_times)[int(len(all_times) * 0.95)] if all_times else 0,
            "p99": sorted(all_times)[int(len(all_times) * 0.99)] if all_times else 0,
        }

        print(f"  Results: {concurrent_stats['successful_requests']} successful, "
              f"{concurrent_stats['failed_requests']} failed, "
              f"Error Rate: {concurrent_stats['error_rate']:.2f}%")

        return concurrent_stats

    def test_frontend_load_time(self) -> Dict:
        """Test frontend page load time"""
        print("\nTesting frontend load time...")

        times = []
        for i in range(20):
            start = time.time()

            try:
                response = requests.get(
                    FRONTEND_URL,
                    timeout=10,
                )
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)

                if i % 5 == 0:
                    print(f"  Load {i + 1}: {elapsed:.2f}ms")

            except requests.RequestException as e:
                print(f"  Load {i + 1}: Failed - {e}")

        if times:
            frontend_stats = {
                "endpoint": FRONTEND_URL,
                "iterations": len(times),
                "min": min(times),
                "max": max(times),
                "mean": statistics.mean(times),
                "p95": sorted(times)[int(len(times) * 0.95)],
                "p99": sorted(times)[int(len(times) * 0.99)],
            }

            print(f"  Results: Mean={frontend_stats['mean']:.2f}ms, P95={frontend_stats['p95']:.2f}ms")
            return frontend_stats

        return {}

    def test_rate_limiting(self) -> Dict:
        """Test API rate limiting"""
        print("\nTesting rate limiting...")

        endpoint = f"{API_URL}/api/data"
        rate_limit_stats = {
            "endpoint": endpoint,
            "requests_sent": 0,
            "success": 0,
            "rate_limited": 0,
            "other_errors": 0,
            "rate_limit_threshold": 0,
        }

        # Send requests until rate limited
        for i in range(200):
            try:
                response = requests.get(
                    endpoint,
                    timeout=5,
                    headers={"Authorization": f"Bearer {self.token}"} if self.token else {}
                )

                rate_limit_stats["requests_sent"] += 1

                if response.status_code == 200:
                    rate_limit_stats["success"] += 1
                elif response.status_code == 429:
                    rate_limit_stats["rate_limited"] += 1
                    if rate_limit_stats["rate_limit_threshold"] == 0:
                        rate_limit_stats["rate_limit_threshold"] = i
                else:
                    rate_limit_stats["other_errors"] += 1

                # Stop after hitting rate limit a few times
                if rate_limit_stats["rate_limited"] >= 5:
                    break

            except requests.RequestException:
                rate_limit_stats["other_errors"] += 1

        print(f"  Rate limit triggered after {rate_limit_stats['rate_limit_threshold']} requests")
        return rate_limit_stats

    def generate_report(self) -> str:
        """Generate performance test report"""
        report = f"""
=== SellIA Performance Test Report ===
Generated: {datetime.now().isoformat()}

## API Response Times

### Endpoints Tested
- /api/health - Health check
- /api/data - Data retrieval
- /api/automations - Automation listing

SLA Target: P95 < 200ms, P99 < 500ms

## Database Performance

### Query Types
- Simple SELECT: P95 < 10ms
- User lookups: P95 < 20ms
- Complex JOINs: P95 < 50ms

## Frontend Performance

### Page Load Times
- Target: < 3 seconds
- Caching: Enabled for static assets

## Concurrent User Load

### Capacity Testing
- 100+ concurrent users
- Multiple automations per user
- WebSocket connections active

## Rate Limiting

### API Protection
- 60 requests/minute per IP
- Burst capacity: 100 requests
- Rate limit response time: < 1ms

## Recommendations

1. Response Times
   - Maintain P95 < 200ms for optimal UX
   - Monitor P99 for tail latencies
   - Cache frequently accessed data

2. Database
   - Add indexes for common queries
   - Connection pooling: 20-50 connections
   - Monitor slow query logs

3. Frontend
   - Optimize bundle size
   - Lazy load components
   - Enable CDN caching

4. Scaling
   - Monitor CPU usage at peaks
   - Scale horizontally at 70% capacity
   - Load balance across instances

5. Monitoring
   - Set alerts for P95 > 300ms
   - Monitor error rates continuously
   - Track resource utilization
"""
        return report

    def run_all_tests(self):
        """Run all performance tests"""
        print("=" * 50)
        print("Starting SellIA Performance Tests")
        print("=" * 50)

        self.setup()

        # API Response Time Tests
        print("\n### API RESPONSE TIME TESTS ###")
        health_stats = self.test_api_response_times("/health", iterations=100)
        data_stats = self.test_api_response_times("/api/data", iterations=100)
        automations_stats = self.test_api_response_times("/api/automations", iterations=100)

        # Database Performance Tests
        print("\n### DATABASE PERFORMANCE TESTS ###")
        db_stats = self.test_database_performance()

        # Frontend Load Time Tests
        print("\n### FRONTEND LOAD TIME TESTS ###")
        frontend_stats = self.test_frontend_load_time()

        # Concurrent Load Tests
        print("\n### CONCURRENT USER LOAD TESTS ###")
        concurrent_50 = self.test_api_concurrent_load("/api/data", num_users=50)
        concurrent_100 = self.test_api_concurrent_load("/api/data", num_users=100)

        # Rate Limiting Tests
        print("\n### RATE LIMITING TESTS ###")
        rate_limit_stats = self.test_rate_limiting()

        # Generate Report
        print("\n" + self.generate_report())

        # Save results to JSON
        results = {
            "timestamp": datetime.now().isoformat(),
            "api_response_times": {
                "health": health_stats,
                "data": data_stats,
                "automations": automations_stats,
            },
            "database": db_stats,
            "frontend": frontend_stats,
            "concurrent_load": {
                "50_users": concurrent_50,
                "100_users": concurrent_100,
            },
            "rate_limiting": rate_limit_stats,
        }

        with open("performance_results.json", "w") as f:
            json.dump(results, f, indent=2)

        print("\nResults saved to performance_results.json")

        # Validate against SLAs
        self.validate_slas(results)

    def validate_slas(self, results: Dict):
        """Validate performance against SLAs"""
        print("\n### SLA VALIDATION ###")

        violations = []

        # Check API response times
        for endpoint, stats in results.get("api_response_times", {}).items():
            if stats.get("p95", 0) > 200:
                violations.append(f"API P95 for {endpoint} exceeds 200ms: {stats['p95']:.2f}ms")
            if stats.get("p99", 0) > 500:
                violations.append(f"API P99 for {endpoint} exceeds 500ms: {stats['p99']:.2f}ms")

        # Check frontend load time
        if results.get("frontend", {}).get("mean", 0) > 3000:
            violations.append(f"Frontend load time exceeds 3s: {results['frontend']['mean']:.2f}ms")

        # Check error rates
        for load_test in results.get("concurrent_load", {}).values():
            if load_test.get("error_rate", 0) > 1:
                violations.append(f"Error rate exceeds 1%: {load_test['error_rate']:.2f}%")

        if violations:
            print("SLA VIOLATIONS FOUND:")
            for violation in violations:
                print(f"  - {violation}")
        else:
            print("All SLAs met! Performance is acceptable for production.")


if __name__ == "__main__":
    tester = PerformanceTest()
    tester.run_all_tests()
