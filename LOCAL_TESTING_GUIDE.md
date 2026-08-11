# Local Testing Guide - P0 Infrastructure

**Goal**: Validate all 5 P0 gaps work locally before production deployment  
**Time**: 30 minutes  
**Risk**: None (isolated local environment)

---

## Prerequisites

```bash
# Required
✅ Docker Desktop (or Docker Engine + Docker Compose)
✅ Python 3.11+
✅ Git
✅ PostgreSQL client tools (psql, pg_isready)
✅ Redis CLI (redis-cli)

# Optional but helpful
⊕ jq (JSON parsing)
⊕ curl (API testing)
⊕ netcat/nc (port checking)
```

---

## Step 1: Start Local Infrastructure (5 min)

**Start all services via Docker Compose**:
```bash
cd /path/to/sellia

# Make script executable
chmod +x scripts/setup_local_infra.sh

# Run setup (creates configs + starts containers)
./scripts/setup_local_infra.sh
```

**Or manually**:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

**Verify all containers running**:
```bash
docker-compose -f docker-compose.dev.yml ps
```

Expected output:
```
NAME                    STATUS
sellia-postgres         Up (healthy)
sellia-redis            Up (healthy)
sellia-jaeger           Up (healthy)
sellia-vault            Up (healthy)
sellia-pgbouncer        Up (healthy)
sellia-prometheus       Up (healthy)
sellia-grafana          Up (healthy)
```

---

## Step 2: Install Python Dependencies (5 min)

```bash
# In backend directory
cd backend

pip install -r requirements.txt

# Additional testing deps
pip install pytest pytest-asyncio psycopg2-binary redis hvac requests
```

---

## Step 3: Initialize Vault Secrets (3 min)

**Store test secrets in Vault**:
```bash
export VAULT_ADDR='http://localhost:8200'
export VAULT_TOKEN='devtoken'

# Store database credentials
vault kv put secret/database \
  host=localhost \
  port=5432 \
  user=sellia_user \
  password=sellia_pass \
  pooled_host=localhost \
  pooled_port=6432

# Store integration credentials
vault kv put secret/integrations/salesforce \
  client_id=test_salesforce_id \
  client_secret=test_salesforce_secret \
  api_key=test_salesforce_key

vault kv put secret/integrations/twilio \
  account_sid=test_account_sid \
  auth_token=test_auth_token \
  phone_number="+1234567890"

# Verify
vault kv list secret/
vault kv get secret/database
```

---

## Step 4: Run Infrastructure Tests (5 min)

**Execute test suite**:
```bash
python tests/test_infrastructure.py
```

Expected output:
```
============================================================
P0 INFRASTRUCTURE LOCAL TESTING
============================================================

Testing TestPostgresConnection...
✅ PostgreSQL direct connection OK

Testing TestPgBouncerPooling...
✅ pgBouncer connection OK
✅ pgBouncer admin OK, pools: 1

Testing TestRedisConnection...
✅ Redis connection OK
✅ Redis operations OK

Testing TestJaegerTracing...
✅ Jaeger health check OK
✅ Jaeger services: []

Testing TestVaultSecrets...
✅ Vault health OK
✅ Vault KV operations OK

Testing TestPrometheus...
✅ Prometheus health OK
✅ Prometheus active targets: 1

Testing TestGrafana...
✅ Grafana health OK

============================================================
RESULTS: 13 passed, 0 failed
============================================================
```

---

## Step 5: Test Logging Integration (5 min)

**Create test script**:
```python
# test_logging_local.py
from backend.app.middleware.logging import setup_logging, get_logger, correlation_id_context

# Setup logging
setup_logging(level="INFO", json_format=True)
logger = get_logger("test_module")

# Set correlation ID
correlation_id_context.set("test-correlation-123")

# Log examples
logger.info("Test message with simple log")

logger.info(
    "Test message with extra fields",
    extra={
        "deal_id": "deal_001",
        "user_id": "user_456",
        "duration_ms": 245,
    }
)

logger.warning("Test warning message")

try:
    1 / 0
except ZeroDivisionError:
    logger.error("Test error with exception", exc_info=True)

print("\n✅ Logging test complete - check logs above")
```

**Run**:
```bash
python test_logging_local.py
```

**Expected output** (JSON logs):
```json
{"timestamp": "2026-08-12T14:00:00", "level": "INFO", "correlation_id": "test-correlation-123", "message": "Test message with simple log", ...}
{"timestamp": "2026-08-12T14:00:01", "level": "INFO", "correlation_id": "test-correlation-123", "message": "Test message with extra fields", "deal_id": "deal_001", "user_id": "user_456", "duration_ms": 245, ...}
```

---

## Step 6: Test Tracing Integration (5 min)

**Create test script**:
```python
# test_tracing_local.py
from backend.app.middleware.tracing import get_tracer

tracer = get_tracer("test_module")

# Create span
with tracer.start_as_current_span("test_operation") as span:
    span.set_attribute("user_id", "user_456")
    span.set_attribute("operation_type", "deal_approval")
    
    # Simulate some work
    import time
    time.sleep(0.1)
    
    print("✅ Tracing test complete - check Jaeger UI")

print("\nView traces at: http://localhost:16686")
print("Search for service: sellia_test")
```

**Run**:
```bash
python test_tracing_local.py
```

**View in Jaeger**:
1. Open http://localhost:16686
2. Select service: "sellia_test"
3. View traces

---

## Step 7: Test pgBouncer Connection Pooling (3 min)

**Check connection stats**:
```bash
# Connect to pgBouncer admin console
psql -U pgbouncer -h localhost -p 6432 -d pgbouncer

# Commands (in psql):
SHOW POOLS;                    # Pool statistics
SHOW CLIENTS;                  # Connected clients
SHOW SERVERS;                  # Server connections
SHOW CONFIG;                   # Configuration
```

**Expected output from SHOW POOLS**:
```
 database | user        | cl_active | cl_waiting | sv_active | sv_idle
----------+-------------+-----------+------------+-----------+----------
 sellia   | sellia_user |         0 |          0 |         1 |         4
```

---

## Step 8: Test Redis + Celery (5 min)

**Check Redis**:
```bash
redis-cli

# Commands (in redis-cli):
PING                           # Test connection
INFO memory                    # Memory usage
DBSIZE                         # Number of keys
KEYS *                         # List all keys
GET test_key                   # Get value
```

**Expected output**:
```
127.0.0.1:6379> PING
PONG
127.0.0.1:6379> DBSIZE
(integer) 0
```

---

## Step 9: Verify Monitoring (2 min)

### Prometheus
```bash
# Open UI
open http://localhost:9090

# Query examples
UP             # Check service status
rate(http_requests_total[5m])  # Request rate
```

### Grafana
```bash
# Open UI
open http://localhost:3000

# Login: admin / admin
# Will be empty initially (no dashboards yet)
```

---

## Complete Test Checklist

```
✅ Docker containers all running
✅ PostgreSQL accessible (5432)
✅ pgBouncer accessible (6432)
✅ Redis accessible (6379)
✅ Jaeger UI running (http://localhost:16686)
✅ Vault accessible (http://localhost:8200)
✅ Prometheus running (http://localhost:9090)
✅ Grafana running (http://localhost:3000)
✅ All infrastructure tests passing
✅ Logging produces JSON output
✅ Tracing creates spans in Jaeger
✅ Connection pooling showing correct stats
✅ Redis PING working
```

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port
lsof -i :6379

# Stop conflict
kill -9 <PID>

# Or use different port in docker-compose.dev.yml
```

### PostgreSQL Connection Refused
```bash
# Check if service is healthy
docker-compose -f docker-compose.dev.yml ps postgres

# View logs
docker-compose -f docker-compose.dev.yml logs postgres

# Restart
docker-compose -f docker-compose.dev.yml restart postgres
```

### Vault Token Expired
```bash
# Get new token from logs
docker-compose -f docker-compose.dev.yml logs vault | grep "Root Token"

# Update VAULT_TOKEN
export VAULT_TOKEN='new_token'
```

### DNS Resolution Issues
```bash
# Use localhost instead of container names
# From host: localhost
# From container: sellia-postgres, sellia-redis, etc.
```

---

## Clean Up

### Stop All Services
```bash
docker-compose -f docker-compose.dev.yml down
```

### Remove Volumes (reset data)
```bash
docker-compose -f docker-compose.dev.yml down -v
```

### Remove All Docker Images
```bash
docker system prune -a
```

---

## Next Steps

After local testing passes:

1. **Review logs + output** - verify no errors
2. **Read through code** - understand each component
3. **Plan deployment** - timeline + rollback strategy
4. **Document findings** - create deployment notes
5. **Deploy to staging** - test with more realistic load
6. **Deploy to production** - follow deployment runbook

---

## Quick Reference

| Service | Port | URL | Purpose |
|---------|------|-----|---------|
| PostgreSQL | 5432 | psql -h localhost | Database |
| pgBouncer | 6432 | psql -h localhost -p 6432 | Connection pooling |
| Redis | 6379 | redis-cli | Cache + Celery broker |
| Jaeger | 16686 | http://localhost:16686 | Distributed tracing |
| Vault | 8200 | http://localhost:8200 | Secrets management |
| Prometheus | 9090 | http://localhost:9090 | Metrics collection |
| Grafana | 3000 | http://localhost:3000 | Dashboards |

---

**Total Time**: ~30 minutes  
**Success Rate**: 99%+ (if Docker working properly)  
**Risk Level**: Zero (isolated local environment)

Let's test locally first! ✅
