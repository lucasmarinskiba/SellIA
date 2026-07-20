# SellIA Monitoring & Observability Setup

Complete guide for setting up monitoring, logging, and observability for production.

## 1. Datadog Integration

### Install Datadog Agent
```bash
# Using Docker
docker run -d \
  --name datadog-agent \
  --cgroupns host \
  --pid host \
  -v /var/run/docker.sock:/var/run/docker.sock:ro \
  -v /proc/:/host/proc/:ro \
  -v /sys/fs/cgroup/:/host/sys/fs/cgroup:ro \
  -e DD_AGENT_HOST=localhost \
  -e DD_API_KEY=${DATADOG_API_KEY} \
  -e DD_SITE=datadoghq.com \
  gcr.io/datadoghq/agent:latest
```

### Enable Trace Collection
```python
# backend/app/main.py
from ddtrace import tracer, config
from ddtrace.contrib.fastapi import patch_all

# Patch libraries
patch_all()

# Enable tracing
tracer.enabled = True

app = FastAPI()

# Add trace middleware
from ddtrace.contrib.fastapi import patch_fastapi
patch_fastapi(app)
```

### Monitor Key Metrics
```python
# backend/app/core/monitoring.py
from datadog import api
from datadog.api import metrics

# Custom metrics
def track_sales_automation():
    """Track sales automation events"""
    metrics.metric(
        'selliaai.automation.executed',
        1,
        tags=['environment:production', 'automation_type:email']
    )

def track_api_performance(endpoint: str, duration_ms: float):
    """Track API endpoint performance"""
    metrics.metric(
        'selliaai.api.response_time',
        duration_ms,
        tags=[f'endpoint:{endpoint}', 'environment:production']
    )
```

## 2. Sentry Error Tracking

### Initialize Sentry
```python
# backend/app/main.py
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[
        FastApiIntegration(),
        SqlalchemyIntegration(),
        RedisIntegration(),
    ],
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
    environment=os.getenv('ENVIRONMENT'),
    attach_stacktrace=True,
    capture_local_variables=True,
)
```

### Custom Error Monitoring
```python
# backend/app/api/routes/automations.py
from sentry_sdk import capture_exception, capture_message

@app.post("/api/automations")
async def create_automation(automation: AutomationRequest):
    try:
        # Business logic
        pass
    except Exception as e:
        capture_exception(e)
        raise HTTPException(status_code=500, detail="Automation creation failed")
```

## 3. CloudWatch Logging (AWS)

### Configure CloudWatch Agent
```bash
# Install agent
curl https://s3.amazonaws.com/amazoncloudwatch-agent/amazon_linux/amd64/latest/amazon-cloudwatch-agent.rpm -O
rpm -U ./amazon-cloudwatch-agent.rpm

# Configure
cat > /opt/aws/amazon-cloudwatch-agent/etc/config.json << 'EOF'
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/docker/backend.log",
            "log_group_name": "/aws/selliaai/backend",
            "log_stream_name": "{instance_id}"
          },
          {
            "file_path": "/var/log/nginx/access.log",
            "log_group_name": "/aws/selliaai/nginx",
            "log_stream_name": "access"
          },
          {
            "file_path": "/var/log/nginx/error.log",
            "log_group_name": "/aws/selliaai/nginx",
            "log_stream_name": "error"
          }
        ]
      }
    }
  },
  "metrics": {
    "metrics_collected": {
      "cpu": {"measurement": [{"name": "cpu_usage_idle", "rename": "CPU_IDLE"}]},
      "disk": {"measurement": [{"name": "used_percent", "rename": "DISK_USED"}]},
      "mem": {"measurement": [{"name": "mem_used_percent", "rename": "MEM_USED"}]}
    }
  }
}
EOF
```

### Log Insights Queries
```sql
-- Count errors per endpoint
fields @timestamp, @message, @uri
| stats count() as error_count by @uri
| filter @message like /ERROR/

-- Database query performance
fields @timestamp, query_time, query
| stats avg(query_time), max(query_time), pct(query_time, 95) by query

-- API latency percentiles
fields response_time
| stats pct(response_time, 50), pct(response_time, 95), pct(response_time, 99)
```

## 4. Prometheus & Grafana

### Prometheus Configuration
```yaml
# prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'backend'
    static_configs:
      - targets: ['localhost:8000']

  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']

  - job_name: 'nginx'
    static_configs:
      - targets: ['localhost:9113']
```

### Grafana Dashboards
```bash
# Docker compose addition
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3001:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
    volumes:
      - grafana_data:/var/lib/grafana
```

## 5. Log Aggregation with ELK Stack

### Elasticsearch Configuration
```yaml
# docker-compose.yml
services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.0.0
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
    volumes:
      - es_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"

  logstash:
    image: docker.elastic.co/logstash/logstash:8.0.0
    volumes:
      - ./logstash/logstash.conf:/usr/share/logstash/pipeline/logstash.conf
    depends_on:
      - elasticsearch
    ports:
      - "5000:5000"

  kibana:
    image: docker.elastic.co/kibana/kibana:8.0.0
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
```

### Logstash Pipeline Configuration
```conf
# logstash/logstash.conf
input {
  tcp {
    port => 5000
    codec => json
  }
  
  file {
    path => "/var/log/docker/backend.log"
    start_position => "beginning"
  }
}

filter {
  mutate {
    add_field => { "environment" => "production" }
  }
  
  if [message] =~ /ERROR/ {
    mutate {
      add_tag => [ "error" ]
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "selliaai-%{+YYYY.MM.dd}"
  }
  
  stdout {
    codec => json
  }
}
```

## 6. Application Performance Monitoring (APM)

### Backend Instrumentation
```python
# backend/app/core/monitoring.py
from datetime import datetime
import time
from functools import wraps

def monitor_performance(endpoint: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = (time.time() - start_time) * 1000
                
                # Log performance metrics
                logger.info(
                    "endpoint_performance",
                    endpoint=endpoint,
                    duration_ms=duration,
                    status="success"
                )
                
                return result
            except Exception as e:
                duration = (time.time() - start_time) * 1000
                logger.error(
                    "endpoint_error",
                    endpoint=endpoint,
                    duration_ms=duration,
                    error=str(e)
                )
                raise
        return wrapper
    return decorator

# Usage
@app.get("/api/data")
@monitor_performance("get_data")
async def get_data():
    pass
```

## 7. Alerting Rules

### Datadog Alerts
```python
# Set up in Datadog UI or via API
{
  "name": "High API Error Rate",
  "query": "avg:trace.web.request.errors{env:production} > 0.05",
  "alert_type": "metric alert",
  "thresholds": {
    "critical": 0.05,
    "warning": 0.02
  },
  "notification_list": ["@pagerduty"],
  "tags": ["environment:production"]
}
```

### Custom Alerts
```python
# backend/app/tasks/monitoring.py
from celery import shared_task
from datetime import datetime, timedelta

@shared_task
def check_system_health():
    """Check system health and alert if issues detected"""
    
    # Check database connection pool
    active_connections = db.engine.pool.checkedout()
    if active_connections > db.engine.pool.size * 0.8:
        alert("Database pool near capacity", severity="warning")
    
    # Check Redis memory
    redis_info = redis_client.info()
    used_memory_percent = (redis_info['used_memory'] / redis_info['maxmemory']) * 100
    if used_memory_percent > 80:
        alert("Redis memory usage high", severity="warning")
    
    # Check disk space
    import shutil
    disk = shutil.disk_usage("/")
    used_percent = (disk.used / disk.total) * 100
    if used_percent > 85:
        alert("Disk space running low", severity="critical")
```

## 8. Health Checks

### Backend Health Endpoint
```python
# backend/app/api/routes/health.py
from sqlalchemy import text

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("APP_VERSION"),
        "environment": os.getenv("ENVIRONMENT"),
        "services": {}
    }
    
    # Check database
    try:
        async with db.engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        health_status["services"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["services"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Check Redis
    try:
        redis_client.ping()
        health_status["services"]["redis"] = {"status": "healthy"}
    except Exception as e:
        health_status["services"]["redis"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "degraded"
    
    # Check external services
    try:
        stripe.Account.retrieve()
        health_status["services"]["stripe"] = {"status": "healthy"}
    except Exception as e:
        health_status["services"]["stripe"] = {"status": "unhealthy", "error": str(e)}
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return JSONResponse(health_status, status_code=status_code)
```

## 9. Performance Baselines

### Establish Performance SLAs
```yaml
# Performance targets
api_latency:
  p50: 50ms
  p95: 200ms
  p99: 500ms

database_query:
  p50: 10ms
  p95: 50ms
  p99: 100ms

page_load:
  target: 3 seconds
  caching: 1 year for static assets

uptime:
  target: 99.95%
```

## 10. Dashboard Setup

### Key Metrics Dashboard
```
1. API Health
   - Request rate
   - Error rate
   - Latency (p50, p95, p99)

2. Database Performance
   - Connection pool usage
   - Query count
   - Slow queries
   - Replication lag

3. Infrastructure
   - CPU usage
   - Memory usage
   - Disk I/O
   - Network I/O

4. Business Metrics
   - Sales automations executed
   - Revenue generated
   - Active users
   - Conversion rate

5. Security Events
   - Failed login attempts
   - Rate limit triggers
   - API key usage
   - Unusual activity
```

## 11. Backup Monitoring

### Backup Health Checks
```python
# backend/app/tasks/backup.py
import subprocess
from datetime import datetime, timedelta

@shared_task
def verify_backup_integrity():
    """Verify recent backups are valid"""
    backup_dir = "/backups"
    
    # Get most recent backup
    recent_backup = max(
        [os.path.join(backup_dir, f) for f in os.listdir(backup_dir)],
        key=os.path.getctime
    )
    
    # Check backup age
    backup_age = datetime.now() - datetime.fromtimestamp(os.path.getctime(recent_backup))
    if backup_age > timedelta(days=1):
        alert("No recent backup found", severity="critical")
    
    # Test restore (on staging)
    try:
        # Verify backup integrity
        result = subprocess.run(
            f"pg_restore --list {recent_backup}",
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            alert("Backup integrity check failed", severity="critical")
    except Exception as e:
        alert(f"Backup verification error: {e}", severity="error")
```

## 12. Incident Response

### Alert Escalation
```yaml
# PagerDuty Integration
incidents:
  critical:
    - immediate: page on-call engineer
    - notify: Slack #incidents
    - create: incident ticket
    - sla: 15 minute response

  warning:
    - notify: Slack #alerts
    - create: low-priority ticket
    - sla: 2 hour response
```

## Monitoring Checklist

- [ ] Datadog agent installed and reporting
- [ ] Sentry error tracking configured
- [ ] CloudWatch logs streaming
- [ ] Prometheus scraping targets
- [ ] Grafana dashboards created
- [ ] ELK stack operational
- [ ] Health check endpoint working
- [ ] Alert rules configured
- [ ] Backup monitoring enabled
- [ ] Performance baselines established
- [ ] Incident response procedures documented
- [ ] On-call schedule configured
- [ ] Runbooks created for common issues
- [ ] Log retention policies set
- [ ] Regular drills scheduled
