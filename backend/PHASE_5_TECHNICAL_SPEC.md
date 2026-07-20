# PHASE 5: Technical Specification & Implementation Details

## Table of Contents
1. [SMS Connector Implementation](#sms-connector)
2. [Message Queue System](#message-queue)
3. [Template Engine](#template-engine)
4. [Channel Router](#channel-router)
5. [Compliance Module](#compliance)
6. [Database Schema](#database-schema)
7. [API Endpoints](#api-endpoints)
8. [Error Handling](#error-handling)
9. [Code Examples](#code-examples)

---

## SMS Connector

### File: `backend/app/domains/channels/connectors/sms.py`

```python
"""SMS Connector — Twilio + AWS SNS."""

import logging
from typing import Any
from enum import Enum

from app.domains.channels.connectors.base import BaseChannelConnector
from app.domains.channels.schemas import WebhookPayload
from app.domains.channels.models import ChannelPlatform

logger = logging.getLogger(__name__)


class SMSProvider(Enum):
    """Supported SMS providers."""
    TWILIO = "twilio"
    AWS_SNS = "aws_sns"


class SMSConnector(BaseChannelConnector):
    """SMS connector supporting Twilio and AWS SNS."""
    
    platform = "sms"
    
    def __init__(self, credentials: dict[str, Any], settings: dict[str, Any]):
        super().__init__(credentials, settings)
        self.provider = SMSProvider(credentials.get("provider", "twilio"))
        self.sender_id = credentials.get("sender_id", "SellIA")
        
        if self.provider == SMSProvider.TWILIO:
            self._init_twilio()
        elif self.provider == SMSProvider.AWS_SNS:
            self._init_aws_sns()
    
    def _init_twilio(self):
        """Initialize Twilio client."""
        try:
            from twilio.rest import Client
            account_sid = self.credentials.get("account_sid")
            auth_token = self.credentials.get("auth_token")
            
            if not account_sid or not auth_token:
                raise ValueError("Missing Twilio credentials")
            
            self.twilio_client = Client(account_sid, auth_token)
            self.twilio_phone = self.credentials.get("from_number")
        except ImportError:
            logger.error("Twilio not installed")
            self.twilio_client = None
    
    def _init_aws_sns(self):
        """Initialize AWS SNS client."""
        try:
            import boto3
            region = self.credentials.get("region", "us-east-1")
            self.sns_client = boto3.client("sns", region_name=region)
        except ImportError:
            logger.error("boto3 not installed")
            self.sns_client = None
    
    async def send_message(
        self,
        recipient_id: str,
        content: str,
        content_type: str = "text",
        **kwargs
    ) -> dict[str, Any]:
        """Send SMS message."""
        # Validate E.164 format
        if not recipient_id.startswith("+"):
            raise ValueError(f"Invalid phone format: {recipient_id}. Use E.164: +1234567890")
        
        # Validate length (160 chars for SMS, 153 for long message)
        if len(content) > 160 and not self.settings.get("allow_concatenated", True):
            raise ValueError(f"SMS too long: {len(content)} chars")
        
        try:
            if self.provider == SMSProvider.TWILIO:
                return await self._send_twilio(recipient_id, content)
            elif self.provider == SMSProvider.AWS_SNS:
                return await self._send_aws_sns(recipient_id, content)
        except Exception as e:
            logger.error(f"SMS send error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _send_twilio(
        self,
        recipient_id: str,
        content: str,
    ) -> dict[str, Any]:
        """Send via Twilio."""
        if not self.twilio_client:
            return {"status": "error", "error": "Twilio not configured"}
        
        try:
            message = self.twilio_client.messages.create(
                body=content,
                from_=self.twilio_phone,
                to=recipient_id,
            )
            
            return {
                "status": "sent",
                "message_id": message.sid,
                "provider": "twilio",
                "cost": message.price or None,
            }
        except Exception as e:
            logger.error(f"Twilio error: {e}")
            return {"status": "error", "error": str(e), "provider": "twilio"}
    
    async def _send_aws_sns(
        self,
        recipient_id: str,
        content: str,
    ) -> dict[str, Any]:
        """Send via AWS SNS."""
        if not self.sns_client:
            return {"status": "error", "error": "AWS SNS not configured"}
        
        try:
            response = self.sns_client.publish(
                PhoneNumber=recipient_id,
                Message=content,
                MessageAttributes={
                    "AWS.SNS.SMS.SenderID": {
                        "DataType": "String",
                        "StringValue": self.sender_id,
                    },
                    "AWS.SNS.SMS.SMSType": {
                        "DataType": "String",
                        "StringValue": "Transactional",
                    },
                },
            )
            
            return {
                "status": "sent",
                "message_id": response["MessageId"],
                "provider": "aws_sns",
            }
        except Exception as e:
            logger.error(f"AWS SNS error: {e}")
            return {"status": "error", "error": str(e), "provider": "aws_sns"}
    
    async def parse_webhook(
        self,
        raw_payload: dict[str, Any],
    ) -> WebhookPayload:
        """Parse SMS webhook (delivery report or MO message)."""
        
        # Determine message type
        message_type = raw_payload.get("MessageStatus") or raw_payload.get("EventType")
        
        if message_type in ("delivered", "sent", "failed"):
            # Status report — usually we don't process as incoming
            # But store for analytics
            return WebhookPayload(
                platform=ChannelPlatform.SMS,
                external_id=raw_payload.get("MessageSid"),
                content_type="status_report",
                content=f"SMS {message_type}",
                extra_data=raw_payload,
            )
        
        else:
            # Inbound message (MO)
            return WebhookPayload(
                platform=ChannelPlatform.SMS,
                external_id=raw_payload.get("From"),
                sender_phone=raw_payload.get("From"),
                content=raw_payload.get("Body", ""),
                content_type="text",
                extra_data=raw_payload,
            )
    
    async def validate_credentials(self) -> bool:
        """Test SMS credentials."""
        try:
            if self.provider == SMSProvider.TWILIO:
                # Verify account exists and has credits
                if not self.twilio_client:
                    return False
                account = self.twilio_client.api.accounts.get(
                    self.credentials["account_sid"]
                ).fetch()
                return account.status == "active"
            
            elif self.provider == SMSProvider.AWS_SNS:
                # Try to get account attributes
                if not self.sns_client:
                    return False
                self.sns_client.get_sms_attributes(
                    Attributes=["MonthlySpendLimit"]
                )
                return True
        
        except Exception as e:
            logger.error(f"Credential validation error: {e}")
            return False
```

### Required Credentials in Database

```json
{
  "provider": "twilio",  // or "aws_sns"
  "account_sid": "ACxxxxx",
  "auth_token": "token",
  "from_number": "+15551234567",
  "sender_id": "SellIA"  // For AWS SNS
}
```

---

## Message Queue System

### File: `backend/app/core/channels/message_queue.py`

```python
"""Message Queue — Reliable delivery with retries and fallback."""

import logging
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Optional, Any

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.channels.models import (
    ChannelConnection, ChannelPlatform, Conversation, Message,
    MessageDirection, MessageStatus
)

logger = logging.getLogger(__name__)


class QueuedMessageStatus(str, Enum):
    """Status of message in queue."""
    PENDING = "pending"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class QueuedMessage:
    """In-memory queued message representation."""
    
    def __init__(
        self,
        message_id: str,
        channel: ChannelConnection,
        recipient: str,
        content: str,
        priority: int = 50,
        fallback_channels: Optional[list[ChannelPlatform]] = None,
        max_retries: int = 3,
        metadata: Optional[dict] = None,
    ):
        self.message_id = message_id
        self.channel = channel
        self.recipient = recipient
        self.content = content
        self.priority = priority
        self.fallback_channels = fallback_channels or []
        self.max_retries = max_retries
        self.retry_count = 0
        self.metadata = metadata or {}
        self.created_at = datetime.now(timezone.utc)
        self.status = QueuedMessageStatus.PENDING
        self.error_reason = None
    
    def can_retry(self) -> bool:
        """Check if message can be retried."""
        return self.retry_count < self.max_retries


class MessageQueue:
    """Priority queue for reliable message delivery."""
    
    def __init__(self, db: AsyncSession, max_concurrent_per_platform: int = 3):
        self.db = db
        self.max_concurrent_per_platform = max_concurrent_per_platform
        self.queue: list[QueuedMessage] = []
        self.processing = False
    
    async def enqueue(
        self,
        channel: ChannelConnection,
        recipient: str,
        content: str,
        priority: int = 50,
        fallback_channels: Optional[list[ChannelPlatform]] = None,
        metadata: Optional[dict] = None,
    ) -> str:
        """Add message to queue. Returns message_id."""
        
        message_id = str(uuid.uuid4())
        
        # Create QueuedMessage
        queued = QueuedMessage(
            message_id=message_id,
            channel=channel,
            recipient=recipient,
            content=content,
            priority=priority,
            fallback_channels=fallback_channels,
            metadata=metadata,
        )
        
        # Store in database
        msg = Message(
            conversation_id=metadata.get("conversation_id"),
            direction=MessageDirection.OUTBOUND,
            content=content,
            content_type="text",
            status=MessageStatus.PENDING,
            extra_data={
                "queue_id": message_id,
                "priority": priority,
                "channel_platform": channel.platform.value,
                **metadata,
            },
        )
        self.db.add(msg)
        await self.db.commit()
        
        # Add to priority queue (higher priority first)
        self.queue.append(queued)
        self.queue.sort(key=lambda x: (-x.priority, x.created_at))
        
        logger.info(f"Message queued: {message_id} (priority={priority})")
        return message_id
    
    async def process_pending(
        self,
        batch_size: int = 100,
        max_concurrent: Optional[int] = None,
    ) -> dict[str, Any]:
        """Process queued messages. Called by automation engine."""
        
        if self.processing:
            return {"status": "already_running"}
        
        self.processing = True
        stats = {
            "processed": 0,
            "sent": 0,
            "failed": 0,
            "retried": 0,
            "dead_letter": 0,
        }
        
        try:
            # Process up to batch_size messages
            for _ in range(min(batch_size, len(self.queue))):
                if not self.queue:
                    break
                
                queued = self.queue.pop(0)
                stats["processed"] += 1
                
                # Send message
                try:
                    from app.domains.channels.connectors import get_connector
                    
                    connector = get_connector(
                        queued.channel.platform,
                        queued.channel.credentials,
                        queued.channel.settings,
                    )
                    
                    result = await connector.send_message(
                        queued.recipient,
                        queued.content,
                    )
                    
                    if result.get("status") == "sent":
                        queued.status = QueuedMessageStatus.SENT
                        stats["sent"] += 1
                        
                        # Update message record
                        # TODO: Update Message.status = MessageStatus.SENT
                    
                    else:
                        # Send failed
                        queued.status = QueuedMessageStatus.FAILED
                        queued.error_reason = result.get("error")
                        queued.retry_count += 1
                        stats["failed"] += 1
                        
                        # Check if can retry
                        if queued.can_retry():
                            self.queue.append(queued)
                            self.queue.sort(key=lambda x: (-x.priority, x.created_at))
                            stats["retried"] += 1
                            logger.warning(f"Message retry: {queued.message_id} (attempt {queued.retry_count})")
                        else:
                            # Move to dead letter
                            await self._move_to_dead_letter(
                                queued,
                                f"Max retries exceeded: {queued.error_reason}"
                            )
                            stats["dead_letter"] += 1
                
                except Exception as e:
                    logger.error(f"Error processing message {queued.message_id}: {e}")
                    queued.error_reason = str(e)
                    queued.retry_count += 1
                    
                    if queued.can_retry():
                        self.queue.append(queued)
                        self.queue.sort(key=lambda x: (-x.priority, x.created_at))
                        stats["retried"] += 1
                    else:
                        await self._move_to_dead_letter(queued, str(e))
                        stats["dead_letter"] += 1
        
        finally:
            self.processing = False
        
        logger.info(f"Queue processing complete: {stats}")
        return stats
    
    async def _move_to_dead_letter(
        self,
        queued: QueuedMessage,
        reason: str,
    ) -> None:
        """Move message to dead letter queue for manual investigation."""
        # Store in dead_letter_messages table (create if doesn't exist)
        # Alert admins
        logger.error(f"Message dead-lettered: {queued.message_id} — {reason}")
        
        # TODO: Trigger escalation if critical
    
    async def get_queue_stats(self) -> dict:
        """Get current queue statistics."""
        return {
            "pending": len(self.queue),
            "oldest_message": self.queue[0].created_at if self.queue else None,
            "total_priority_sum": sum(q.priority for q in self.queue),
            "by_platform": self._count_by_platform(),
        }
    
    def _count_by_platform(self) -> dict:
        """Count pending messages by platform."""
        counts = {}
        for q in self.queue:
            platform = q.channel.platform.value
            counts[platform] = counts.get(platform, 0) + 1
        return counts
```

---

## Template Engine

### File: `backend/app/core/channels/template_engine.py`

```python
"""Template Engine — Dynamic message generation with personalization."""

import logging
from typing import Any, Optional
from jinja2 import Environment, BaseLoader, TemplateError, TemplateSyntaxError
from jinja2.sandbox import SandboxedEnvironment

from app.domains.channels.models import ChannelPlatform

logger = logging.getLogger(__name__)


class TemplateEngine:
    """Jinja2-based template rendering with channel-specific formatting."""
    
    def __init__(self, sandbox: bool = True):
        """Initialize template engine."""
        if sandbox:
            self.env = SandboxedEnvironment(loader=BaseLoader())
        else:
            self.env = Environment(loader=BaseLoader())
        
        # Add custom filters
        self.env.filters["truncate_sms"] = self._truncate_sms
        self.env.filters["escape_html"] = self._escape_html
        self.env.filters["phone_format"] = self._phone_format
    
    async def render(
        self,
        template_content: str,
        context: dict[str, Any],
        channel: ChannelPlatform,
    ) -> str:
        """Render template with context validation."""
        
        try:
            template = self.env.from_string(template_content)
            rendered = template.render(**context)
            
            # Post-process by channel
            if channel == ChannelPlatform.SMS:
                rendered = self._format_for_sms(rendered)
            elif channel == ChannelPlatform.EMAIL:
                rendered = self._format_for_email(rendered)
            elif channel == ChannelPlatform.WHATSAPP:
                rendered = self._format_for_whatsapp(rendered)
            
            return rendered
        
        except TemplateSyntaxError as e:
            logger.error(f"Template syntax error: {e}")
            raise ValueError(f"Invalid template: {e}")
        except TemplateError as e:
            logger.error(f"Template render error: {e}")
            raise ValueError(f"Template rendering failed: {e}")
    
    def _format_for_sms(self, content: str) -> str:
        """Format content for SMS (160 char limit)."""
        content = content.replace("\n", " ")  # Remove newlines
        if len(content) > 160:
            content = content[:157] + "..."
        return content.strip()
    
    def _format_for_email(self, content: str) -> str:
        """Format content for email."""
        # Already HTML, just validate
        return content
    
    def _format_for_whatsapp(self, content: str) -> str:
        """Format content for WhatsApp (markdown-like)."""
        # Keep newlines for readability
        return content.strip()
    
    def _truncate_sms(self, value: str, length: int = 160) -> str:
        """Jinja2 filter: truncate to SMS length."""
        if len(value) > length:
            return value[:length-3] + "..."
        return value
    
    def _escape_html(self, value: str) -> str:
        """Jinja2 filter: escape HTML."""
        import html
        return html.escape(value)
    
    def _phone_format(self, value: str) -> str:
        """Jinja2 filter: format phone number."""
        # Simple E.164 validation
        if not value.startswith("+"):
            return f"+{value}"
        return value
    
    async def validate_template(
        self,
        template_content: str,
        required_variables: list[str],
    ) -> tuple[bool, Optional[str]]:
        """Validate template has no syntax errors and includes all variables."""
        
        try:
            template = self.env.from_string(template_content)
        except TemplateSyntaxError as e:
            return False, f"Syntax error: {e}"
        
        # Check for required variables
        template_vars = template.module.__dict__.keys()
        missing = set(required_variables) - set(template_vars)
        
        if missing:
            return False, f"Missing variables: {missing}"
        
        return True, None


# Predefined templates
TEMPLATES = {
    "sales/inquiry_follow_up": {
        "channels": ["whatsapp", "email", "sms"],
        "required_variables": ["name", "product_name"],
        "content": {
            "whatsapp": """Hi {{name}}! 👋

Still interested in {{product_name}}?
{% if discount %}💰 Special offer: {{discount}}% off today only!{% endif %}

Reply INTEREST to learn more.""",
            
            "email": """<h2>Hi {{name}},</h2>
<p>We noticed you were interested in <strong>{{product_name}}</strong>.</p>
{% if discount %}<p>🎉 Limited time offer: {{discount}}% off!</p>{% endif %}
<a href="{{cta_url}}">Learn More</a>
<p>Best regards,<br>{{business_name}}</p>""",
            
            "sms": "Hi {{name}}, still interested in {{product_name}}? {{discount|default('Special offer')}} off today! Reply YES.",
        },
    },
    
    "logistics/shipment_notification": {
        "channels": ["whatsapp", "email", "sms"],
        "required_variables": ["order_id", "tracking_number"],
        "content": {
            "whatsapp": """📦 Order {{order_id}} shipped!

Tracking: {{tracking_number}}
ETA: {{estimated_delivery}}

Track here: {{tracking_url}}""",
            
            "email": """<h2>Your order has shipped!</h2>
<p>Order ID: {{order_id}}</p>
<p>Tracking: <a href="{{tracking_url}}">{{tracking_number}}</a></p>
<p>Estimated delivery: {{estimated_delivery}}</p>""",
            
            "sms": "Order {{order_id}} shipped! Tracking: {{tracking_number}} ETA: {{estimated_delivery}}",
        },
    },
}
```

---

## Channel Router

### File: `backend/app/core/channels/channel_router.py`

```python
"""Channel Router — Intelligent channel selection per lead."""

import logging
from typing import Optional
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.channels.models import (
    ChannelConnection, ChannelPlatform, Conversation, Message,
    MessageDirection
)

logger = logging.getLogger(__name__)


class ChannelRouter:
    """Select optimal channel for each lead based on engagement."""
    
    async def select_channel(
        self,
        conversation: Conversation,
        business_id,
        db: AsyncSession,
        message_type: str = "follow_up",  # follow_up, promotional, support
        exclude_platforms: Optional[list[ChannelPlatform]] = None,
    ) -> Optional[ChannelConnection]:
        """Select best channel for this lead."""
        
        exclude_platforms = exclude_platforms or []
        
        # Priority 1: Lead's preferred channel (if set in extra_data)
        preferred = conversation.extra_data.get("preferred_channel")
        if preferred:
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.business_id == business_id,
                    ChannelConnection.platform == ChannelPlatform(preferred),
                    ChannelConnection.is_active == True,
                )
            )
            channel = result.scalar_one_or_none()
            if channel and channel.platform not in exclude_platforms:
                logger.info(f"Selected preferred channel: {preferred}")
                return channel
        
        # Priority 2: Channel with highest engagement score
        engagement = await self._calculate_engagement_scores(
            conversation.id,
            db,
            hours=7 * 24,
        )
        
        if engagement:
            best_platform = max(engagement.items(), key=lambda x: x[1]["score"])[0]
            
            result = await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.business_id == business_id,
                    ChannelConnection.platform == best_platform,
                    ChannelConnection.is_active == True,
                )
            )
            channel = result.scalar_one_or_none()
            if channel and channel.platform not in exclude_platforms:
                logger.info(f"Selected high-engagement channel: {best_platform}")
                return channel
        
        # Priority 3: First active channel
        result = await db.execute(
            select(ChannelConnection).where(
                ChannelConnection.business_id == business_id,
                ChannelConnection.is_active == True,
            ).order_by(ChannelConnection.created_at)
        )
        channel = result.scalar_one_or_none()
        if channel and channel.platform not in exclude_platforms:
            logger.info(f"Selected first available channel: {channel.platform}")
            return channel
        
        logger.warning("No available channel found")
        return None
    
    async def _calculate_engagement_scores(
        self,
        conversation_id,
        db: AsyncSession,
        hours: int = 168,  # 7 days
    ) -> dict[ChannelPlatform, dict]:
        """Calculate engagement metrics per channel."""
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Query messages by channel
        result = await db.execute(
            select(
                Message.content_type,
                func.count(Message.id).label("count"),
                func.sum((Message.direction == MessageDirection.INBOUND).cast(int)).label("inbound"),
            ).where(
                Message.conversation_id == conversation_id,
                Message.created_at >= cutoff_time,
            ).group_by(Message.content_type)
        )
        
        scores = {}
        for row in result:
            channel_type = row[0]
            message_count = row[1]
            inbound_count = row[2]
            
            # Calculate score
            # Inbound responses count double (indicates engagement)
            score = message_count + (inbound_count * 2)
            
            try:
                platform = ChannelPlatform(channel_type)
                scores[platform] = {
                    "message_count": message_count,
                    "inbound_count": inbound_count,
                    "score": score,
                }
            except ValueError:
                # Unknown platform type
                pass
        
        return scores
    
    async def record_channel_interaction(
        self,
        conversation: Conversation,
        channel: ChannelPlatform,
        engagement_signal: str,  # response, click, purchase, ignore
        db: AsyncSession,
    ) -> None:
        """Track channel engagement for learning."""
        
        if not conversation.extra_data:
            conversation.extra_data = {}
        
        # Initialize channel history if needed
        if "channel_interactions" not in conversation.extra_data:
            conversation.extra_data["channel_interactions"] = {}
        
        channel_key = channel.value
        if channel_key not in conversation.extra_data["channel_interactions"]:
            conversation.extra_data["channel_interactions"][channel_key] = {
                "total": 0,
                "responses": 0,
                "clicks": 0,
                "purchases": 0,
                "ignores": 0,
            }
        
        # Update counts
        history = conversation.extra_data["channel_interactions"][channel_key]
        history["total"] += 1
        history[f"{engagement_signal}s"] = history.get(f"{engagement_signal}s", 0) + 1
        
        # Update timestamp
        conversation.extra_data["last_channel_interaction"] = channel_key
        conversation.extra_data["last_interaction_time"] = datetime.now(timezone.utc).isoformat()
        
        await db.commit()
```

---

## Compliance Module

### File: `backend/app/core/channels/compliance.py` (excerpt)

```python
"""Compliance Management — GDPR, CCPA, CAN-SPAM, Telemarketing."""

import logging
from enum import Enum
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.channels.models import Conversation, ChannelPlatform

logger = logging.getLogger(__name__)


class ConsentType(str, Enum):
    MARKETING = "marketing"
    TRANSACTIONAL = "transactional"
    NEWSLETTER = "newsletter"


class ComplianceRegion(str, Enum):
    EU = "eu"  # GDPR
    US_CA = "us_ca"  # CCPA
    US_OTHER = "us_other"  # CAN-SPAM, TCPA
    GLOBAL = "global"


class ComplianceManager:
    """Enforce messaging compliance regulations."""
    
    def __init__(self, db: AsyncSession, region: ComplianceRegion = ComplianceRegion.GLOBAL):
        self.db = db
        self.region = region
    
    async def can_send(
        self,
        conversation: Conversation,
        channel: ChannelPlatform,
        message_type: str = "promotional",  # transactional|promotional|newsletter
    ) -> Tuple[bool, Optional[str]]:
        """Check if sending is legally compliant."""
        
        # Transactional messages always allowed
        if message_type == "transactional":
            return True, None
        
        # Check consent
        has_consent = await self._check_consent(
            conversation,
            channel,
            message_type,
        )
        
        if not has_consent:
            return False, f"No consent for {message_type} on {channel.value}"
        
        # Check region-specific rules
        if self.region == ComplianceRegion.EU:
            gdpr_ok, reason = await self._check_gdpr(conversation)
            if not gdpr_ok:
                return False, reason
        
        elif self.region == ComplianceRegion.US_CA:
            ccpa_ok, reason = await self._check_ccpa(conversation)
            if not ccpa_ok:
                return False, reason
        
        # Check universal rules
        can_spam_ok, issues = await self._check_can_spam(
            conversation,
            channel,
            message_type,
        )
        if not can_spam_ok:
            return False, f"CAN-SPAM violation: {issues[0]}"
        
        return True, None
    
    async def _check_consent(
        self,
        conversation: Conversation,
        channel: ChannelPlatform,
        message_type: str,
    ) -> bool:
        """Check if contact has given consent."""
        
        extra = conversation.extra_data or {}
        
        # Check channel + message type consent
        consent_key = f"consent_{channel.value}_{message_type}"
        
        if consent_key not in extra:
            return False
        
        consent_record = extra[consent_key]
        
        # Check if consent is still valid (not revoked)
        if consent_record.get("status") == "revoked":
            return False
        
        # Check GDPR data retention (max 5 years)
        if self.region == ComplianceRegion.EU:
            consent_date = consent_record.get("consented_at")
            if consent_date:
                cutoff = datetime.now(timezone.utc) - timedelta(days=5*365)
                if datetime.fromisoformat(consent_date) < cutoff:
                    return False  # Consent too old
        
        return True
    
    async def _check_gdpr(self, conversation: Conversation) -> Tuple[bool, Optional[str]]:
        """Validate GDPR requirements (EU residents)."""
        
        extra = conversation.extra_data or {}
        
        # Must have explicit consent for non-transactional
        if not extra.get("gdpr_consent"):
            return False, "GDPR consent required"
        
        # Must respect right-to-be-forgotten
        if extra.get("deletion_requested"):
            return False, "Right-to-be-forgotten: cannot contact"
        
        # Data processing agreement required for processors
        # (assume agreed for this implementation)
        
        return True, None
    
    async def _check_ccpa(self, conversation: Conversation) -> Tuple[bool, Optional[str]]:
        """Validate CCPA requirements (California residents)."""
        
        extra = conversation.extra_data or {}
        
        # Check do-not-sell preference
        if extra.get("ccpa_do_not_sell"):
            return False, "CCPA do-not-sell preference"
        
        # Opt-in required for promotional
        if not extra.get("ccpa_opt_in"):
            return False, "CCPA opt-in required"
        
        return True, None
    
    async def _check_can_spam(
        self,
        conversation: Conversation,
        channel: ChannelPlatform,
        message_type: str,
    ) -> Tuple[bool, list[str]]:
        """Validate CAN-SPAM requirements (US emails)."""
        
        if channel != ChannelPlatform.EMAIL:
            return True, []
        
        issues = []
        
        # TODO: Check for unsubscribe link
        # TODO: Check for physical address
        # TODO: Check for clear subject line
        
        return len(issues) == 0, issues
    
    async def process_unsubscribe(
        self,
        conversation: Conversation,
        channel: ChannelPlatform,
        message_type: str,
    ) -> None:
        """Handle unsubscribe request."""
        
        if not conversation.extra_data:
            conversation.extra_data = {}
        
        consent_key = f"consent_{channel.value}_{message_type}"
        conversation.extra_data[consent_key] = {
            "status": "revoked",
            "revoked_at": datetime.now(timezone.utc).isoformat(),
            "reason": "user_unsubscribe",
        }
        
        await self.db.commit()
        logger.info(f"Unsubscribed: {conversation.id} from {channel.value}/{message_type}")
```

---

## Database Schema

### New Tables to Create

```sql
-- Message Queue Table
CREATE TABLE message_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    channel_id UUID NOT NULL REFERENCES channel_connections(id) ON DELETE SET NULL,
    recipient VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(50) DEFAULT 'text',
    
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending|sending|sent|failed|dead_letter
    priority INTEGER DEFAULT 50,
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    error_message TEXT,
    external_message_id VARCHAR(255),
    
    queued_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    sent_at TIMESTAMP WITH TIME ZONE,
    delivered_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    
    metadata JSONB DEFAULT '{}',
    
    INDEX idx_status (status),
    INDEX idx_business_status (business_id, status),
    INDEX idx_queued_at (queued_at),
);

-- Message Templates Table
CREATE TABLE message_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    template_type VARCHAR(50) NOT NULL,  -- sales, support, logistics, etc.
    channels VARCHAR(50)[] NOT NULL,  -- Array of channel platforms
    
    content JSONB NOT NULL,  -- {whatsapp: "...", email: "...", sms: "..."}
    required_variables VARCHAR(255)[] DEFAULT '{}',
    optional_variables VARCHAR(255)[] DEFAULT '{}',
    
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_business_active (business_id, is_active),
);

-- Consent Records Table
CREATE TABLE consent_records (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    channel VARCHAR(50) NOT NULL,
    message_type VARCHAR(50) NOT NULL,  -- marketing|transactional|newsletter
    
    status VARCHAR(50) NOT NULL,  -- given|revoked
    consented_at TIMESTAMP WITH TIME ZONE,
    revoked_at TIMESTAMP WITH TIME ZONE,
    
    consent_ip VARCHAR(45),
    consent_user_agent TEXT,
    consent_source VARCHAR(100),  -- web_form|email_link|api|etc
    
    INDEX idx_conversation_channel (conversation_id, channel, message_type),
);

-- Dead Letter Queue
CREATE TABLE dead_letter_queue (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    business_id UUID NOT NULL REFERENCES businesses(id),
    original_message_id UUID REFERENCES message_queue(id),
    
    reason TEXT NOT NULL,
    error_details JSONB,
    
    flagged_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMP WITH TIME ZONE,
    
    INDEX idx_business_resolved (business_id, resolved),
);
```

---

## API Endpoints

### New/Modified Endpoints

```python
# api/v1/messages.py (NEW FILE)

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

router = APIRouter(prefix="/messages", tags=["messages"])

@router.post("/{conversation_id}/send")
async def send_message(
    conversation_id: UUID,
    content: str,
    channel_id: UUID = None,  # Optional; if not provided, router selects
    fallback_channels: list[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Send message to contact via specified or auto-selected channel."""
    # Validate conversation ownership
    # Check compliance (GDPR/CCPA/CAN-SPAM)
    # Route to best channel if not specified
    # Enqueue message
    # Return {message_id, status, channel_used}

@router.get("/{message_id}/status")
async def get_message_status(
    message_id: UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get delivery status of queued message."""
    # Return {status, sent_at, delivered_at, error}

@router.post("/{conversation_id}/templates/{template_id}/send")
async def send_templated_message(
    conversation_id: UUID,
    template_id: UUID,
    context: dict,  # Template variables
    db: AsyncSession = Depends(get_db),
):
    """Send templated message with automatic channel selection."""
    # Load template
    # Render with context
    # Check compliance
    # Send

@router.post("/{conversation_id}/unsubscribe")
async def unsubscribe(
    conversation_id: UUID,
    channel: str,
    message_type: str = "promotional",
    db: AsyncSession = Depends(get_db),
):
    """Record unsubscribe request."""
    # Update consent record
    # Return confirmation

@router.get("/queue/stats")
async def get_queue_stats(db: AsyncSession = Depends(get_db)):
    """Get real-time queue statistics."""
    # Return {pending, oldest, by_platform}

@router.get("/dead-letter")
async def list_dead_letters(
    business_id: UUID = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """List dead-lettered messages for investigation."""
    # Return paginated dead letter queue
```

---

## Error Handling

### Retry Strategy

```python
class RetryPolicy(Enum):
    AGGRESSIVE = {
        "max_attempts": 5,
        "backoff_base": 0.5,  # seconds
        "backoff_multiplier": 1.5,
        "max_wait": 30,
    }
    DEFAULT = {
        "max_attempts": 3,
        "backoff_base": 1.0,
        "backoff_multiplier": 2.0,
        "max_wait": 30,
    }
    CONSERVATIVE = {
        "max_attempts": 1,
        "backoff_base": 5.0,
        "backoff_multiplier": 2.0,
        "max_wait": 30,
    }

def calculate_retry_delay(attempt: int, policy: RetryPolicy) -> float:
    """Calculate exponential backoff delay."""
    p = policy.value
    delay = p["backoff_base"] * (p["backoff_multiplier"] ** (attempt - 1))
    return min(delay, p["max_wait"])
```

### Fallback Strategy

```python
CHANNEL_FALLBACK_CHAINS = {
    ChannelPlatform.WHATSAPP: [
        ChannelPlatform.SMS,
        ChannelPlatform.EMAIL,
    ],
    ChannelPlatform.SMS: [
        ChannelPlatform.EMAIL,
        ChannelPlatform.WHATSAPP,
    ],
    ChannelPlatform.EMAIL: [
        ChannelPlatform.SMS,
        ChannelPlatform.WHATSAPP,
    ],
}
```

---

## Code Examples

### Example 1: Send Message via Router

```python
async def send_automated_follow_up(
    conversation: Conversation,
    business_id: UUID,
    db: AsyncSession,
):
    """Send follow-up message via best channel."""
    
    from app.core.channels.channel_router import ChannelRouter
    from app.core.channels.template_engine import TemplateEngine
    from app.core.channels.message_queue import MessageQueue
    from app.core.channels.compliance import ComplianceManager
    
    # Initialize components
    router = ChannelRouter()
    template_engine = TemplateEngine()
    queue = MessageQueue(db)
    compliance = ComplianceManager(db)
    
    # 1. Select channel
    channel = await router.select_channel(
        conversation,
        business_id,
        db,
        message_type="follow_up",
    )
    
    if not channel:
        logger.error("No channel available")
        return
    
    # 2. Check compliance
    can_send, reason = await compliance.can_send(
        conversation,
        channel.platform,
        "promotional",
    )
    
    if not can_send:
        logger.warning(f"Cannot send: {reason}")
        return
    
    # 3. Render template
    template_content = TEMPLATES["sales/inquiry_follow_up"]["content"][channel.platform.value]
    message_content = await template_engine.render(
        template_content,
        context={
            "name": conversation.lead_name,
            "product_name": "Amazing Product",
            "discount": 20,
        },
        channel=channel.platform,
    )
    
    # 4. Enqueue message
    message_id = await queue.enqueue(
        channel=channel,
        recipient=conversation.lead_phone or conversation.lead_email,
        content=message_content,
        priority=75,  # HIGH
        fallback_channels=[ChannelPlatform.SMS, ChannelPlatform.EMAIL],
        metadata={
            "conversation_id": conversation.id,
            "template": "inquiry_follow_up",
        },
    )
    
    logger.info(f"Message queued: {message_id}")
    return message_id
```

### Example 2: Integration with Automation Engine

```python
# In automation_engine.py:

async def handle_send_follow_ups(payload: dict) -> dict:
    """Handler for scheduled follow-up sending."""
    
    from app.core.channels.message_queue import MessageQueue
    
    db = get_db()
    queue = MessageQueue(db)
    
    # Get pending conversations
    result = await db.execute(
        select(Conversation).where(
            Conversation.business_id == payload["business_id"],
            Conversation.status == ConversationStatus.ACTIVE,
        )
    )
    conversations = result.scalars().all()
    
    sent_count = 0
    for conversation in conversations:
        try:
            message_id = await send_automated_follow_up(
                conversation,
                payload["business_id"],
                db,
            )
            if message_id:
                sent_count += 1
        except Exception as e:
            logger.error(f"Error sending follow-up: {e}")
    
    # Process queue
    queue_stats = await queue.process_pending(batch_size=100)
    
    return {
        "status": "success",
        "conversations_processed": len(conversations),
        "messages_sent": sent_count,
        "queue_stats": queue_stats,
    }

# Register with automation engine:
engine.register_handler(
    JobType.SEND_FOLLOW_UPS,
    handle_send_follow_ups,
)

# Schedule
await engine.add_recurring_task(
    name="Send follow-ups",
    job_type=JobType.SEND_FOLLOW_UPS,
    priority=Priority.HIGH,
    schedule="0 9,14,18 * * *",  # 9am, 2pm, 6pm
    payload={"business_id": business_id},
)
```

---

## Testing Examples

### Unit Test: SMS Connector

```python
import pytest
from app.domains.channels.connectors.sms import SMSConnector

@pytest.mark.asyncio
async def test_sms_send_twilio():
    """Test SMS send via Twilio."""
    
    credentials = {
        "provider": "twilio",
        "account_sid": "ACxxx",
        "auth_token": "token",
        "from_number": "+15551234567",
    }
    
    connector = SMSConnector(credentials, {})
    
    result = await connector.send_message(
        "+14155552671",
        "Hello, World!",
    )
    
    assert result["status"] == "sent"
    assert "message_id" in result

@pytest.mark.asyncio
async def test_sms_invalid_phone():
    """Test SMS with invalid phone number."""
    
    connector = SMSConnector({...}, {})
    
    with pytest.raises(ValueError):
        await connector.send_message(
            "1234567890",  # Invalid format
            "Hello",
        )
```

---

## Monitoring & Observability

### Key Metrics to Track

```python
METRICS = {
    "message_queue_size": gauge,  # Current pending messages
    "message_send_latency": histogram,  # seconds from queue to delivery
    "message_delivery_rate": counter,  # % successful deliveries
    "channel_usage": counter,  # Messages by channel
    "dead_letter_rate": gauge,  # % messages moving to DLQ
    "retry_rate": gauge,  # % messages requiring retry
    "compliance_rejections": counter,  # Messages blocked by compliance
    "template_render_errors": counter,  # Template failures
}
```

### Example Monitoring Query

```python
async def get_dashboard_stats(db: AsyncSession) -> dict:
    """Get real-time stats for monitoring dashboard."""
    
    # Pending messages by platform
    pending = await db.execute(
        select(
            ChannelConnection.platform,
            func.count(MessageQueue.id),
        ).join(MessageQueue).where(
            MessageQueue.status == "pending"
        ).group_by(ChannelConnection.platform)
    )
    
    # Delivery rate (last 24h)
    delivered = await db.execute(
        select(func.count(Message.id)).where(
            Message.direction == MessageDirection.OUTBOUND,
            Message.status == MessageStatus.DELIVERED,
            Message.created_at >= datetime.now(timezone.utc) - timedelta(days=1),
        )
    )
    
    total = await db.execute(
        select(func.count(Message.id)).where(
            Message.direction == MessageDirection.OUTBOUND,
            Message.created_at >= datetime.now(timezone.utc) - timedelta(days=1),
        )
    )
    
    delivery_rate = delivered.scalar() / total.scalar() if total.scalar() else 0
    
    return {
        "pending_by_platform": dict(pending),
        "delivery_rate_24h": delivery_rate,
        "queue_size": await queue.get_queue_stats(),
    }
```

---

## Next Steps

1. **Create SMS Connector** — Start here, foundation for other modules
2. **Implement Message Queue** — Core reliability infrastructure
3. **Build Template Engine** — Personalization capability
4. **Add Channel Router** — Optimization logic
5. **Implement Compliance** — Legal requirements
6. **Write Tests** — Validation suite
7. **Deploy & Monitor** — Production readiness

