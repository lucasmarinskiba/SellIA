# SellIA Infrastructure Gaps + Improvements

**Current Status**: v1.0.0 production ready (basic infrastructure)  
**Gap Analysis**: What's missing for enterprise scale

---

## Critical Gaps (Address Before Phase 34)

### 1. Distributed Tracing
**Current**: Sentry (error tracking only)  
**Gap**: No request tracing across services  
**Impact**: Hard to debug slow requests, N+1 queries, bottlenecks

**Solution**: OpenTelemetry
```python
# backend/app/middleware/tracing.py
from opentelemetry import trace, metrics
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider

jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=6831,
)
trace.set_tracer_provider(TracerProvider())
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

@app.middleware("http")
async def trace_middleware(request: Request, call_next):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span(f"{request.method} {request.url.path}") as span:
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))
        response = await call_next(request)
        span.set_attribute("http.status_code", response.status_code)
        return response
```

**Result**: Full visibility into request flow through all services

### 2. Database Connection Pooling
**Current**: Basic connection pool (default 10 connections)  
**Gap**: No monitoring, tuning, or optimization  
**Impact**: Connection exhaustion under load, slow queries

**Solution**: pgBouncer + monitoring
```ini
# pgbouncer.ini
[databases]
sellia = host=db.internal port=5432 dbname=sellia

[pgbouncer]
pool_mode = transaction
max_client_conn = 1000
default_pool_size = 25
reserve_pool_size = 5
reserve_pool_timeout = 10
```

**Monitoring**:
```python
# Prometheus metrics
db_connections_active = Gauge('db_connections_active', 'Active connections')
db_connections_waiting = Gauge('db_connections_waiting', 'Waiting clients')
db_queries_slow = Counter('db_queries_slow', 'Slow queries >100ms')
```

### 3. Caching Strategy Optimization
**Current**: Redis caching but inconsistent invalidation  
**Gap**: Cache hits ~94%, could be 99%+  
**Impact**: Unnecessary database queries, higher latency

**Solution**: Cache warming + invalidation patterns
```python
# backend/app/services/cache_warmer.py
class CacheWarmer:
    async def warm_on_startup(self):
        """Pre-populate critical caches on startup."""
        # Get all active deals
        deals = await get_active_deals()
        for deal in deals:
            cache_key = f"deal:{deal.id}"
            await cache.set(cache_key, deal, ttl=3600)

    async def invalidate_on_change(self, deal_id: str):
        """Invalidate related caches when deal changes."""
        patterns = [
            f"deal:{deal_id}",
            f"user:*:deals",  # User's deal list
            f"metrics:*",  # Any metrics
        ]
        for pattern in patterns:
            await cache.delete_pattern(pattern)
```

### 4. Async Task Processing
**Current**: Background jobs queued but no workers  
**Gap**: Jobs enqueued but not executed  
**Impact**: Exports timeout, integrations don't sync, webhooks fail

**Solution**: Celery workers
```python
# backend/tasks.py
from celery import Celery

celery_app = Celery(
    'sellia',
    broker='redis://localhost:6379',
    backend='redis://localhost:6379',
)

@celery_app.task(bind=True, max_retries=3)
def send_email(self, to_email: str, subject: str, body: str):
    try:
        # Send email via SES
        return {"status": "sent"}
    except Exception as exc:
        # Exponential backoff retry
        self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))

@celery_app.task
def export_deals_to_csv(user_id: str, filters: dict):
    # Generate CSV
    # Upload to S3
    # Send download link via email
    pass

@celery_app.task
def sync_salesforce_contacts(account_id: str):
    # Sync contacts from Salesforce
    # Log sync results
    pass

# Periodic tasks
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    'sync-salesforce-hourly': {
        'task': 'tasks.sync_salesforce_contacts',
        'schedule': crontab(minute=0),  # Every hour
    },
    'calculate-forecasts-daily': {
        'task': 'tasks.calculate_revenue_forecasts',
        'schedule': crontab(hour=1, minute=0),  # 1am daily
    },
}
```

Deployment:
```bash
# Start workers
celery -A tasks worker --loglevel=info --concurrency=4

# Start scheduler
celery -A tasks beat --loglevel=info
```

### 5. Structured Logging
**Current**: Basic logging, no correlation IDs  
**Gap**: Hard to trace user request through logs  
**Impact**: Difficult debugging, slow troubleshooting

**Solution**: Correlation IDs + structured JSON logs
```python
# backend/app/middleware/logging.py
import uuid
import json
from pythonjsonlogger import jsonlogger

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
        request.state.correlation_id = correlation_id
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response

# Log every request with correlation ID
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
handler.setFormatter(formatter)
logger.addHandler(handler)

# Usage
logger.info("Deal approved", extra={
    "correlation_id": request.state.correlation_id,
    "deal_id": deal_id,
    "user_id": user_id,
    "action": "deal.approve",
})
```

Output (each line is searchable in CloudWatch):
```json
{"timestamp": "2026-08-12T14:30:45Z", "level": "INFO", "message": "Deal approved", "correlation_id": "abc-123", "deal_id": "deal_001", "user_id": "user_123", "action": "deal.approve"}
```

---

## Major Gaps (Phase 34-35)

### 6. Load Testing Framework
**Current**: Manual testing only  
**Gap**: No automated load testing  
**Impact**: Don't know breaking point, can't validate performance gains

**Solution**: K6 load testing
```javascript
// tests/load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '2m', target: 100 },  // Ramp-up
    { duration: '5m', target: 100 },  // Stay
    { duration: '2m', target: 200 },  // Spike
    { duration: '5m', target: 0 },    // Ramp-down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500', 'p(99)<1000'],
    http_req_failed: ['rate<0.1'],
  },
};

export default function () {
  let res = http.get('https://api.production.com/api/v1/deals');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

Run:
```bash
k6 run tests/load_test.js
```

### 7. Blue-Green Deployments
**Current**: Direct deployment (all-or-nothing)  
**Gap**: Can't rollback fast, high risk deployments  
**Impact**: 10-minute downtime if deployment fails

**Solution**: Blue-green infrastructure
```bash
# Current (blue)
docker run -d --name api-blue -p 8000:8000 api:v1.0.0

# New (green)
docker run -d --name api-green -p 8001:8000 api:v1.0.1

# Switch traffic (fast rollback)
nginx conf:
  upstream api {
    server api-green:8000;  # or api-blue:8000
  }

# Rollback if needed: switch back to api-blue
```

### 8. Canary Deployments
**Current**: All-at-once  
**Gap**: Can't detect issues before full rollout  
**Impact**: 1% issue affects 100% of users

**Solution**: Canary with traffic split
```yaml
# kubernetes (optional)
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: api
spec:
  targetRef:
    name: api
  service:
    port: 8000
  analysis:
    interval: 1m
    threshold: 5
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
  stepWeight: 10  # Start with 10% traffic
  maxWeight: 100
  skipAnalysis: false
  steps:
  - weight: 10
    interval: 1m
  - weight: 50
    interval: 1m
  - weight: 100
    interval: 1m
```

---

## Nice-to-Have (Phase 35+)

### 9. Infrastructure as Code (Terraform)
**Current**: Manual AWS console clicks  
**Gap**: Can't reproduce infrastructure, disaster recovery slow  
**Impact**: Inconsistent environments, human error

### 10. Kubernetes Migration
**Current**: Docker Compose on single server  
**Gap**: No orchestration, autoscaling, or high availability  
**Impact**: Single point of failure, manual scaling

### 11. Multi-Region Failover
**Current**: Single region (us-east-1)  
**Gap**: No disaster recovery, global availability  
**Impact**: 8-hour RTO if region goes down

### 12. Cost Optimization
**Current**: No cost tracking  
**Gap**: Don't know if infrastructure is efficient  
**Impact**: Spending more than necessary

**Implementation**:
- Reserved instances (30% savings)
- Spot instances for non-critical workloads
- Auto-scaling (scale down at night)
- CDN optimization (CloudFront caching)

---

## Security Gaps (Before Enterprise Contracts)

### 13. API Key Rotation
**Current**: Keys never rotate  
**Gap**: Compromised key = full access forever  
**Impact**: Security liability

**Solution**:
```python
class APIKeyManager:
    async def create_key_pair(self, user_id: str):
        """Create new key, deprecate old key in 30 days."""
        new_key = generate_api_key()
        old_key = await get_current_key(user_id)
        
        # New key active immediately
        await store_key(user_id, new_key, status='active')
        
        # Old key deprecated in 30 days
        await schedule_key_deprecation(old_key, days=30)
        
        return new_key
```

### 14. Request Signing
**Current**: No webhook signature verification  
**Gap**: Webhooks can be spoofed  
**Impact**: Security vulnerability

**Solution**:
```python
# Sign outgoing webhooks
import hmac
import hashlib

def sign_webhook(payload: dict, secret: str):
    payload_json = json.dumps(payload)
    signature = hmac.new(
        secret.encode(),
        payload_json.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"sha256={signature}"

# Client verifies
def verify_webhook(payload: bytes, signature: str, secret: str):
    expected = sign_webhook(json.loads(payload), secret)
    return hmac.compare_digest(signature, expected)
```

### 15. Secrets Management
**Current**: Secrets in environment variables  
**Gap**: Secrets visible in logs, git history  
**Impact**: Credential exposure risk

**Solution**: HashiCorp Vault
```python
from hvac import Client

vault = Client(url='https://vault.internal')
secret = vault.secrets.kv.v2.read_secret_version(
    path='sellia/database',
)
db_password = secret['data']['data']['password']
```

---

## Summary: Infrastructure Investment Needed

| Gap | Priority | Effort | Impact | Timeline |
|-----|----------|--------|--------|----------|
| Distributed Tracing | P0 | 2 weeks | High visibility | Before Phase 34 |
| Connection Pooling | P0 | 1 week | 10x better scale | Before Phase 34 |
| Caching Optimization | P0 | 2 weeks | 50% latency reduction | Before Phase 34 |
| Async Workers | P1 | 2 weeks | Background jobs work | Before Phase 34 |
| Structured Logging | P1 | 1 week | Better debugging | Before Phase 34 |
| Load Testing | P2 | 1 week | Know breaking point | Phase 34 |
| Blue-Green Deploy | P2 | 1 week | Safe deployments | Phase 34 |
| Canary Deploy | P2 | 2 weeks | Gradual rollout | Phase 35 |
| Terraform | P3 | 3 weeks | Infrastructure as code | Phase 35 |
| Kubernetes | P3 | 4 weeks | Auto-scaling | Phase 36 |
| Multi-Region | P3 | 3 weeks | Global availability | Phase 36 |
| Secrets Manager | P1 | 1 week | Security | Before Phase 34 |

**Estimated Total**: 8-10 weeks to address all P0/P1 gaps

---

**Next Action**: Implement P0 gaps before Phase 34 starts
