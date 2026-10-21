"""Notifications module — Email, SMS, push notifications."""

from .email_service import (
    EmailMessage,
    EmailProvider,
    EmailRecipient,
    EmailService,
    EmailTemplate,
)
from .sms_service import (
    SMSMessage,
    SMSProvider,
    SMSService,
    SMSTemplate,
)

__all__ = [
    "EmailMessage",
    "EmailProvider",
    "EmailRecipient",
    "EmailService",
    "EmailTemplate",
    "SMSMessage",
    "SMSProvider",
    "SMSService",
    "SMSTemplate",
]
