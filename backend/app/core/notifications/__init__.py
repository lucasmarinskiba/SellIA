"""Notifications module — Email, SMS, push notifications."""

from .email_service import (
    EmailService,
    EmailProvider,
    EmailTemplate,
    EmailMessage,
    EmailRecipient,
)

from .sms_service import (
    SMSService,
    SMSProvider,
    SMSTemplate,
    SMSMessage,
)

__all__ = [
    "EmailService",
    "EmailProvider",
    "EmailTemplate",
    "EmailMessage",
    "EmailRecipient",
    "SMSService",
    "SMSProvider",
    "SMSTemplate",
    "SMSMessage",
]
