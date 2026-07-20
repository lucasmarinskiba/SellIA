# PHASE 5: Quick Start Guide

## 60-Second Overview

**What's DONE:**
- ✅ Channel models + API endpoints
- ✅ WhatsApp + Email connectors
- ✅ Basic SMS service
- ✅ Automation engine (24/7 orchestration)
- ✅ OAuth flows for Meta platforms

**What's MISSING (to implement):**
- ❌ SMS as a channel platform (need to add to ChannelPlatform enum)
- ❌ Message queue (reliability layer)
- ❌ Template engine (personalization)
- ❌ Channel router (intelligent selection)
- ❌ Compliance module (GDPR/CCPA/CAN-SPAM)

**Effort Estimate:** 14-18 days, ~3,000 lines of code

---

## Getting Started

### Step 1: Add SMS Platform (30 min)

**File:** `backend/app/domains/channels/models.py`

```python
class ChannelPlatform(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    SMS = "sms"  # ← ADD THIS
    # ... rest remains same
```

### Step 2: Create SMS Connector (2 hours)

**File:** `backend/app/domains/channels/connectors/sms.py`

Copy from `PHASE_5_TECHNICAL_SPEC.md` → SMS Connector section

### Step 3: Register Connector (15 min)

**File:** `backend/app/domains/channels/connectors/__init__.py`

```python
from .sms import SMSConnector

CONNECTOR_REGISTRY = {
    # ... existing ...
    ChannelPlatform.SMS: SMSConnector,
}
```

### Step 4: Test It (1 hour)

```bash
# Test SMS send
curl -X POST http://localhost:8000/api/v1/channels/test \
  -H "Content-Type: application/json" \
  -d '{
    "platform": "sms",
    "credentials": {
      "provider": "twilio",
      "account_sid": "ACxxx",
      "auth_token": "token",
      "from_number": "+15551234567"
    }
  }'
```

---

## Module Dependencies

```
Phase 5A (SMS): 1 file
├── SMS Connector ← START HERE

Phase 5B (Message Queue): 2 files
├── Message Queue
└── Delivery Service

Phase 5C (Templates): 2 files
├── Template Engine
└── Predefined Templates

Phase 5D (Router): 1 file
└── Channel Router

Phase 5E (Compliance): 1 file
└── Compliance Manager

Phase 5F (Tests): 4 files
└── Unit, Integration, Compliance, Load tests
```

**Build in this order.** Each depends on previous layers.

---

## File Structure

```
backend/app/
├── domains/channels/
│   ├── connectors/
│   │   ├── sms.py ← CREATE
│   │   ├── email.py (existing)
│   │   ├── whatsapp.py (existing)
│   │   └── __init__.py (UPDATE)
│   ├── models.py (UPDATE - add SMS platform)
│   ├── schemas.py (existing)
│   └── services.py (existing)
│
├── core/channels/ ← CREATE THIS DIRECTORY
│   ├── __init__.py
│   ├── message_queue.py ← CREATE
│   ├── delivery_service.py ← CREATE
│   ├── template_engine.py ← CREATE
│   ├── templates.py ← CREATE
│   ├── channel_router.py ← CREATE
│   └── compliance.py ← CREATE
│
├── core/automation/ (existing)
│   └── automation_engine.py (UPDATE - integrate message queue)
│
└── api/v1/
    └── messages.py ← CREATE (new endpoints)

tests/
└── channels/ ← CREATE THIS DIRECTORY
    ├── test_connectors.py
    ├── test_integration.py
    ├── test_compliance.py
    └── test_load.py
```

---

## Configuration Checklist

### Environment Variables

```bash
# SMS (Twilio)
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=+15551234567

# SMS (AWS SNS) - alternative
AWS_SNS_REGION=us-east-1
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx

# Compliance
COMPLIANCE_REGIONS=eu,us_ca,us_other  # Which regulations to enforce
MAX_RETRIES_DEFAULT=3
DEAD_LETTER_ALERT_EMAIL=ops@company.com
```

### Database Migrations

```sql
-- Run these after implementing message queue:
-- See PHASE_5_TECHNICAL_SPEC.md for full SQL

CREATE TABLE message_queue (
    id UUID PRIMARY KEY,
    business_id UUID NOT NULL,
    status VARCHAR(50),
    -- ...
);

CREATE TABLE message_templates (
    id UUID PRIMARY KEY,
    business_id UUID NOT NULL,
    -- ...
);

CREATE TABLE consent_records (
    id UUID PRIMARY KEY,
    conversation_id UUID NOT NULL,
    -- ...
);
```

---

## Testing Locally

### Unit Test Template

```python
# tests/channels/test_sms_connector.py

import pytest
from app.domains.channels.connectors.sms import SMSConnector

@pytest.mark.asyncio
async def test_sms_send():
    connector = SMSConnector({
        "provider": "twilio",
        "account_sid": "ACtest",
        "auth_token": "test",
        "from_number": "+15551234567",
    }, {})
    
    result = await connector.send_message(
        "+14155552671",
        "Hello",
    )
    
    assert result["status"] == "sent"
```

### Integration Test Template

```python
# tests/channels/test_integration.py

@pytest.mark.asyncio
async def test_end_to_end_send():
    # 1. Create channel connection
    # 2. Send message via channel router
    # 3. Process queue
    # 4. Verify delivery status
    pass
```

---

## Common Tasks

### Add a New Channel

1. Create connector at `backend/app/domains/channels/connectors/{platform}.py`
2. Implement:
   - `async send_message()`
   - `async parse_webhook()`
   - `async validate_credentials()`
3. Register in `__init__.py`
4. Add platform to `ChannelPlatform` enum
5. Create unit + integration tests

### Send a Message

```python
from app.core.channels.delivery_service import MessageDeliveryService

delivery = MessageDeliveryService(db)

result = await delivery.send_to_contact(
    conversation=conv,
    content="Hello!",
    preferred_channel=ChannelPlatform.WHATSAPP,
    fallback=True,  # Try SMS if WhatsApp fails
)

print(result)
# {
#   "status": "queued",
#   "message_id": "xxx",
#   "channel_used": "whatsapp"
# }
```

### Send Templated Message

```python
from app.core.channels.template_engine import TemplateEngine

engine = TemplateEngine()

rendered = await engine.render(
    template_content="Hi {{name}}, your order {{order_id}} is ready!",
    context={"name": "John", "order_id": "12345"},
    channel=ChannelPlatform.SMS,
)

# rendered = "Hi John, your order 12345 is ready!"
```

### Check Compliance

```python
from app.core.channels.compliance import ComplianceManager

compliance = ComplianceManager(db, region="eu")

can_send, reason = await compliance.can_send(
    conversation=conv,
    channel=ChannelPlatform.EMAIL,
    message_type="promotional",
)

if not can_send:
    print(f"Cannot send: {reason}")
```

---

## Monitoring

### Key Metrics

```python
# Queue size (should stay < 1000)
pending_count = len(message_queue)

# Delivery rate (should be > 99%)
delivery_rate = successful_sends / total_sends

# Message latency (should be < 5 seconds)
latency = sent_at - queued_at

# Retry rate (should be < 5%)
retry_rate = retried_messages / total_messages

# Dead letter rate (should be near 0%)
dlq_rate = dead_letter_messages / total_messages
```

### Alerts to Set Up

- Queue size > 5000 messages
- Delivery rate < 95%
- Dead letter queue growing
- Template render errors
- Compliance violations

---

## Deployment Phases

### Phase 1: Shadow Mode (3 days)
- Deploy code with feature flags OFF
- Queue messages but don't send
- Validate rendering + formatting
- Test error handling

### Phase 2: Gradual Rollout (5 days)
- Enable for 10% of businesses
- Monitor metrics closely
- Enable for 50% on day 3
- Enable for 100% on day 5

### Phase 3: Optimization (7 days)
- A/B test templates
- Optimize channel routing
- Tune retry policies
- Monitor compliance issues

### Phase 4: Production (ongoing)
- Monitor SLAs
- Analyze performance
- Gather user feedback
- Iterate templates

---

## Troubleshooting

### Messages Not Sending

1. Check queue status: `GET /queue/stats`
2. Check error logs: `message_queue.error_message`
3. Verify credentials: `POST /channels/{id}/test`
4. Check compliance: Is contact opted-in?
5. Check rate limits: Twilio/AWS SNS quotas?

### Template Render Errors

1. Validate template syntax: `{% if ... %}`
2. Check required variables: All present?
3. Check for SQL injection: Use Jinja2 sandbox mode
4. Review error logs: Specific error message?

### High Retry Rate

1. Check API credentials
2. Check network connectivity
3. Increase max_retries for transient errors
4. Check rate limiting (too many concurrent sends?)

### Delivery Taking Long

1. Check queue size (process more frequently)
2. Check batch size (should be 100-500)
3. Check retry backoff (exponential = slower)
4. Check channel provider status (maintenance?)

---

## Code Quality

### Linting

```bash
cd backend
python -m pylint app/core/channels/
python -m black app/core/channels/
```

### Type Checking

```bash
mypy backend/app/core/channels/
```

### Tests

```bash
pytest tests/channels/ -v
pytest tests/channels/ --cov=app.core.channels
```

### Coverage Target

Aim for **>80% code coverage** in each module.

---

## Documentation

Each new file should have:
- Module docstring (purpose + examples)
- Class docstrings (responsibilities)
- Method docstrings (parameters + return types)
- Inline comments for complex logic
- Examples in docstrings

Example:

```python
"""
SMS Connector — Send messages via Twilio or AWS SNS.

Example:
    >>> connector = SMSConnector(credentials, settings)
    >>> result = await connector.send_message("+14155552671", "Hello")
    >>> print(result["status"])
    "sent"
"""
```

---

## Performance Targets

| Metric | Target | Notes |
|--------|--------|-------|
| Message send latency | <5s | Queue → delivery to provider |
| Queue processing | 1000 msg/min | Batch processing |
| API response time | <200ms | Create message endpoint |
| Template rendering | <50ms | Jinja2 compilation |
| Delivery rate | >99.5% | Successful sends |
| Retry success rate | >90% | Messages recovered on retry |

---

## Security Checklist

- [ ] SMS credentials encrypted at rest (use vaults)
- [ ] API keys not in logs
- [ ] Jinja2 sandboxed (no arbitrary code)
- [ ] SQL injection prevention (parameterized queries)
- [ ] Rate limiting (prevent abuse)
- [ ] GDPR consent validation
- [ ] Unsubscribe handling
- [ ] Audit logging (who sent what when)
- [ ] PII handling (don't log full phone numbers)

---

## Support

**Questions?** See:
- `PHASE_5_CHANNEL_AUTOMATION.md` — Architecture overview
- `PHASE_5_TECHNICAL_SPEC.md` — Detailed implementation
- `AUTOMATION_ENGINE.md` — How to integrate with automation

**Issues?** Check:
- Error logs: `docker logs -f backend`
- Database: `psql -d selliarealestatedb`
- Queue status: `GET /api/v1/messages/queue/stats`
- Dead letters: `GET /api/v1/messages/dead-letter`

---

## Timeline

```
Week 1
├─ Mon: SMS Connector (Phase 5A)
├─ Tue: Message Queue (Phase 5B start)
├─ Wed: Message Queue (Phase 5B finish)
├─ Thu: Template Engine (Phase 5C)
└─ Fri: Channel Router (Phase 5D)

Week 2
├─ Mon: Compliance Module (Phase 5E)
├─ Tue: Tests (Phase 5F)
├─ Wed: Shadow Mode Deployment
├─ Thu: Monitoring Setup
└─ Fri: Gradual Rollout (10%)

Week 3
├─ Mon-Tue: Full Rollout (100%)
├─ Wed-Fri: Optimization + Bug Fixes

Week 4
└─ Monitoring + Iteration
```

**Total: 14-18 days**

---

## Success Criteria

- ✅ All 3 channels (WhatsApp, Email, SMS) working
- ✅ Message queue processing 1000+ messages/min
- ✅ >99.5% delivery success rate
- ✅ Zero compliance violations in production
- ✅ <5s average message latency
- ✅ <0.1% dead letter rate
- ✅ 24/7 uptime (no data loss)
- ✅ Full audit trail for compliance
- ✅ >80% code coverage
- ✅ Performance targets met

---

## Next Action

1. **Today:** Review this document + `PHASE_5_CHANNEL_AUTOMATION.md`
2. **Tomorrow:** Start Phase 5A (SMS Connector)
3. **This week:** Complete Phase 5A + 5B
4. **Next week:** Phase 5C-5F

**Ready? Start with:** `backend/app/domains/channels/connectors/sms.py`

