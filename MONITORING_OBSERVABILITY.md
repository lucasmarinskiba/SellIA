# Monitoring & Observability - Production v1.0.0

**Status**: Configuration ready for deployment  
**Platforms**: Sentry, Prometheus, Grafana, CloudWatch  
**SLA Target**: 99.5% uptime, <500ms p95 latency

## Real-Time Metrics Dashboard

### Key Performance Indicators (KPIs)

#### API Health
```
Metric: API Response Time (p95)
Target: < 500ms
Alert: > 2s → Page on-call
Sources: Sentry, Prometheus
Frequency: Real-time
```

```
Metric: Error Rate
Target: < 1%
Alert: > 5% → Page on-call
Sources: Sentry, CloudWatch logs
Frequency: Real-time
```

```
Metric: Uptime
Target: > 99.5%
Alert: < 99% → Page on-call
Sources: Health checks, synthetic monitoring
Frequency: Every 60s
```

#### Database
```
Metric: Connection Pool Usage
Target: < 80 connections
Alert: > 80 → Page on-call
Sources: PostgreSQL metrics
Frequency: Every 30s
```

```
Metric: Query Time (p95)
Target: < 100ms
Alert: > 500ms → Log escalation
Sources: PostgreSQL slow query log
Frequency: Real-time
```

```
Metric: Disk Usage
Target: < 80%
Alert: > 90% → Page on-call
Sources: CloudWatch, host metrics
Frequency: Every 5 min
```

#### Cache
```
Metric: Redis Hit Rate
Target: > 90%
Alert: < 80% → Investigate
Sources: Redis INFO command
Frequency: Every 60s
```

```
Metric: Redis Memory Usage
Target: < 80% allocated
Alert: > 90% → Page on-call
Sources: Redis metrics
Frequency: Every 30s
```

#### Voice & Integrations
```
Metric: Voice Call Success Rate
Target: > 98%
Alert: < 95% → Investigate
Sources: Twilio logs, app logs
Frequency: Real-time
```

```
Metric: Integration Sync Success Rate
Target: > 99%
Alert: < 98% → Investigate
Sources: App logs, sync job logs
Frequency: Every 5 min
```

---

## Sentry Configuration

### Project Setup
- **Organization**: [YourOrg]
- **Project**: sellia-production
- **DSN**: `https://[key]@sentry.io/[project-id]`
- **Environment**: production
- **Release**: v1.0.0

### Error Tracking

#### Issues to Monitor
- **Unhandled Exceptions**: Critical, notify immediately
- **Database Errors**: High, notify within 15 min
- **API Timeout Errors**: Medium, notify within 1 hour
- **WebSocket Disconnections**: Low, log and review daily

#### Alert Rules
```
Error rate > 5% → Slack #oncall
Error rate > 10% → Page on-call + Slack
Specific error type repeated 3x → Slack #bugs
```

### Breadcrumb Logging
```python
# Log user actions for context
sentry_sdk.capture_breadcrumb(
    message=f"User {user_id} performed action",
    category="user-action",
    level="info",
    data={"action": "create_deal", "deal_id": deal_id}
)

# Log API requests
sentry_sdk.capture_breadcrumb(
    message=f"API request: {method} {path}",
    category="http",
    level="info",
    data={"status_code": 200, "duration_ms": 145}
)
```

### Performance Monitoring (Transactions)
```python
# Track critical paths
with sentry_sdk.start_transaction(op="http.client", name="POST /api/v1/deals") as transaction:
    # API request handling
    pass

# Track database queries
with sentry_sdk.start_transaction(op="db", name="SELECT * FROM deals") as transaction:
    # Query execution
    pass
```

---

## Prometheus Configuration

### Scrape Targets

#### Backend Metrics (Endpoint: :8000/metrics)
```yaml
job_name: 'sellia-backend'
static_configs:
  - targets: ['localhost:8000']
scrape_interval: 15s
```

#### Database Metrics (postgres_exporter:9187)
```yaml
job_name: 'postgres'
static_configs:
  - targets: ['localhost:9187']
scrape_interval: 30s
```

#### Redis Metrics (redis_exporter:9121)
```yaml
job_name: 'redis'
static_configs:
  - targets: ['localhost:9121']
scrape_interval: 30s
```

#### Node Metrics (node_exporter:9100)
```yaml
job_name: 'node'
static_configs:
  - targets: ['localhost:9100']
scrape_interval: 60s
```

### Custom Metrics

#### API Metrics
```
http_request_duration_seconds (histogram)
  labels: method, path, status
  
http_requests_total (counter)
  labels: method, path, status
  
http_request_size_bytes (histogram)
  labels: method, path

http_response_size_bytes (histogram)
  labels: method, path
```

#### Database Metrics
```
db_query_duration_seconds (histogram)
  labels: query_type, table

db_connections_active (gauge)
  labels: database

db_pool_size (gauge)
  
slow_queries_total (counter)
  labels: query_type, table
```

#### Cache Metrics
```
cache_hits_total (counter)
  labels: cache_key_pattern

cache_misses_total (counter)
  labels: cache_key_pattern

cache_hit_rate (gauge)
  
redis_memory_bytes (gauge)
```

#### Voice Metrics
```
voice_calls_total (counter)
  labels: status, duration_bucket

voice_call_duration_seconds (histogram)
  labels: status

voice_transcription_accuracy (gauge)
  
call_recording_upload_duration_seconds (histogram)
```

---

## Grafana Dashboards

### Dashboard 1: System Health (Real-time)
```
Row 1: KPIs
  - Uptime (%)
  - Error Rate (%)
  - Response Time (p95, ms)
  - Active Users

Row 2: API Performance
  - Request rate (req/s)
  - Response time (histogram)
  - Status codes (stacked bar)
  - Top endpoints by latency

Row 3: Database
  - Query time (histogram)
  - Connection pool usage
  - Slow queries (table)
  - Disk usage

Row 4: Cache
  - Hit rate (%)
  - Memory usage
  - Top keys by size
  - Eviction rate

Row 5: Alerts
  - Active alerts (table)
  - Alert firing rate (graph)
  - Mean time to resolve (metric)
```

### Dashboard 2: Business Metrics
```
Row 1: Deal Pipeline
  - Deals closed today
  - Revenue today
  - Forecast accuracy
  
Row 2: User Activity
  - Active users (realtime)
  - Approvals pending
  - Calls made today
  
Row 3: Integration Health
  - Salesforce sync success rate
  - HubSpot sync success rate
  - Stripe payment success rate
  
Row 4: Feature Usage
  - Comments posted
  - Workflows executed
  - Reports generated
```

### Dashboard 3: Mobile App
```
Row 1: App Performance
  - Crash rate
  - Session duration
  - App startup time
  
Row 2: Features
  - Offline sync success rate
  - Push notifications delivered
  - Screen load times
  
Row 3: Platform Usage
  - iOS vs Android
  - Top actions
  - Device types
```

---

## Alert Rules

### Critical Alerts (Page On-Call Immediately)

```yaml
- alert: ServiceDown
  expr: up{job="sellia-backend"} == 0
  for: 1m
  action: page_oncall

- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
  for: 5m
  action: page_oncall

- alert: HighLatency
  expr: histogram_quantile(0.95, http_request_duration_seconds) > 2
  for: 5m
  action: page_oncall

- alert: DatabaseDown
  expr: pg_up{job="postgres"} == 0
  for: 1m
  action: page_oncall

- alert: RedisDown
  expr: redis_up{job="redis"} == 0
  for: 1m
  action: page_oncall
```

### High Alerts (Notify Slack Within 30 Min)

```yaml
- alert: HighMemoryUsage
  expr: (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) < 0.2
  for: 10m
  action: slack #oncall

- alert: HighDiskUsage
  expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
  for: 10m
  action: slack #oncall

- alert: SlowQueries
  expr: rate(slow_queries_total[5m]) > 0.5
  for: 10m
  action: slack #bugs
```

### Low Alerts (Log and Review)

```yaml
- alert: CacheMissRate
  expr: rate(cache_misses_total[5m]) / (rate(cache_misses_total[5m]) + rate(cache_hits_total[5m])) > 0.2
  for: 30m
  action: log

- alert: LowIntegrationSuccessRate
  expr: rate(integration_sync_success[5m]) < 0.98
  for: 30m
  action: log
```

---

## CloudWatch Configuration

### Log Groups
- `/aws/lambda/sellia-backend`: Backend logs
- `/aws/lambda/sellia-frontend`: Frontend logs
- `/aws/rds/postgres`: Database logs
- `/aws/elasticache/redis`: Cache logs

### Log Streams
- `sellia-backend-api`: API logs
- `sellia-backend-jobs`: Job queue logs
- `sellia-backend-webhooks`: Webhook logs
- `sellia-frontend-app`: Frontend logs

### Metric Filters
```
[timestamp, request_id, level = "ERROR", ...] → log error count
[timestamp, request_id, duration > 1000, ...] → log slow request count
[timestamp, request_id, status_code = 5*, ...] → log 5xx count
```

---

## Logging Strategy

### Structured Logging Format

```json
{
  "timestamp": "2026-08-11T14:00:00Z",
  "level": "INFO",
  "service": "sellia-backend",
  "request_id": "req_abc123",
  "user_id": "user_123",
  "action": "create_deal",
  "duration_ms": 145,
  "status": "success",
  "metadata": {
    "deal_id": "deal_456",
    "pipeline_id": "pipe_789"
  }
}
```

### Log Levels
- **DEBUG**: Development only, verbose detail
- **INFO**: Key business events (deal creation, user login, API calls)
- **WARN**: Recoverable errors, degraded performance, retry attempts
- **ERROR**: Unhandled exceptions, data loss, integration failures
- **CRITICAL**: System down, security breaches, data corruption

### Retention Policy
- **Debug logs**: 7 days
- **Info/Warn logs**: 30 days
- **Error logs**: 90 days
- **Audit logs**: 1 year (compliance)

---

## Performance Profiling

### Backend Profiling (Python)
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run code
api_call()

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative').print_stats(20)
```

### Database Profiling
```sql
-- Enable slow query logging
SET log_min_duration_statement = 100;  -- 100ms threshold

-- Analyze query plans
EXPLAIN ANALYZE
SELECT * FROM deals WHERE stage = 'closed' AND closed_at > NOW() - INTERVAL '30 days';
```

### Memory Profiling
```python
from memory_profiler import profile

@profile
def heavy_function():
    # Memory usage tracked line-by-line
    pass
```

---

## Health Checks

### API Health Endpoint (GET /health)
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-08-11T14:00:00Z",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "external_apis": "ok"
  }
}
```

### Readiness Endpoint (GET /ready)
```json
{
  "ready": true,
  "timestamp": "2026-08-11T14:00:00Z"
}
```

### Liveness Endpoint (GET /live)
```json
{
  "alive": true
}
```

---

## Incident Response

### Detection
1. Alert fires (Prometheus/Sentry/CloudWatch)
2. Alert routed to #oncall via Slack integration
3. On-call engineer notified (page if critical)

### Acknowledgment (< 5 min)
- Engineer acknowledges alert in Slack
- Creates incident thread
- Begins investigation

### Diagnosis (< 15 min)
- Gather logs + metrics
- Identify root cause
- Assess blast radius

### Mitigation (< 30 min)
- Deploy fix OR rollback
- Verify resolution
- Monitor for recurrence

### Postmortem (< 24 hours)
- Document timeline
- Root cause analysis
- Action items to prevent recurrence

---

## Verification Checklist (Pre-Launch)

- [ ] Sentry project configured + DSN in code
- [ ] Prometheus scrape jobs configured
- [ ] Grafana dashboards created (3 dashboards)
- [ ] Alert rules in place (critical + high + low)
- [ ] CloudWatch log groups created
- [ ] Health check endpoints working
- [ ] Logging configured (JSON structured logs)
- [ ] Database slow query logging enabled
- [ ] Redis monitoring active
- [ ] On-call escalation configured
- [ ] Team trained on dashboard + alerts
- [ ] Incident response runbook documented
- [ ] Load testing complete (1000 req/s validated)
- [ ] Performance baselines recorded

---

**Status**: Ready for production  
**Last Updated**: 2026-08-11
