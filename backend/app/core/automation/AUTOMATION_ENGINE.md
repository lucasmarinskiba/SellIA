# Automation Engine — 3,500+ líneas Production-Ready

Sistema que ejecuta **24/7 SIN intervención humana**.

## ARQUITECTURA

```
Strategy (Blue Ocean, Retention, etc)
    ↓
Workflow (Daily Sales, Lead Nurturing, Inventory Sync)
    ↓
TaskScheduler: CUÁNDO ejecutar (cron-based)
    ↓
JobQueue: QUÉ hacer (priority queue)
    ↓
AutomationEngine: ORQUESTA la ejecución
    ↓
Computer Use / API calls: EJECUTA tareas
    ↓
StateManager: TRACKING de estado
    ↓
Monitoring: MÉTRICAS en tiempo real
    ↓
If failed: RetryHandler (exponential backoff)
    ↓
If unrecoverable: EscalationHandler (notifica humano)
```

## COMPONENTES

### 1. AutomationEngine (automation_engine.py)
Central brain que orquesta todo. Ejecuta en un loop infinito 24/7.

**Key Features:**
- Cycle-based execution (checks every second)
- Task scheduling
- Job enqueuing
- Error handling and recovery
- Graceful shutdown

**Usage:**
```python
from app.core.automation import AutomationEngine, Priority, JobType

engine = AutomationEngine(scheduler, job_queue, state_manager, retry_handler, escalation_handler, monitoring)

# Register handlers
async def handle_post_product(payload):
    # Implementar posting de productos
    return {"status": "success"}

engine.register_handler(JobType.POST_PRODUCT, handle_post_product)

# Add recurring tasks
await engine.add_recurring_task(
    name="Post productos (mañana)",
    job_type=JobType.POST_PRODUCT,
    priority=Priority.HIGH,
    schedule="0 9 * * *",  # 9am diario
    payload={"count": 5}
)

# Run 24/7
await engine.run()
```

### 2. TaskScheduler (task_scheduler.py)
Programa cuándo ejecutar tareas.

**Features:**
- Cron-based scheduling (APScheduler compatible)
- One-time tasks
- Recurring tasks
- Smart timing (evita picos)
- Task enable/disable

**Built-in Schedules:**
- Post productos: 9am, 2pm, 6pm (3 veces diarias)
- Responder inquiries: cada 30 min (real-time)
- Enviar emails: 10am, 3pm, 7pm
- Sincronizar inventory: cada hora
- Monitorear performance: cada 2 horas
- Reporte semanal: Lunes 8am

**Cron Expression Examples:**
```
"0 9 * * *"       → Daily at 9am
"*/30 * * * *"    → Every 30 minutes
"0 */6 * * *"     → Every 6 hours
"0 0 * * MON"     → Every Monday midnight
"0 9-18 * * *"    → Every hour 9am-6pm
```

### 3. JobQueue (job_queue.py)
Priority queue que ejecuta jobs en orden.

**Features:**
- Priority-based ordering (urgent first)
- Rate limiting per platform (avoid ban)
- Deduplication (no duplicates)
- Dead letter queue (permanently failed)
- Batch processing support

**Priority Levels:**
- 100: CRITICAL (inquiries)
- 75: HIGH (product posts)
- 50: NORMAL (emails)
- 30: LOW (reports)
- 10: DEFERRED (analytics)

**Rate Limiting:**
```python
queue = JobQueue(max_concurrent_per_platform=3)
# Max 3 jobs per platform simultaneously (avoid rate limits)
```

### 4. StateManager (state_manager.py)
Tracking completo de estado.

**Features:**
- Job state transitions
- Audit trail completo
- Queries by status, type, date range
- Statistics (success rate, avg duration)
- Job recovery after crashes

**State Flow:**
```
PENDING → RUNNING → SUCCESS
                  → FAILED (retry) → RUNNING → SUCCESS
                  → ESCALATED (human review)
```

**Queries:**
```python
# Get recent jobs
recent = await state_manager.get_recent(hours=1, limit=50)

# Get by status
failed = await state_manager.get_by_status(JobStatus.FAILED)

# Get statistics
stats = await state_manager.get_statistics(hours=24)
# Returns: total, success_rate, avg_duration, by_status, by_type
```

### 5. RetryHandler (retry_handler.py)
Reintentos con exponential backoff.

**Policies:**
- AGGRESSIVE: 5 retries, fast backoff (0.5s, 1.5x multiplier)
- DEFAULT: 3 retries, normal backoff (1s, 2x multiplier)
- CONSERVATIVE: 1 retry, long wait (5s, 2x multiplier)
- PAYMENT: 3 retries, very long waits (critical)

**Delays:**
- Attempt 1: 1s
- Attempt 2: 2s
- Attempt 3: 4s
- Attempt 4: 8s
- Attempt 5: 16s (capped at 30s)

**Usage:**
```python
# Automatic retry on job failure
if job.can_retry:
    await retry_handler.schedule_retry(job, policy=RetryPolicy.DEFAULT)
```

### 6. EscalationHandler (escalation_handler.py)
Escala a humanos cuando automation no puede.

**Triggers:**
- Refund requests (need verification)
- Customer complaints (need personalization)
- Payment failures (fraud check?)
- Complex negotiations (stuck on price)
- Regulatory issues (unknown law)
- Max retries exceeded

**Severity Levels:**
- CRITICAL: Immediate (1-5 min response)
- HIGH: Urgent (15-30 min)
- MEDIUM: Important (1-2 hours)
- LOW: Background (next business day)

**Notifications:**
- Email (escalations@company.com)
- Slack (if configured)
- SMS for CRITICAL

**Usage:**
```python
escalation_id = await escalation_handler.escalate(
    job,
    reason="Payment failed - possible fraud",
    severity="critical"
)

# Human resolves
await escalation_handler.resolve_escalation(
    escalation_id,
    resolution="Approved after verification",
    assigned_to="john@company.com"
)
```

### 7. MonitoringDashboard (monitoring_dashboard.py)
Real-time visibility de ALL operations.

**Metrics:**
- Jobs queued / processing / completed
- Success rate (%)
- Error rate (%)
- Avg execution time by type
- Platform performance
- Lead conversion rate
- Revenue generated
- Top errors (retry opportunities)
- Escalations (learning opportunities)

**Dashboards:**
- **Real-time:** Live job execution
- **Hourly:** Throughput, errors
- **Daily:** Revenue, leads, conversions
- **Weekly:** Trends, optimization
- **Monthly:** Growth, profitability

**Alerts:**
- Queue backing up (>100 jobs)
- Dead letters accumulating (>10)
- Unresolved escalations (>5)
- Low success rate (<80% in last hour)
- Service timeouts

**API:**
```python
# Get current status
status = await monitoring.get_status()

# Get KPIs
metrics = await monitoring.get_metrics()

# Get alerts
alerts = await monitoring.get_alerts()

# Export to Prometheus
prometheus_metrics = await monitoring.export_prometheus_metrics()
```

### 8. WorkflowBuilder (workflow_builder.py)
Define workflows complejos.

**Example: Daily Sales Workflow**
```python
builder = WorkflowBuilder()
workflow = builder.create_workflow(
    name="Daily Sales Workflow",
    description="Posts, responds, emails",
    trigger=WorkflowTrigger.SCHEDULE,
    schedule="0 9 * * *"  # 9am
)

# Step 1: Post products
builder.add_step(
    workflow.id,
    "Post morning products",
    "post_product",
    {"count": 5}
)

# Step 2: Respond to inquiries
builder.add_step(
    workflow.id,
    "Respond to inquiries",
    "respond_inquiry",
    {"batch": True}
)

# Step 3: With condition
builder.add_step(
    workflow.id,
    "Send follow-up emails",
    "send_email",
    {"template": "hot_leads"}
)

# Step 4: Report
builder.add_step(
    workflow.id,
    "Generate report",
    "generate_report",
    {"report_type": "daily_sales"}
)
```

## SETUP & USAGE

### Installation
```bash
# Dependencies
pip install croniter aioredis asyncio

# Import
from app.core.automation import (
    setup_automation_engine,
    AutomationEngine,
    JobType,
    Priority,
)
```

### Quick Start
```python
import asyncio
from app.core.automation import setup_automation_engine, JobType, Priority

async def main():
    # Setup
    engine = await setup_automation_engine()
    
    # Register handlers for each job type
    async def handle_post_product(payload):
        # Use Computer Use to post
        products_to_post = payload.get("count", 5)
        # ... implementation
        return {"status": "success", "posted": products_to_post}
    
    async def handle_respond_inquiry(payload):
        # Use AI to respond
        # ... implementation
        return {"status": "success", "replied": 1}
    
    engine.register_handler(JobType.POST_PRODUCT, handle_post_product)
    engine.register_handler(JobType.RESPOND_INQUIRY, handle_respond_inquiry)
    
    # Add tasks
    await engine.add_recurring_task(
        name="Post productos",
        job_type=JobType.POST_PRODUCT,
        priority=Priority.HIGH,
        schedule="0 9 * * *",
        payload={"count": 5}
    )
    
    await engine.add_recurring_task(
        name="Responder inquiries",
        job_type=JobType.RESPOND_INQUIRY,
        priority=Priority.CRITICAL,
        schedule="*/30 * * * *",
        payload={"batch": True}
    )
    
    # Run 24/7
    try:
        await engine.run()
    except KeyboardInterrupt:
        await engine.graceful_shutdown()

if __name__ == "__main__":
    asyncio.run(main())
```

## MONITORING

### Dashboard Endpoint
```python
from app.core.automation import DashboardAPI

dashboard = DashboardAPI(monitoring)

# Get full dashboard data
data = await dashboard.get_dashboard_data()
# {
#     "status": { ... },
#     "metrics": { ... },
#     "alerts": [ ... ],
#     "hourly": { ... }
# }

# Get jobs table for UI
jobs = await dashboard.get_jobs_table(limit=50)

# Get escalations table
escalations = await dashboard.get_escalations_table(limit=50)
```

### Prometheus Metrics
```
job.success - Total successful jobs
job.failure - Total failed jobs
job.duration.post_product - Time to post
job.attempts.respond_inquiry - Retries needed
cycle.duration - Automation cycle time
queue_size - Current queue depth
jobs_active - Currently processing
```

## TESTING

```bash
# Run all tests
pytest app/core/automation/test_automation_engine.py -v

# Run specific test
pytest app/core/automation/test_automation_engine.py::TestJobQueue::test_priority_ordering -v

# With coverage
pytest app/core/automation/test_automation_engine.py --cov=app.core.automation
```

## ERROR HANDLING

### Automatic Retry
```
Job fails
  ↓
Check: can_retry?
  ├─ YES → Schedule retry with backoff
  │         Wait X seconds
  │         Retry job
  │         
  └─ NO → Check escalation policy
           Escalate to human
           Send notification
           Wait for resolution
```

### Circuit Breaker
After 5+ consecutive failures, circuit breaker opens and rejects new requests for 60s.

When half-open (testing recovery), 2 consecutive successes closes circuit.

## PERFORMANCE

**Target Metrics:**
- 50-100 jobs/hour (scales to 1000+)
- 95%+ success rate
- <2 min avg response time to inquiries
- <1% escalation rate
- Zero manual intervention

**Optimizations:**
- Priority queue (urgent first)
- Rate limiting (avoid bans)
- Deduplication (no duplicates)
- Batch processing (reduce API calls)
- Exponential backoff (smart retries)
- Circuit breaker (fail fast)

## DEPLOYMENT

### Docker
```dockerfile
FROM python:3.11
RUN pip install -r requirements.txt
CMD ["python", "-m", "app.main"]
```

### Environment Variables
```
AUTOMATION_ENABLED=true
AUTOMATION_CYCLE_INTERVAL=1  # seconds
MAX_JOBS_PER_PLATFORM=3
ESCALATION_EMAIL=escalations@company.com
MONITORING_ENABLED=true
```

### Health Check
```bash
curl http://localhost:8000/api/automation/status
# {
#   "running": true,
#   "cycle_count": 12345,
#   "queue": {"size": 5, "pending": 3, "running": 2},
#   "jobs": {"failed": 0, "escalated": 1}
# }
```

## ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────┐
│              AutomationEngine (Main Loop)               │
│                    Runs 24/7                            │
└─────────────────────────────────────────────────────────┘
    ↓              ↓              ↓              ↓
┌──────────┐ ┌──────────┐ ┌────────────┐ ┌──────────┐
│Scheduler │ │Job Queue │ │State Mgr   │ │Monitoring│
│(WHEN)    │ │(WHAT)    │ │(TRACKING)  │ │(METRICS) │
└──────────┘ └──────────┘ └────────────┘ └──────────┘
    ↓              ↓              ↓
┌──────────────────────────────────────────────────┐
│    Job Execution (Computer Use / APIs)           │
└──────────────────────────────────────────────────┘
    ↓              ↓              ↓
┌──────────┐ ┌──────────┐ ┌──────────┐
│Retry     │ │Escalation│ │Learning  │
│Engine    │ │Handler   │ │Loop      │
└──────────┘ └──────────┘ └──────────┘
```

## ROADMAP

- [ ] Distributed execution (multiple nodes)
- [ ] ML-based scheduling optimization
- [ ] Slack/Email webhook events
- [ ] Cost optimization (defer low-priority jobs at high cost)
- [ ] A/B testing framework
- [ ] Multi-language support
- [ ] Advanced analytics (attribution, CAC, LTV)

## SUPPORT

For issues or questions:
1. Check logs: `docker logs automation-engine`
2. Check dashboard: `/api/automation/dashboard`
3. Check escalations: `/api/automation/escalations`
4. Create issue with full context
