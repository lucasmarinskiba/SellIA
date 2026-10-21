"""Notifications & alerts domain."""

from app.domains.alerts.models import AlertRule
from app.domains.notifications.notification_models import (
    AlertPriority,
    AlertTemplate,
    AlertType,
    NotificationChannel,
    NotificationLog,
    NotificationMetrics,
    NotificationPreference,
)
from app.domains.notifications.notification_service import NotificationService

__all__ = [
    "AlertPriority",
    "AlertRule",
    "AlertTemplate",
    "AlertType",
    "NotificationChannel",
    "NotificationLog",
    "NotificationMetrics",
    "NotificationPreference",
    "NotificationService",
]
