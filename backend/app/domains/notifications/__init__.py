"""Notifications & alerts domain."""

from app.domains.notifications.notification_models import (
    NotificationPreference,
    NotificationLog,
    AlertTemplate,
    NotificationMetrics,
    NotificationChannel,
    AlertType,
    AlertPriority,
)
from app.domains.alerts.models import AlertRule
from app.domains.notifications.notification_service import NotificationService

__all__ = [
    "NotificationPreference",
    "AlertRule",
    "NotificationLog",
    "AlertTemplate",
    "NotificationMetrics",
    "NotificationChannel",
    "AlertType",
    "AlertPriority",
    "NotificationService",
]
