# PHASE 5: Codebase Map & Integration Points

**Quick Reference for Developers**

---

## Current Codebase Structure

### Channel System (Existing)

```
backend/app/domains/channels/
├── models.py (128 lines)
│   ├── ChannelPlatform enum (18 platforms)
│   ├── ChannelConnection model
│   ├── Conversation model
│   ├── Message model
│   └── Status enums
│
├── connectors/
│   ├── base.py (BaseChannelConnector)
│   ├── whatsapp.py (100L) — Works ✅
│   ├── email.py (74L) — Works ✅
│   ├── sms.py — MISSING ❌
│   ├── instagram.py
│   ├── telegram.py
│   ├── messenger.py
│   ├── linkedin.py
│   ├── twitter.py
│   ├── threads.py
│   ├── mercadolibre.py
│   ├── amazon.py
│   ├── shopify.py
│   ├── webchat.py
│   ├── facebook_ads.py
│   ├── google_ads.py
│   ├── meta_ads.py
│   ├── tiktok.py
│   ├── tiktok_ads.py
│   ├── beacons.py
│   └── __init__.py (CONNECTOR_REGISTRY)
│
├── schemas.py (Pydantic models for API)
│   ├── ChannelConnectionCreate
│   ├── ChannelConnectionUpdate
│   ├── ChannelConnectionResponse
│   ├── WebhookPayload
│   └── OAuth schemas
│
└── services.py (600+ lines)
    ├── process_incoming_message()
    ├── _ai_classify_intent()
    ├── _detect_competitor_mentions()
    └── Intent + workflow routing

backend/app/api/v1/channels.py (705 lines)
├── Create channel (POST /{business_id}/channels)
├── List channels (GET /{business_id}/channels)
├── Get channel (GET /{business_id}/channels/{id})
├── Update channel (PUT /{business_id}/channels/{id})
├── Delete channel (DELETE /{business_id}/channels/{id})
├── Test channel (POST /{business_id}/channels/{id}/test)
├── OAuth flows
│   ├── get_oauth_url()
│   └── oauth_callback()
├── Webhook verification (GET /webhook/{platform})
└── Webhook reception (POST /webhook/{platform})
```

### Automation System (Existing)

```
backend/app/core/automation/
├── automation_engine.py (230L) ✅ WORKING
│   ├── AutomationEngine class
│   ├── 24/7 execution loop
│   ├── Task registration
│   ├── Job enqueueing
│   └── Error handling
│
├── task_scheduler.py (200L) ✅ WORKING
│   ├── TaskScheduler class
│   ├── Cron-based scheduling
│   └── Built-in schedules
│
├── job_queue.py (250L) ✅ WORKING
│   ├── JobQueue class
│   ├── Priority ordering
│   ├── Rate limiting
│   └── Deduplication
│
├── state_manager.py (220L) ✅ WORKING
│   ├── StateManager class
│   ├── Job tracking
│   └── Statistics
│
├── retry_handler.py (180L) ✅ WORKING
│   ├── RetryHandler class
│   ├── Exponential backoff
│   └── Retry policies
│
├── escalation_handler.py (210L) ✅ WORKING
│   ├── EscalationHandler class
│   ├── Alert routing
│   └── Human escalation
│
├── monitoring_dashboard.py (150L) ✅ WORKING
│   └── Real-time metrics
│
└── AUTOMATION_ENGINE.md ✅ DOCUMENTED
    └── Architecture + usage guide
```

### Notification System (Existing)

```
backend/app/core/notifications/
├── sms_service.py (357 lines) ⚠️ PARTIAL
│   ├── SMSService class
│   ├── SMSProvider enum (Twilio, AWS SNS)
│   ├── SMSTemplate enum (6 templates)
│   ├── Template engine (basic)
│   ├── Twilio integration
│   ├── AWS SNS integration
│   └── Note: Exists but not in channel system
│
└── email_service.py (200L) ✅ WORKING
    ├── Email sending
    └── Formatting
```

### Database Models (Existing)

```
backend/app/domains/channels/models.py

channel_connections table
├── id (UUID)
├── business_id (UUID FK)
├── platform (ChannelPlatform enum)
├── name (string)
├── credentials (JSONB)
├── settings (JSONB)
├── status (ChannelStatus enum)
├── webhook_url (string)
├── webhook_token (string)
├── last_sync_at (datetime)
└── timestamps

conversations table
├── id (UUID)
├── business_id (UUID FK)
├── channel_connection_id (UUID FK)
├── external_id (string)
├── lead_name, lead_email, lead_phone (strings)
├── status (ConversationStatus enum)
├── last_message_at (datetime)
├── extra_data (JSONB)
└── timestamps

messages table
├── id (UUID)
├── conversation_id (UUID FK)
├── direction (MessageDirection: inbound|outbound)
├── content (text)
├── content_type (string)
├── status (MessageStatus enum)
├── external_message_id (string)
├── extra_data (JSONB)
└── timestamps
```

---

## Integration Points for Phase 5

### 1. Add SMS Platform

**File:** `backend/app/domains/channels/models.py`

**Current State:**
```python
class ChannelPlatform(str, enum.Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"
    INSTAGRAM = "instagram"
    # ... 15 more
    # Missing: SMS
```

**Change Required:**
```python
class ChannelPlatform(str, enum.Enum):
    # ... all existing ...
    SMS = "sms"  # ← ADD
```

**Impact:** Minimal (just enum addition)

---

### 2. Create SMS Connector

**File:** `backend/app/domains/channels/connectors/sms.py` (NEW)

**Interface (from BaseChannelConnector):**
```python
class SMSConnector(BaseChannelConnector):
    platform = "sms"
    
    async def send_message(
        self,
        recipient_id: str,
        content: str,
        content_type: str = "text",
        **kwargs
    ) -> dict[str, Any]:
        """Send SMS."""
    
    async def parse_webhook(
        self,
        raw_payload: dict[str, Any]
    ) -> WebhookPayload:
        """Parse webhook payload."""
    
    async def validate_credentials(self) -> bool:
        """Test credentials."""
```

**Required Methods from existing SMS service:**
- Use code from `backend/app/core/notifications/sms_service.py`
- Integrate `SMSProvider` (Twilio, AWS SNS)
- Integrate `SMSTemplateEngine`

---

### 3. Create Message Queue

**File:** `backend/app/core/channels/message_queue.py` (NEW)

**Integration with Automation Engine:**

```python
# In automation_engine.py, add handler:

async def handle_process_message_queue(payload: dict) -> dict:
    """Handler for message queue processing."""
    from app.core.channels.message_queue import MessageQueue
    
    queue = MessageQueue(db)
    stats = await queue.process_pending(batch_size=100)
    return stats

# Register with engine:
engine.register_handler(
    JobType.PROCESS_MESSAGE_QUEUE,
    handle_process_message_queue,
)

# Schedule recurring:
await engine.add_recurring_task(
    name="Process message queue",
    job_type=JobType.PROCESS_MESSAGE_QUEUE,
    schedule="*/5 * * * *",  # Every 5 minutes
    priority=Priority.HIGH,
)
```

**Database Integration:**
- Use existing `Message` model for storage
- Add new `message_queue` table for queuing
- Add `dead_letter_queue` table for investigation

---

### 4. Connect Template Engine

**File:** `backend/app/core/channels/template_engine.py` (NEW)

**Integration with API:**

```python
# In api/v1/messages.py (NEW FILE):

@router.post("/{conversation_id}/send-templated")
async def send_templated_message(
    conversation_id: UUID,
    template_id: str,
    context: dict,
    db: AsyncSession = Depends(get_db),
):
    """Send message using stored template."""
    from app.core.channels.template_engine import TemplateEngine
    
    engine = TemplateEngine(db)
    rendered = await engine.render(
        template_id,
        context,
    )
    # ... send via message queue ...
```

**Database Integration:**
- Add `message_templates` table
- Store template content (JSONB)
- Support versioning + A/B testing

---

### 5. Implement Channel Router

**File:** `backend/app/core/channels/channel_router.py` (NEW)

**Integration with Delivery Service:**

```python
# In delivery_service.py:

from app.core.channels.channel_router import ChannelRouter

async def send_to_contact(
    conversation: Conversation,
    content: str,
    preferred_channel: ChannelPlatform | None = None,
):
    router = ChannelRouter()
    
    # If no preference, auto-select
    if not preferred_channel:
        channel = await router.select_channel(
            conversation,
            conversation.business_id,
            db,
            message_type="promotional",
        )
    else:
        channel = preferred_channel
    
    # ... send via selected channel ...
```

**Data Usage:**
- Reads from `Message` table (engagement history)
- Updates `conversations.extra_data` (channel preferences)
- Uses `state_manager` from automation engine

---

### 6. Build Compliance Module

**File:** `backend/app/core/channels/compliance.py` (NEW)

**Integration with Delivery Service:**

```python
# In delivery_service.py:

from app.core.channels.compliance import ComplianceManager

async def send_to_contact(...):
    compliance = ComplianceManager(db)
    
    # Check if we can send
    can_send, reason = await compliance.can_send(
        conversation,
        channel.platform,
        "promotional",
    )
    
    if not can_send:
        logger.warning(f"Blocked: {reason}")
        return None
    
    # ... proceed with send ...
```

**Database Integration:**
- Add `consent_records` table
- Store GDPR/CCPA preferences in `conversations.extra_data`
- Audit logging for regulatory compliance

---

### 7. Webhook Integration

**Current:** `backend/app/api/v1/channels.py` lines 402-704

**Integration Point - Webhook Reception:**

```python
@router.post("/webhook/{platform}")
async def receive_webhook(
    platform: ChannelPlatform,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    # Already handles all platforms
    # After parsing, calls:
    from app.domains.channels.services import process_incoming_message
    await process_incoming_message(db, channel, payload)
```

**For SMS webhooks (new):**
- Twilio: Parse SID, Body, From fields
- AWS SNS: Parse MessageId, Message fields
- Verify signatures (provided by connectors)

---

## Code Dependencies & Imports

### Phase 5A (SMS Connector)

```python
# Requires:
from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform

# Optional (for E164 validation):
import phonenumbers

# External:
from twilio.rest import Client  # pip install twilio
import boto3  # pip install boto3
```

### Phase 5B (Message Queue)

```python
# Requires:
from app.domains.channels.models import (
    ChannelConnection, Message, MessageDirection, MessageStatus
)
from app.domains.channels.connectors import get_connector
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Internal:
import uuid, logging
from datetime import datetime, timedelta, timezone
from enum import Enum
```

### Phase 5C (Template Engine)

```python
# Requires:
from jinja2 import Environment, BaseLoader, TemplateSyntaxError
from jinja2.sandbox import SandboxedEnvironment
from app.domains.channels.models import ChannelPlatform

# Optional:
import html
```

### Phase 5D (Channel Router)

```python
# Requires:
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.channels.models import (
    ChannelConnection, Conversation, Message, MessageDirection
)
```

### Phase 5E (Compliance Module)

```python
# Requires:
from datetime import datetime, timedelta, timezone
from enum import Enum
from app.domains.channels.models import (
    Conversation, ChannelPlatform
)
from sqlalchemy.ext.asyncio import AsyncSession
```

---

## Testing Integration Points

### Unit Tests

```python
# tests/channels/test_sms_connector.py
from app.domains.channels.connectors.sms import SMSConnector

# tests/channels/test_message_queue.py
from app.core.channels.message_queue import MessageQueue

# tests/channels/test_template_engine.py
from app.core.channels.template_engine import TemplateEngine

# tests/channels/test_channel_router.py
from app.core.channels.channel_router import ChannelRouter

# tests/channels/test_compliance.py
from app.core.channels.compliance import ComplianceManager
```

### Integration Tests

```python
# tests/channels/test_integration.py
# Test flows:
# 1. Create channel → Send message → Check queue → Process → Verify delivery
# 2. Webhook in → Parse → Create conversation → Route reply
# 3. Template render → Personalize → Send → Track engagement
# 4. Compliance check → Block/allow → Log audit
```

---

## Configuration & Environment Variables

### Required Additions

```bash
# SMS (Twilio)
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=+15551234567

# SMS (AWS SNS)
AWS_SNS_REGION=us-east-1
AWS_ACCESS_KEY_ID=xxx
AWS_SECRET_ACCESS_KEY=xxx

# Compliance
ENFORCE_GDPR=true
ENFORCE_CCPA=true
ENFORCE_CAN_SPAM=true
COMPLIANCE_AUDIT_LOG=true

# Message Queue
MESSAGE_QUEUE_BATCH_SIZE=100
MESSAGE_QUEUE_PROCESS_INTERVAL=5  # seconds
MESSAGE_QUEUE_MAX_RETRIES=3
MESSAGE_QUEUE_MAX_CONCURRENT_PER_PLATFORM=3

# Monitoring
MONITORING_ENABLE=true
MONITORING_METRICS_PORT=9090
DEAD_LETTER_ALERT_EMAIL=ops@company.com
```

---

## API Endpoint Changes

### New Endpoints (Phase 5)

```
POST   /api/v1/messages/{conversation_id}/send
GET    /api/v1/messages/{message_id}/status
POST   /api/v1/messages/{conversation_id}/send-templated
POST   /api/v1/messages/{conversation_id}/unsubscribe
GET    /api/v1/messages/queue/stats
GET    /api/v1/messages/dead-letter
GET    /api/v1/messages/templates
POST   /api/v1/messages/templates
```

### Modified Endpoints

```
POST   /api/v1/{business_id}/channels/{channel_id}/test
       ↳ Now works for SMS too

POST   /webhook/{platform}
       ↳ Now handles SMS webhooks
```

---

## Database Migration Order

1. **Phase 5B:** Add `message_queue` table
2. **Phase 5C:** Add `message_templates` table
3. **Phase 5E:** Add `consent_records` table
4. **Phase 5E:** Add `dead_letter_queue` table

**Execution:**
```bash
cd backend
alembic revision --autogenerate -m "Phase 5: Channel Automation"
alembic upgrade head
```

---

## Deployment Checklist

### Pre-Deployment

- [ ] All modules implemented (5A-5F complete)
- [ ] Unit tests passing (>80% coverage)
- [ ] Integration tests passing
- [ ] Load tests validate throughput
- [ ] Code reviewed and approved
- [ ] Documentation written
- [ ] Credentials configured (Twilio, AWS, etc.)
- [ ] Database migrations tested

### Deployment

- [ ] Create feature branch
- [ ] Deploy to staging
- [ ] Run smoke tests
- [ ] Monitor metrics for 24h
- [ ] Deploy to production (gradual rollout)
- [ ] Monitor production metrics
- [ ] Alert team on escalations

### Post-Deployment

- [ ] Monitor SLAs
- [ ] Collect user feedback
- [ ] Analyze metrics
- [ ] Iterate on templates
- [ ] Optimize performance

---

## File Size Summary

```
New Files to Create:
├── sms.py                  (300 lines)
├── message_queue.py        (400 lines)
├── delivery_service.py     (300 lines)
├── template_engine.py      (350 lines)
├── templates.py            (150 lines)
├── channel_router.py       (250 lines)
├── compliance.py           (600 lines)
├── test_connectors.py      (300 lines)
├── test_integration.py     (250 lines)
├── test_compliance.py      (150 lines)
└── test_load.py            (100 lines)

Total New Code: ~3,150 lines

Files to Modify:
├── models.py               (+5 lines)
├── __init__.py             (+3 lines)
├── api/v1/channels.py      (+50 lines for SMS webhooks)
├── automation_engine.py    (+30 lines for queue integration)
└── requirements.txt        (+5 packages)

Total Changes: ~90 lines modified
```

---

## Success Indicators

**After Phase 5 Complete:**

1. **SMS channel appears in UI** ✅
2. **Can send SMS via API** ✅
3. **Messages queue and retry** ✅
4. **Templates personalize** ✅
5. **Best channel auto-selected** ✅
6. **Compliance checks work** ✅
7. **Webhooks process SMS** ✅
8. **Monitoring shows metrics** ✅
9. **Tests all passing** ✅
10. **Production deployment successful** ✅

---

## Quick Reference

| Phase | Files | Lines | Days | Status |
|-------|-------|-------|------|--------|
| 5A    | 3     | 300   | 1-2  | ⏳ TODO |
| 5B    | 2     | 700   | 3-4  | ⏳ TODO |
| 5C    | 2     | 500   | 2-3  | ⏳ TODO |
| 5D    | 1     | 250   | 2    | ⏳ TODO |
| 5E    | 1     | 600   | 3-4  | ⏳ TODO |
| 5F    | 4     | 800   | 2-3  | ⏳ TODO |
| Total | 13    | 3,150 | 14-18| 🎯 Plan |

---

**Ready to start?** Begin with Phase 5A (SMS Connector).  
See `PHASE_5_QUICK_START.md` for step-by-step guidance.

