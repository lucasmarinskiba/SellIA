# Redis Queue + Email Scheduler - FASE 3 STEP 2

## Overview
Redis-based task queue for delayed email sends + batch processing.

**Components:**
- Redis sorted set for delayed tasks
- Email scheduler service
- Task processor (async queue worker)
- Queue monitoring endpoints

---

## Architecture

```
Lead enrolled in workflow
        ↓
Workflow Service creates execution
        ↓
Email Scheduler queues send task
        ↓
Redis Queue (immediate) OR Delayed Set (if delay)
        ↓
Task Processor polls queue
        ↓
Pop task → Send email via SendGrid
        ↓
Update execution status + EmailLog
        ↓
Mark completed OR retry on failure
```

---

## Redis Setup

### Local Development
```bash
# Install Redis
brew install redis

# Start Redis
redis-server

# Or with Docker
docker run -d -p 6379:6379 redis:7-alpine
```

### Environment
```bash
export REDIS_URL="redis://localhost:6379/0"
```

### Production (Heroku, AWS, Render)
```bash
# Heroku
heroku addons:create heroku-redis:premium-0
heroku config:get REDIS_URL
# Auto-set in env

# AWS ElastiCache
export REDIS_URL="redis://yourcluster.abc123.cache.amazonaws.com:6379"
```

---

## Task Types

### SEND_WORKFLOW_EMAIL
Single email send (step progression).

```json
{
  "type": "send_workflow_email",
  "workflow_execution_id": 1001,
  "lead_email": "john@example.com",
  "subject": "Quick question about {company}",
  "body": "<html>...",
  "send_at": "2026-07-29T18:00:00",
  "priority": 5,
  "attempts": 0
}
```

### SEND_BATCH_EMAILS
Multiple emails at once (e.g., segment sends).

```json
{
  "type": "send_batch_emails",
  "workflow_id": 1,
  "leads": [
    { "id": 42, "email": "john@example.com", "subject": "...", "body": "..." },
    { "id": 43, "email": "jane@example.com", "subject": "...", "body": "..." }
  ],
  "send_at": "2026-07-29T18:00:00",
  "count": 2
}
```

### UPDATE_LEAD_SCORE
Increment/decrement lead score on engagement.

```json
{
  "type": "update_lead_score",
  "lead_id": 42,
  "score_delta": 15,
  "reason": "email_clicked"
}
```

### PROGRESS_WORKFLOW
Move execution to next workflow step.

```json
{
  "type": "progress_workflow",
  "workflow_execution_id": 1001,
  "next_step": 2
}
```

---

## Queue Endpoints

### Get Queue Stats
```bash
GET /api/v1/queue/stats

Response:
{
  "status": "ok",
  "queue": {
    "queued": 145,
    "delayed": 32,
    "processing": 3,
    "failed": 2,
    "provider": "redis"
  }
}
```

### Peek Queue
```bash
GET /api/v1/queue/peek?count=5

Response:
{
  "status": "ok",
  "tasks": [
    {
      "type": "send_workflow_email",
      "workflow_execution_id": 1001,
      "lead_email": "john@example.com",
      "send_at": "2026-07-29T15:30:00"
    },
    ...
  ],
  "count": 5
}
```

---

## Integration Example

### Workflow Enrollment with Scheduling

```bash
# 1. Create workflow
POST /api/v1/workflows
{
  "name": "Cold Outreach",
  "steps": [
    {
      "step_number": 1,
      "trigger_type": "manual",
      "email_template": { ... }
    },
    {
      "step_number": 2,
      "trigger_type": "time_delay",
      "delay_days": 3,
      "email_template": { ... }
    }
  ]
}
→ Response: { id: 1, status: "draft" }

# 2. Activate
POST /api/v1/workflows/1/activate

# 3. Create lead
POST /api/v1/leads
{ name: "John", email: "john@example.com", company: "Acme" }
→ Response: { id: 42 }

# 4. Enroll (queues step 1 email)
POST /api/v1/workflows/1/enroll-lead
{ lead_id: 42 }
→ Response: {
    id: 1001,
    step_number: 1,
    tracking_id: "task_1001_...",
    send_at: null  // Immediate send
  }

# 5. Check queue
GET /api/v1/queue/stats
→ { queued: 1, delayed: 0, ... }

# 6. Processor sends email immediately
POST /api/v1/webhooks/sendgrid (email delivered)

# 7. Webhook: email opened
→ Lead score +5

# 8. Next step scheduled for 3 days later
→ Execution 1002 created with send_at: "2026-08-01T..."

# 9. Check delayed queue
GET /api/v1/queue/peek
→ Shows execution 1002 in delayed set

# 10. After 3 days, processor moves to main queue
→ Sends step 2 email
```

---

## Processor Lifecycle

### Startup
```python
# In app lifespan
await init_db()
scheduler = await get_scheduler()  # Connect to Redis
processor = await init_processor(scheduler)
asyncio.create_task(start_processor())  # Start background worker
```

### Processing Loop
```python
while running:
    # Move expired delayed tasks to main queue
    await scheduler.move_delayed_to_queue()
    
    # Process batch of tasks (default: 10 at a time)
    for _ in range(batch_size):
        task = await scheduler.pop_task()
        if not task:
            break
        
        await processor._process_task(task)
    
    # Sleep before next poll
    await asyncio.sleep(5)
```

### Shutdown
```python
# In app lifespan shutdown
await stop_processor()
await scheduler.close()
await close_db()
```

---

## Retry Logic

### Automatic Retries
- Max 3 attempts per task
- Retry delay: 5 minutes
- After 3 failures: move to failed queue

### Manual Inspection
```bash
# Peek at failed queue (for debugging)
redis-cli LRANGE sellia:failed 0 -1
```

---

## Monitoring

### Queue Metrics
```bash
redis-cli
> LLEN sellia:queue       # Tasks pending
> ZCARD sellia:delayed    # Tasks scheduled for later
> LLEN sellia:processing  # Currently executing
> LLEN sellia:failed      # Failed tasks
```

### Grafana Dashboard (Optional)
Track over time:
- Queue depth
- Processing rate
- Failure rate
- Email delivery rate

---

## Performance Tuning

### Batch Size
Default: 10 tasks per poll cycle
```python
processor = TaskProcessor(scheduler, batch_size=20)  # More aggressive
```

### Poll Interval
Default: 5 seconds between cycles
Adjust in task_processor.py:
```python
await asyncio.sleep(5)  # Change to 2, 10, etc.
```

### Redis Connection Pool
For high volume:
```python
redis = await redis.from_url(
    REDIS_URL,
    decode_responses=True,
    max_connections=50  # Increase pool size
)
```

---

## Error Handling

### Redis Unavailable
- Scheduler falls back to MOCK mode
- Tasks logged but not persisted
- Switch to MOCK provider to test without Redis

### Database Connection Lost
- Task fails after attempt
- Retried 3 times (5-min intervals)
- Moved to failed queue
- Manually retry once DB recovered

### Email Send Failure
- Task marked failed
- Retried up to 3 times
- Failed task stored with error detail

---

## Testing

### Manual Queue Test
```bash
# Enroll lead (queues email)
POST /api/v1/workflows/1/enroll-lead
{ lead_id: 42 }

# Check queue
GET /api/v1/queue/stats
→ queued: 1

# Processor sends email
# (Check logs: "📨 Email sent")

# Simulate webhook
POST /api/v1/webhooks/sendgrid/test-open?email=john@example.com

# Check execution status
GET /api/v1/workflows/executions/list?workflow_id=1
→ status: "opened", opened_count: 1
```

### Mock Mode (No Redis)
```bash
# Unset REDIS_URL (or set invalid value)
unset REDIS_URL

# Run app
# Logs: "[MOCK] Queued: task_..."
# Queue ops return 0 (no persistence)
```

---

## Next Steps (FASE 3.3)

- [ ] Celery for distributed workers
- [ ] Multi-worker deployment
- [ ] Queue priority lanes
- [ ] Dead-letter queue
- [ ] Webhook signature verification
- [ ] Rate limiting (SendGrid throttle)
- [ ] Email template versioning (A/B test)

---

## Troubleshooting

### Queue stuck / not processing
1. Check Redis: `redis-cli PING` → should return PONG
2. Check processor logs
3. Restart processor: `systemctl restart sellia-processor`

### High latency on send
- Batch size too large → reduce
- Poll interval too long → decrease
- Redis latency → check connection

### Emails sent twice
- Duplicate task in queue (rare)
- Redis persistence enabled, recovered tasks
- Use `tracking_id` uniqueness to prevent duplicates

### Tasks piling up (backlog)
- Processor too slow → increase batch size
- Redis slow → upgrade instance
- SendGrid rate limit hit → add backoff

