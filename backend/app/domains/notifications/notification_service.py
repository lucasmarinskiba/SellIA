"""Notification & alert service."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional, List, Dict
import json

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.notifications.notification_models import (
    NotificationPreference, AlertRule, NotificationLog, AlertTemplate, NotificationMetrics,
    AlertType, NotificationChannel, AlertPriority
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Manage notifications and alerts."""

    @staticmethod
    def set_notification_preferences(
        user_id: UUID,
        business_id: UUID,
        preferences: dict,
        db: Session = None
    ) -> dict:
        """Set user notification preferences."""
        if not db:
            raise ValueError("Database session required")

        pref = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id,
            NotificationPreference.business_id == business_id
        ).first()

        if not pref:
            pref = NotificationPreference(
                user_id=user_id,
                business_id=business_id
            )

        # Update preferences
        for key, value in preferences.items():
            if hasattr(pref, key):
                setattr(pref, key, value)

        db.add(pref)
        db.commit()
        db.refresh(pref)

        return {
            "user_id": str(user_id),
            "email_enabled": pref.email_enabled,
            "sms_enabled": pref.sms_enabled,
            "whatsapp_enabled": pref.whatsapp_enabled,
            "in_app_enabled": pref.in_app_enabled,
            "quiet_hours_start": pref.quiet_hours_start,
            "quiet_hours_end": pref.quiet_hours_end,
        }

    @staticmethod
    def get_notification_preferences(
        user_id: UUID,
        business_id: UUID,
        db: Session = None
    ) -> dict:
        """Get user notification preferences."""
        if not db:
            raise ValueError("Database session required")

        pref = db.query(NotificationPreference).filter(
            NotificationPreference.user_id == user_id,
            NotificationPreference.business_id == business_id
        ).first()

        if not pref:
            return {"message": "No preferences found"}

        return {
            "email_enabled": pref.email_enabled,
            "sms_enabled": pref.sms_enabled,
            "whatsapp_enabled": pref.whatsapp_enabled,
            "in_app_enabled": pref.in_app_enabled,
            "slack_enabled": pref.slack_enabled,
            "quiet_hours_start": pref.quiet_hours_start,
            "quiet_hours_end": pref.quiet_hours_end,
        }

    @staticmethod
    def create_alert_rule(
        business_id: UUID,
        name: str,
        alert_type: str,
        condition_json: dict,
        channels: List[str],
        priority: str = AlertPriority.MEDIUM.value,
        enabled: bool = True,
        db: Session = None
    ) -> dict:
        """Create alert rule."""
        if not db:
            raise ValueError("Database session required")

        rule = AlertRule(
            business_id=business_id,
            name=name,
            alert_type=alert_type,
            condition_json=condition_json,
            channels=channels,
            priority=priority,
            enabled=enabled
        )

        db.add(rule)
        db.commit()
        db.refresh(rule)

        logger.info(f"Alert rule created: {name} ({alert_type})")

        return {
            "rule_id": str(rule.id),
            "name": name,
            "alert_type": alert_type,
            "priority": priority,
            "enabled": enabled
        }

    @staticmethod
    def update_alert_rule(
        rule_id: UUID,
        updates: dict,
        db: Session = None
    ) -> dict:
        """Update alert rule."""
        if not db:
            raise ValueError("Database session required")

        rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
        if not rule:
            raise ValueError("Rule not found")

        for key, value in updates.items():
            if hasattr(rule, key):
                setattr(rule, key, value)

        db.commit()
        db.refresh(rule)

        return {"rule_id": str(rule.id), "updated": True}

    @staticmethod
    def get_alert_rules(
        business_id: UUID,
        enabled_only: bool = True,
        db: Session = None
    ) -> List[dict]:
        """Get alert rules."""
        if not db:
            raise ValueError("Database session required")

        query = db.query(AlertRule).filter(AlertRule.business_id == business_id)
        if enabled_only:
            query = query.filter(AlertRule.enabled == True)

        rules = query.all()

        return [
            {
                "rule_id": str(r.id),
                "name": r.name,
                "alert_type": r.alert_type,
                "priority": r.priority,
                "channels": r.channels,
                "enabled": r.enabled,
                "last_triggered": r.last_triggered_at.isoformat() if r.last_triggered_at else None,
            }
            for r in rules
        ]

    @staticmethod
    def trigger_alert(
        business_id: UUID,
        alert_type: str,
        alert_title: str,
        alert_message: str,
        priority: str = AlertPriority.MEDIUM.value,
        target_user_ids: Optional[List[UUID]] = None,
        db: Session = None
    ) -> dict:
        """Trigger alert and send notifications."""
        if not db:
            raise ValueError("Database session required")

        # Get matching alert rules
        rules = db.query(AlertRule).filter(
            AlertRule.business_id == business_id,
            AlertRule.alert_type == alert_type,
            AlertRule.enabled == True
        ).all()

        if not rules:
            logger.warning(f"No alert rules found for {alert_type}")
            return {"triggered": False, "reason": "No matching rules"}

        # Get users to notify
        if not target_user_ids:
            target_user_ids = []

        notified_count = 0
        for rule in rules:
            for user_id in target_user_ids:
                # Check notification preferences
                pref = db.query(NotificationPreference).filter(
                    NotificationPreference.user_id == user_id,
                    NotificationPreference.business_id == business_id
                ).first()

                if not pref:
                    continue

                # Get channels from rule + user preferences
                for channel in rule.channels:
                    if not NotificationService._should_send(channel, pref):
                        continue

                    # Log notification
                    log = NotificationLog(
                        business_id=business_id,
                        user_id=user_id,
                        alert_rule_id=rule.id,
                        alert_type=alert_type,
                        alert_title=alert_title,
                        alert_message=alert_message,
                        priority=priority,
                        channel=channel,
                        recipient=NotificationService._get_recipient(user_id, channel, db),
                        delivery_status="pending"
                    )
                    db.add(log)
                    notified_count += 1

            # Update rule triggered timestamp
            rule.last_triggered_at = datetime.now(timezone.utc)
            rule.triggered_count_today += 1

        db.commit()
        logger.info(f"Alert triggered: {alert_type} - {notified_count} notifications queued")

        return {
            "alert_type": alert_type,
            "notifications_queued": notified_count
        }

    @staticmethod
    def _should_send(channel: str, pref: NotificationPreference) -> bool:
        """Check if should send on channel based on preferences."""
        channel_map = {
            NotificationChannel.EMAIL.value: pref.email_enabled,
            NotificationChannel.SMS.value: pref.sms_enabled,
            NotificationChannel.WHATSAPP.value: pref.whatsapp_enabled,
            NotificationChannel.IN_APP.value: pref.in_app_enabled,
            NotificationChannel.SLACK.value: pref.slack_enabled,
        }
        return channel_map.get(channel, False)

    @staticmethod
    def _get_recipient(user_id: UUID, channel: str, db: Session) -> str:
        """Get recipient address for channel."""
        # In production, fetch from users table
        return str(user_id)

    @staticmethod
    def get_notification_history(
        user_id: UUID,
        business_id: UUID,
        days: int = 30,
        db: Session = None
    ) -> List[dict]:
        """Get notification history."""
        if not db:
            raise ValueError("Database session required")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        logs = db.query(NotificationLog).filter(
            NotificationLog.user_id == user_id,
            NotificationLog.business_id == business_id,
            NotificationLog.created_at >= cutoff
        ).order_by(NotificationLog.created_at.desc()).all()

        return [
            {
                "notification_id": str(l.id),
                "alert_type": l.alert_type,
                "title": l.alert_title,
                "message": l.alert_message,
                "channel": l.channel,
                "priority": l.priority,
                "status": l.delivery_status,
                "read": l.read_at is not None,
                "timestamp": l.created_at.isoformat(),
            }
            for l in logs
        ]

    @staticmethod
    def mark_as_read(
        notification_id: UUID,
        action: Optional[str] = None,
        db: Session = None
    ) -> dict:
        """Mark notification as read."""
        if not db:
            raise ValueError("Database session required")

        log = db.query(NotificationLog).filter(NotificationLog.id == notification_id).first()
        if not log:
            raise ValueError("Notification not found")

        log.read_at = datetime.now(timezone.utc)
        if action:
            log.action_taken = action

        db.commit()
        return {"notification_id": str(notification_id), "marked_read": True}

    @staticmethod
    def get_notification_metrics(
        business_id: UUID,
        days: int = 30,
        db: Session = None
    ) -> dict:
        """Get notification metrics."""
        if not db:
            raise ValueError("Database session required")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        total = db.query(func.count(NotificationLog.id)).filter(
            NotificationLog.business_id == business_id,
            NotificationLog.created_at >= cutoff
        ).scalar() or 0

        successful = db.query(func.count(NotificationLog.id)).filter(
            NotificationLog.business_id == business_id,
            NotificationLog.delivery_status == "sent",
            NotificationLog.created_at >= cutoff
        ).scalar() or 0

        failed = db.query(func.count(NotificationLog.id)).filter(
            NotificationLog.business_id == business_id,
            NotificationLog.delivery_status == "failed",
            NotificationLog.created_at >= cutoff
        ).scalar() or 0

        read = db.query(func.count(NotificationLog.id)).filter(
            NotificationLog.business_id == business_id,
            NotificationLog.read_at.isnot(None),
            NotificationLog.created_at >= cutoff
        ).scalar() or 0

        # Channel breakdown
        channel_counts = db.query(
            NotificationLog.channel,
            func.count(NotificationLog.id)
        ).filter(
            NotificationLog.business_id == business_id,
            NotificationLog.created_at >= cutoff
        ).group_by(NotificationLog.channel).all()

        return {
            "total_notifications": total,
            "successful": successful,
            "failed": failed,
            "read_count": read,
            "read_rate_pct": round((read / max(total, 1)) * 100, 2),
            "channels": {channel: count for channel, count in channel_counts},
            "days": days
        }
