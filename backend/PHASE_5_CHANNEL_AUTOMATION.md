# PHASE 5: CHANNEL AUTOMATION — 3,500L Implementation Plan

## Executive Summary

**Status:** 60% Complete. Core infrastructure exists; gaps identified for production-ready deployment.

**Deliverable:** Fully automated WhatsApp, Email, and SMS channels with compliance-first messaging, intelligent routing, and production-grade reliability.

---

## CURRENT STATE AUDIT

### Existing Components (WORKING)
✅ **ChannelConnection Model** (`domains/channels/models.py`)
   - Supports 18+ platforms (WhatsApp, Email, Instagram, TikTok, etc.)
   - Webhook infrastructure (unique tokens per channel)
   - Credential + Settings storage (JSONB)

✅ **WhatsApp Connector** (`domains/channels/connectors/whatsapp.py`)
   - Message send/receive
   - Group support
   - Media handling

✅ **Email Connector** (`domains/channels/connectors/email.py`)
   - SMTP-based send
   - Subject + HTML body support
   - Credential validation

✅ **SMS Service** (`core/notifications/sms_service.py`)
   - Twilio + AWS SNS support
   - Template engine (160 char optimization)
   - 6 predefined templates

✅ **Automation Engine** (`core/automation/automation_engine.py`)
   - 24/7 task orchestration
   - Priority queue + job scheduling
   - State management + retry logic
   - Escalation handling

✅ **API Endpoints** (`api/v1/channels.py`)
   - CRUD for channel connections
   - OAuth flows (Meta, MercadoLibre)
   - Webhook verification + reception
   - Test channel endpoint

### Gaps Identified (MUST IMPLEMENT)

❌ **SMS as a Channel Platform**
   - ChannelPlatform enum missing `SMS` value
   - No SMS connector implementation
   - Integration with automation engine incomplete

❌ **Message Queue / Reliable Delivery**
   - No message_queue.py
   - No retry/fallback for failed sends
   - No dead letter handling
   - Broadcasting to groups untested

❌ **Template Engine**
   - SMS templates exist but basic
   - No dynamic personalization system
   - Missing HTML email templates
   - No template versioning/A/B testing

❌ **Channel Router**
   - No logic to select best channel per lead
   - No channel preference tracking
   - No lead history consideration

❌ **Compliance Module**
   - No GDPR consent tracking
   - No CCPA/CAN-SPAM enforcement
   - No telemarketing suppression list
   - Missing unsubscribe handlers

❌ **Testing**
   - No unit tests for connectors
   - No integration tests
   - No webhook signature verification tests
   - No rate limiting tests

---

## IMPLEMENTATION ROADMAP

### PHASE 5A: SMS Integration (2-3 days)
**Files to Create/Modify:** 5 files, ~600L

#### 1. Add SMS to ChannelPlatform Enum
**File:** `backend/app/domains/channels/models.py`
```python
class ChannelPlatform(str, enum.Enum):
    # ... existing ...
    SMS = "sms"  # ← ADD
```

#### 2. Create SMS Connector
**File:** `backend/app/domains/channels/connectors/sms.py` (~300L)
```python
class SMSConnector(BaseChannelConnector):
    """Twilio/AWS SNS SMS connector."""
    
    platform = "sms"
    
    async def send_message(self, recipient_id: str, content: str, **kwargs) -> dict:
        """Send SMS message with automatic provider fallback."""
        # Twilio primary, AWS SNS fallback
        # E164 validation
        # Length checking + compression
        # Delivery status tracking
    
    async def parse_webhook(self, raw_payload: dict) -> WebhookPayload:
        """Parse SMS status callbacks + inbound messages."""
        # Delivery reports
        # MO messages (inbound)
        
    async def validate_credentials(self) -> bool:
        """Test SMS credentials."""
        # Send test SMS to configured number
        # Or validate API keys directly
```

#### 3. Update Message Schemas
**File:** `backend/app/domains/channels/schemas.py`
```python
class ChannelConnectionCreate(BaseModel):
    platform: ChannelPlatform  # Now includes SMS
    # credentials must include:
    # - For SMS: provider (twilio|aws_sns), account_id, auth_token, sender_number
```

#### 4. Register SMS Connector
**File:** `backend/app/domains/channels/connectors/__init__.py`
```python
from .sms import SMSConnector

CONNECTOR_REGISTRY = {
    # ... existing ...
    ChannelPlatform.SMS: SMSConnector,
}
```

#### 5. Update API Endpoints
**File:** `backend/app/api/v1/channels.py` (add OAuth for SMS providers)
```python
# SMS doesn't use OAuth, just API key validation
# Ensure test_channel_connection works for SMS
```

---

### PHASE 5B: Message Queue & Reliable Delivery (3-4 days)
**Files to Create:** 2 main files, ~700L

#### 1. Create Message Queue
**File:** `backend/app/core/channels/message_queue.py` (~400L)
```python
class MessageQueue:
    """Reliable message delivery with retries, batching, and fallback channels."""
    
    async def enqueue_message(
        self,
        channel: ChannelConnection,
        recipient: str,
        content: str,
        priority: int = 50,
        fallback_channels: list[ChannelPlatform] | None = None,
        metadata: dict | None = None,
    ) -> str:
        """Queue message for sending. Returns message_id."""
        # Store in DB (messages table)
        # Priority queue ordering
        # Idempotency key to prevent duplicates
    
    async def process_pending(self, batch_size: int = 100) -> dict:
        """Process queued messages. Called by automation engine."""
        # Fetch pending messages
        # Send via channel connector
        # Update status on delivery
        # On failure: increment retry count + schedule retry
        # On persistent failure: try fallback channel
    
    async def get_delivery_status(self, message_id: str) -> str:
        """Check message status (pending/sent/failed/delivered/read)."""
    
    async def mark_dead_letter(self, message_id: str, reason: str) -> None:
        """Move to dead letter queue after max retries."""
        # Log for manual investigation
        # Trigger escalation if critical
```

#### 2. Create Message Delivery Service
**File:** `backend/app/core/channels/delivery_service.py` (~300L)
```python
class MessageDeliveryService:
    """High-level delivery orchestration."""
    
    async def send_to_contact(
        self,
        conversation: Conversation,
        content: str,
        preferred_channel: ChannelPlatform | None = None,
        fallback: bool = True,
    ) -> dict:
        """Send message with automatic channel selection + retry."""
        # If preferred_channel: try first, fallback if fails
        # If None: use channel_router to select best
        # Enqueue with fallback list
        # Return {status, message_id, channel_used}
    
    async def broadcast_to_group(
        self,
        channel: ChannelConnection,
        group_id: str,
        content: str,
        batch_delay: float = 0.5,  # Avoid rate limits
    ) -> dict:
        """Send message to group with rate limiting."""
        # Fetch group members
        # Queue individual messages with delays
        # Return {status, queued_count, failed_count}
```

---

### PHASE 5C: Template Engine (2-3 days)
**Files to Create:** 2 files, ~500L

#### 1. Enhanced Template Engine
**File:** `backend/app/core/channels/template_engine.py` (~350L)
```python
class TemplateEngine:
    """Dynamic message generation with personalization."""
    
    async def render(
        self,
        template_id: str,
        channel: ChannelPlatform,
        context: dict,  # {name, product, price, status, etc.}
        language: str = "es",
    ) -> str:
        """Render template with Jinja2 + personalization."""
        # Load template (DB or files)
        # Validate context against template requirements
        # Render with Jinja2
        # Post-process (trim, validate length per channel)
        # Optionally apply tone/style (formal, casual, urgent)
    
    async def create_template(
        self,
        business_id: UUID,
        name: str,
        channel: ChannelPlatform,
        content: str,  # Jinja2 template
        variables: list[str],  # {name, email, product_name, ...}
        tags: list[str] | None = None,
    ) -> dict:
        """Create/update business template."""
    
    async def list_templates(self, business_id: UUID) -> list[dict]:
        """List all templates for business."""
    
    async def preview(
        self,
        template_id: str,
        sample_context: dict,
        channel: ChannelPlatform,
    ) -> str:
        """Preview rendered template with sample data."""
```

#### 2. Predefined Templates
**File:** `backend/app/core/channels/templates.py` (~150L)
```python
TEMPLATES = {
    "sales/inquiry_follow_up": {
        "channels": [ChannelPlatform.WHATSAPP, ChannelPlatform.EMAIL, ChannelPlatform.SMS],
        "whatsapp": """Hi {{name}}! 👋

Still interested in {{product_name}}? 
💰 Special offer: {{discount}}% off today only!

Reply INTEREST to learn more.""",
        "email": """Subject: {{name}}, your {{product_name}} is waiting ⏰
        
Hi {{name}},

We noticed you were interested in {{product_name}}.
Limited time offer: {{discount}}% off! 

[Call to action button]
        
Best regards,
{{business_name}}""",
        "sms": "{{name}}, {{discount}}% off {{product_name}}! Reply YES to claim. Expires {{expiry_date}}.",
    },
    # More templates for shipment, delivery, refund, etc.
}
```

---

### PHASE 5D: Channel Router (2 days)
**Files to Create:** 1 file, ~250L

#### 1. Intelligent Channel Router
**File:** `backend/app/core/channels/channel_router.py` (~250L)
```python
class ChannelRouter:
    """Select optimal channel for each lead."""
    
    async def select_channel(
        self,
        conversation: Conversation,
        business_id: UUID,
        db: AsyncSession,
        message_type: str = "inquiry_follow_up",  # sales, support, announcement, etc.
    ) -> ChannelConnection | None:
        """Determine best channel for this lead."""
        # Priority 1: Lead's preferred channel (if set)
        # Priority 2: Channel with highest engagement history
        # Priority 3: Channel with best response rate (by message_type)
        # Priority 4: First available channel
        # Exclude: disabled channels, rate-limited channels
        
    async def get_engagement_stats(
        self,
        conversation_id: UUID,
        hours: int = 7 * 24,  # 7 days
    ) -> dict:
        """Analyze message history per channel."""
        # {channel_platform: {response_rate, avg_response_time, engagement_score}}
    
    async def record_channel_preference(
        self,
        conversation_id: UUID,
        channel: ChannelPlatform,
        engagement_signal: str = "response",  # response|click|purchase|ignore
    ) -> None:
        """Track channel performance for this lead."""
```

---

### PHASE 5E: Compliance Module (3-4 days)
**Files to Create:** 2 files, ~600L

#### 1. Compliance Manager
**File:** `backend/app/core/channels/compliance.py` (~600L)
```python
class ComplianceManager:
    """Enforce GDPR, CCPA, CAN-SPAM, telemarketing regulations."""
    
    async def check_can_send(
        self,
        conversation: Conversation,
        channel: ChannelPlatform,
        message_type: str = "promotional",  # transactional|promotional|newsletter
        db: AsyncSession,
    ) -> tuple[bool, str | None]:
        """Check if we can legally send to this contact."""
        # Transactional: always allowed (order confirmation, etc.)
        # Promotional/Newsletter: require explicit opt-in
        # Return (can_send: bool, reason_if_denied: str | None)
    
    async def check_gdpr_compliance(self, conversation: Conversation) -> bool:
        """Validate GDPR requirements (EU residents)."""
        # Check consent record
        # Check data retention limits (5 year max)
        # Check right-to-be-forgotten requests
        
    async def check_ccpa_compliance(self, conversation: Conversation) -> bool:
        """Validate CCPA requirements (California residents)."""
        # Opt-in for promotional messages
        # Honor do-not-sell preferences
        
    async def check_can_spam(
        self,
        message_content: str,
        channel: ChannelPlatform,
    ) -> tuple[bool, list[str]]:
        """Validate CAN-SPAM requirements for emails."""
        # Must have unsubscribe link
        # Must have business address
        # Subject line not deceptive
        # No misleading "From" headers
        # Return (compliant, issues)
    
    async def check_telemarketing_rules(
        self,
        phone_number: str,
        country: str = "US",
    ) -> tuple[bool, str | None]:
        """Check Do-Not-Call registers."""
        # FTC DNC (US)
        # TCPA rules
        # GDPR calling restrictions (EU)
    
    async def process_unsubscribe(
        self,
        conversation: Conversation,
        channel: ChannelPlatform,
    ) -> None:
        """Handle unsubscribe requests."""
        # Mark as unsubscribed
        # Log reason
        # Alert business (if needed)
    
    async def get_consent_record(
        self,
        conversation: Conversation,
        channel: ChannelPlatform,
    ) -> dict:
        """Fetch consent + preferences for contact."""
        # {consented: bool, date: datetime, channel, ip, user_agent}
```

---

### PHASE 5F: Testing Suite (2-3 days)
**Files to Create:** 4+ test files, ~800L

#### 1. Unit Tests
**File:** `backend/tests/channels/test_connectors.py` (~300L)
```python
# Test each connector independently:
# - send_message (success, network error, rate limit)
# - parse_webhook (all platforms)
# - validate_credentials (valid, invalid, timeout)
# - broadcast (group send with rate limiting)
```

#### 2. Integration Tests
**File:** `backend/tests/channels/test_integration.py` (~250L)
```python
# End-to-end flows:
# - Create channel → send message → verify delivery
# - Webhook ingress → parse → store in DB
# - Multi-channel broadcast
# - Fallback to secondary channel on error
```

#### 3. Compliance Tests
**File:** `backend/tests/channels/test_compliance.py` (~150L)
```python
# GDPR, CCPA, CAN-SPAM validation
# Unsubscribe handling
# DNC list checks
```

#### 4. Load Tests
**File:** `backend/tests/channels/test_load.py` (~100L)
```python
# Rate limiting
# Batch processing (1000+ messages)
# Queue resilience
```

---

## ARCHITECTURE DIAGRAM

```
┌─────────────────────────────────────────────────────────────────┐
│                    AUTOMATION ENGINE (24/7)                    │
│          (Already exists: core/automation/automation_engine.py)  │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┴──────────────┐
        │                           │
        ▼                           ▼
   ┌─────────────┐          ┌──────────────┐
   │ TaskScheduler           │  JobQueue    │
   │ (cron-based)            │ (priority)   │
   └──────┬──────┘           └──────┬───────┘
          │                         │
          └─────────────┬───────────┘
                        ▼
          ┌─────────────────────────────┐
          │  CHANNEL ROUTER [NEW]        │
          │ (Selects best channel)       │
          └──────────┬────────────────────┘
                     │
        ┌────────────┴──────────────────┐
        │                               │
        ▼                               ▼
  ┌──────────────────┐         ┌──────────────────┐
  │ COMPLIANCE       │         │ MESSAGE QUEUE    │
  │ MANAGER [NEW]    │         │ [NEW]            │
  │ - GDPR           │         │ - Retries        │
  │ - CCPA           │         │ - Dedup          │
  │ - CAN-SPAM       │         │ - Dead Letter    │
  │ - DNC            │         │ - Batch          │
  └────────┬─────────┘         └────────┬─────────┘
           │                            │
           └────────────┬───────────────┘
                        │
        ┌───────────────┴───────────────────┐
        │                                   │
        ▼                                   ▼
  ┌────────────────────────┐       ┌──────────────────┐
  │ TEMPLATE ENGINE [NEW]  │       │ DELIVERY SERVICE │
  │ - Jinja2 rendering     │       │ [NEW]            │
  │ - Personalization      │       │ - Fallback       │
  │ - A/B variants         │       │ - Broadcasting   │
  └────────────┬───────────┘       └────────┬─────────┘
               │                            │
               └────────────┬───────────────┘
                            ▼
       ┌────────────────────────────────────┐
       │   CHANNEL CONNECTORS (Updated)     │
       ├────────────────────────────────────┤
       │  ✅ WhatsApp  │ ✅ Email  │ ✅ SMS │
       │  ✅ Instagram │ ✅ Telegram        │
       │  + 13 more...                      │
       └────────────────────────────────────┘
                            │
       ┌────────────────────┴────────────────┐
       │                                     │
       ▼                                     ▼
  External APIs               STATE MANAGER & DB
  - Meta Graph               - Message status
  - Twilio / AWS SNS         - Delivery reports
  - SMTP                     - Audit trail
  - etc.
```

---

## FILE CHECKLIST

### To Create (10 new files, ~3,000L)
- [ ] `backend/app/domains/channels/connectors/sms.py` (300L)
- [ ] `backend/app/core/channels/message_queue.py` (400L)
- [ ] `backend/app/core/channels/delivery_service.py` (300L)
- [ ] `backend/app/core/channels/template_engine.py` (350L)
- [ ] `backend/app/core/channels/templates.py` (150L)
- [ ] `backend/app/core/channels/channel_router.py` (250L)
- [ ] `backend/app/core/channels/compliance.py` (600L)
- [ ] `backend/tests/channels/test_connectors.py` (300L)
- [ ] `backend/tests/channels/test_integration.py` (250L)
- [ ] `backend/tests/channels/test_load.py` (100L)

### To Modify (5 files)
- [ ] `backend/app/domains/channels/models.py` (add SMS platform + message queue schema)
- [ ] `backend/app/domains/channels/connectors/__init__.py` (register SMS connector)
- [ ] `backend/app/api/v1/channels.py` (test SMS endpoint, webhook handlers)
- [ ] `backend/app/core/automation/automation_engine.py` (integrate message queue processor)
- [ ] `backend/requirements.txt` (add/verify dependencies: twilio, jinja2, etc.)

---

## DEPENDENCIES

### Required Packages
```
twilio>=8.0.0              # SMS/WhatsApp
aiosmtplib>=2.0.0          # Email (async)
jinja2>=3.1.0              # Template rendering
email_validator>=2.0.0     # Email validation
phonenumbers>=8.12.0       # Phone validation
```

### Already Installed (Verified)
```
sqlalchemy>=2.0
pydantic>=2.0
fastapi>=0.95
aiohttp>=3.8
```

---

## DEPLOYMENT CHECKLIST

### Pre-Production
- [ ] Database migrations (new tables for message queue)
- [ ] Environment variables configured
  - `TWILIO_ACCOUNT_SID` / `TWILIO_AUTH_TOKEN`
  - `AWS_SNS_REGION` (if SMS)
  - `SMTP_HOST` / `SMTP_USER` / `SMTP_PASSWORD`
  - `COMPLIANCE_COUNTRY_CODES` (list of countries to enforce compliance)
- [ ] Webhook URLs registered with platforms
- [ ] API rate limits tested
- [ ] Load testing (1000+ concurrent messages)
- [ ] Error scenarios tested (network outage, API down, rate limits)

### Production
- [ ] Monitoring dashboards set up
- [ ] Alerting configured (Slack/Email)
- [ ] Backup channel validated (manual fallback)
- [ ] Compliance audit completed
- [ ] Legal review (especially CAN-SPAM, GDPR)
- [ ] Customer communication (new channels available)
- [ ] Support team trained on escalation procedures

---

## MIGRATION STRATEGY

### Phase 1: Shadow Mode (Week 1)
- Deploy all code
- Queue messages but don't send
- Validate template rendering
- Monitor queue length

### Phase 2: Gradual Rollout (Week 2)
- Enable SMS for 10% of businesses
- Monitor error rates + delivery times
- Collect performance metrics

### Phase 3: Full Deployment (Week 3)
- Enable all channels for all businesses
- Monitor SLAs
- Watch for compliance issues

### Phase 4: Optimization (Week 4)
- A/B test templates
- Optimize send times per channel
- Refine channel routing algorithm

---

## SUCCESS METRICS

By end of Phase 5:
- ✅ Support 3 messaging channels (WhatsApp, Email, SMS)
- ✅ 99.5% message delivery success rate
- ✅ <5s avg message send latency (queued → delivered)
- ✅ Zero compliance violations (GDPR/CCPA/CAN-SPAM)
- ✅ <0.1% dead letter rate
- ✅ 24/7 uptime with automatic failover
- ✅ Full audit trail for regulatory compliance
- ✅ Template A/B testing capability
- ✅ >80% response rate improvement (vs. manual)

---

## RISK MITIGATION

| Risk | Mitigation |
|------|-----------|
| Rate limiting bans | Gradual rollout, respect platform limits, implement backoff |
| Delivery failures | Message queue + retries, fallback channels, dead letter queue |
| Compliance violations | Pre-send validation, audit logging, legal review before launch |
| Spam complaints | Consent tracking, easy unsubscribe, monitor complaint rates |
| Template injection | Jinja2 sandboxed mode, input validation |
| Database overwhelm | Batch processing, archiving old messages, connection pooling |

---

## REFERENCES

- [WhatsApp Business API Docs](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Twilio SMS API](https://www.twilio.com/docs/sms)
- [GDPR Compliance Guide](https://gdpr-info.eu/)
- [CAN-SPAM Act](https://www.ftc.gov/business-guidance/resources/can-spam-act-compliance-guide)
- [CCPA Regulations](https://oag.ca.gov/privacy/ccpa)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)

---

## Next Steps

1. **Approve this plan** with stakeholders
2. **Start Phase 5A** (SMS integration) — 2-3 days
3. **Parallel work:** Setup test environment, prepare test data
4. **Phase 5B-F:** Sequential implementation with testing at each phase
5. **Staging deployment** before production launch

**Estimated Total Time:** 14-18 days with concurrent sprints

