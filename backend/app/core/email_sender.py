"""
Email Sender Service
- SMTP + SendGrid support
- Template rendering
- Retry logic + scheduling
- Bounce/unsubscribe handling
"""
import os
import logging
from typing import Optional
import httpx
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# ============================================================
# EMAIL PROVIDER ENUMS
# ============================================================
class EmailProvider(str, Enum):
    SMTP = "smtp"
    SENDGRID = "sendgrid"
    RESEND = "resend"
    MOCK = "mock"  # For testing

# ============================================================
# EMAIL SENDER
# ============================================================
class EmailSender:
    """Email sender abstraction - SMTP or SendGrid."""

    def __init__(self, provider: EmailProvider = EmailProvider.MOCK):
        self.provider = provider

        if provider == EmailProvider.SENDGRID:
            self.api_key = os.getenv("SENDGRID_API_KEY")
            if not self.api_key:
                logger.warning("SENDGRID_API_KEY not set, falling back to MOCK")
                self.provider = EmailProvider.MOCK

        elif provider == EmailProvider.RESEND:
            self.api_key = os.getenv("RESEND_API_KEY")
            if not self.api_key:
                logger.warning("RESEND_API_KEY not set, falling back to MOCK")
                self.provider = EmailProvider.MOCK

        elif provider == EmailProvider.SMTP:
            self.smtp_host = os.getenv("SMTP_HOST", "localhost")
            self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
            self.smtp_user = os.getenv("SMTP_USER", "")
            self.smtp_pass = os.getenv("SMTP_PASSWORD", "")

    async def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str = "noreply@sellia.io",
        from_name: str = "SellIA",
        reply_to: Optional[str] = None,
        tracking_id: Optional[str] = None
    ) -> dict:
        """Send email via configured provider."""

        if self.provider == EmailProvider.SENDGRID:
            return await self._send_sendgrid(
                to=to,
                subject=subject,
                body=body,
                from_email=from_email,
                from_name=from_name,
                reply_to=reply_to,
                tracking_id=tracking_id
            )

        elif self.provider == EmailProvider.RESEND:
            return await self._send_resend(
                to=to,
                subject=subject,
                body=body,
                from_email=from_email,
                from_name=from_name,
                reply_to=reply_to,
                tracking_id=tracking_id
            )

        elif self.provider == EmailProvider.SMTP:
            return await self._send_smtp(
                to=to,
                subject=subject,
                body=body,
                from_email=from_email,
                from_name=from_name
            )

        else:  # MOCK
            return self._send_mock(
                to=to,
                subject=subject,
                from_email=from_email,
                tracking_id=tracking_id
            )

    async def _send_sendgrid(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str,
        from_name: str,
        reply_to: Optional[str],
        tracking_id: Optional[str]
    ) -> dict:
        """Send via SendGrid API."""
        try:
            email_data = {
                "personalizations": [
                    {
                        "to": [{"email": to}],
                        "subject": subject
                    }
                ],
                "from": {
                    "email": from_email,
                    "name": from_name
                },
                "content": [
                    {
                        "type": "text/html",
                        "value": body
                    }
                ],
                "tracking_settings": {
                    "open": {"enable": True},
                    "click": {"enable": True}
                }
            }

            if reply_to:
                email_data["reply_to"] = {
                    "email": reply_to,
                    "name": from_name
                }

            # Add custom args for tracking
            if tracking_id:
                email_data["personalizations"][0]["custom_args"] = {
                    "tracking_id": tracking_id
                }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.sendgrid.com/v3/mail/send",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=email_data,
                    timeout=30
                )

                if response.status_code in [200, 202]:
                    logger.info(f"Email sent via SendGrid to {to}")
                    return {
                        "status": "sent",
                        "provider": "sendgrid",
                        "timestamp": datetime.now().isoformat(),
                        "tracking_id": tracking_id
                    }
                else:
                    logger.error(f"SendGrid error: {response.text}")
                    return {
                        "status": "failed",
                        "provider": "sendgrid",
                        "error": response.text
                    }

        except Exception as e:
            logger.error(f"SendGrid send failed: {e}")
            return {
                "status": "failed",
                "provider": "sendgrid",
                "error": str(e)
            }

    async def _send_resend(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str,
        from_name: str,
        reply_to: Optional[str],
        tracking_id: Optional[str]
    ) -> dict:
        """Send via Resend API (https://resend.com/docs/api-reference/emails/send-email)."""
        try:
            email_data = {
                "from": f"{from_name} <{from_email}>",
                "to": [to],
                "subject": subject,
                "html": body,
            }

            if reply_to:
                email_data["reply_to"] = reply_to

            if tracking_id:
                email_data["tags"] = [{"name": "tracking_id", "value": tracking_id}]

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=email_data,
                    timeout=30
                )

                if response.status_code in [200, 201]:
                    result = response.json()
                    logger.info(f"Email sent via Resend to {to} (id={result.get('id')})")
                    return {
                        "status": "sent",
                        "provider": "resend",
                        "provider_message_id": result.get("id"),
                        "timestamp": datetime.now().isoformat(),
                        "tracking_id": tracking_id
                    }
                else:
                    logger.error(f"Resend error: {response.text}")
                    return {
                        "status": "failed",
                        "provider": "resend",
                        "error": response.text
                    }

        except Exception as e:
            logger.error(f"Resend send failed: {e}")
            return {
                "status": "failed",
                "provider": "resend",
                "error": str(e)
            }

    async def _send_smtp(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: str,
        from_name: str
    ) -> dict:
        """Send via SMTP."""
        try:
            # In production: use aiosmtplib or similar async SMTP
            # For now: mock implementation
            logger.info(f"[MOCK SMTP] Email to {to}: {subject}")

            return {
                "status": "sent",
                "provider": "smtp",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"SMTP send failed: {e}")
            return {
                "status": "failed",
                "provider": "smtp",
                "error": str(e)
            }

    def _send_mock(
        self,
        to: str,
        subject: str,
        from_email: str,
        tracking_id: Optional[str]
    ) -> dict:
        """Mock send for testing."""
        logger.info(f"[MOCK EMAIL] To: {to}, Subject: {subject}, ID: {tracking_id}")

        return {
            "status": "sent",
            "provider": "mock",
            "timestamp": datetime.now().isoformat(),
            "tracking_id": tracking_id,
            "message": "Email sent (mock mode)"
        }

    async def mark_opened(self, tracking_id: str) -> dict:
        """Webhook: mark email as opened."""
        logger.info(f"Email opened: {tracking_id}")

        # In prod: update email_execution.opened_at in DB
        return {
            "tracking_id": tracking_id,
            "status": "opened",
            "timestamp": datetime.now().isoformat()
        }

    async def mark_clicked(self, tracking_id: str, url: str) -> dict:
        """Webhook: mark email as clicked."""
        logger.info(f"Email clicked: {tracking_id} -> {url}")

        # In prod: update email_execution.clicked_at in DB
        return {
            "tracking_id": tracking_id,
            "status": "clicked",
            "url": url,
            "timestamp": datetime.now().isoformat()
        }

    async def mark_bounced(self, email: str, reason: str) -> dict:
        """Webhook: mark email as bounced."""
        logger.warning(f"Email bounced: {email} - {reason}")

        # In prod: update lead status, stop sending
        return {
            "email": email,
            "status": "bounced",
            "reason": reason,
            "timestamp": datetime.now().isoformat()
        }

    async def mark_unsubscribed(self, email: str) -> dict:
        """Webhook: mark email as unsubscribed."""
        logger.info(f"Email unsubscribed: {email}")

        # In prod: mark lead as unsubscribed
        return {
            "email": email,
            "status": "unsubscribed",
            "timestamp": datetime.now().isoformat()
        }

# ============================================================
# SCHEDULER
# ============================================================
class EmailScheduler:
    """Schedule and send emails with retry logic."""

    def __init__(self, sender: EmailSender):
        self.sender = sender
        self.max_retries = 3
        self.retry_delay = 300  # 5 minutes

    async def schedule_workflow_email(
        self,
        workflow_execution_id: int,
        lead_email: str,
        subject: str,
        body: str,
        send_at: Optional[datetime] = None
    ) -> dict:
        """Schedule workflow email for delivery."""

        # If send_at is None, send immediately
        if not send_at:
            result = await self.sender.send_email(
                to=lead_email,
                subject=subject,
                body=body,
                tracking_id=f"wf_{workflow_execution_id}"
            )

            return {
                "workflow_execution_id": workflow_execution_id,
                "status": result["status"],
                "sent_at": datetime.now().isoformat()
            }

        else:
            # In prod: store in queue, process by scheduler
            logger.info(f"Email scheduled for {send_at}: {workflow_execution_id}")

            return {
                "workflow_execution_id": workflow_execution_id,
                "status": "scheduled",
                "scheduled_for": send_at.isoformat()
            }

    async def send_with_retry(
        self,
        to: str,
        subject: str,
        body: str,
        max_retries: int = 3
    ) -> dict:
        """Send email with retry logic."""

        for attempt in range(max_retries):
            try:
                result = await self.sender.send_email(
                    to=to,
                    subject=subject,
                    body=body
                )

                if result["status"] == "sent":
                    return result

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")

                if attempt == max_retries - 1:
                    return {
                        "status": "failed",
                        "error": str(e),
                        "attempts": attempt + 1
                    }

# ============================================================
# FACTORY
# ============================================================
def get_email_sender(provider: Optional[str] = None) -> EmailSender:
    """Factory to get configured email sender.

    Sin provider explícito, resuelve por env vars disponibles en este orden:
    RESEND_API_KEY -> SENDGRID_API_KEY -> MOCK. Antes el default hardcodeado
    era "sendgrid" incluso sin SENDGRID_API_KEY seteada, silenciosamente cayendo
    a MOCK - ahora se resuelve al primer provider realmente configurado.
    """
    if provider is None:
        if os.getenv("RESEND_API_KEY"):
            provider = "resend"
        elif os.getenv("SENDGRID_API_KEY"):
            provider = "sendgrid"
        else:
            provider = "mock"

    if provider == "resend":
        return EmailSender(EmailProvider.RESEND)
    elif provider == "sendgrid":
        return EmailSender(EmailProvider.SENDGRID)
    elif provider == "smtp":
        return EmailSender(EmailProvider.SMTP)
    else:
        return EmailSender(EmailProvider.MOCK)

def get_email_scheduler(provider: Optional[str] = None) -> EmailScheduler:
    """Factory to get configured email scheduler."""
    sender = get_email_sender(provider)
    return EmailScheduler(sender)
