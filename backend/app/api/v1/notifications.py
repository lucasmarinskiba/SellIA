"""Notifications API endpoints."""

from uuid import UUID
from typing import Optional, List, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.domains.notifications.notification_service import NotificationService

router = APIRouter(prefix="/api/v1", tags=["notifications"])


class NotificationPreferenceRequest(BaseModel):
    email_enabled: Optional[bool] = None
    sms_enabled: Optional[bool] = None
    whatsapp_enabled: Optional[bool] = None
    in_app_enabled: Optional[bool] = None
    slack_enabled: Optional[bool] = None
    quiet_hours_start: Optional[str] = None
    quiet_hours_end: Optional[str] = None


class AlertRuleRequest(BaseModel):
    name: str
    alert_type: str
    condition_json: Dict
    channels: List[str]
    priority: Optional[str] = "medium"


class AlertTriggerRequest(BaseModel):
    alert_type: str
    alert_title: str
    alert_message: str
    priority: Optional[str] = "medium"
    target_user_ids: Optional[List[UUID]] = None


@router.post("/users/{user_id}/notifications/preferences")
def set_notification_preferences(
    user_id: UUID,
    business_id: UUID = Query(...),
    request: NotificationPreferenceRequest = None,
    db: Session = Depends(get_db)
):
    """Set user notification preferences."""
    preferences = request.dict(exclude_none=True) if request else {}
    return NotificationService.set_notification_preferences(
        user_id=user_id,
        business_id=business_id,
        preferences=preferences,
        db=db
    )


@router.get("/users/{user_id}/notifications/preferences")
def get_notification_preferences(
    user_id: UUID,
    business_id: UUID = Query(...),
    db: Session = Depends(get_db)
):
    """Get user notification preferences."""
    return NotificationService.get_notification_preferences(
        user_id=user_id,
        business_id=business_id,
        db=db
    )


@router.post("/businesses/{business_id}/alerts/rules")
def create_alert_rule(
    business_id: UUID,
    request: AlertRuleRequest,
    db: Session = Depends(get_db)
):
    """Create alert rule."""
    return NotificationService.create_alert_rule(
        business_id=business_id,
        name=request.name,
        alert_type=request.alert_type,
        condition_json=request.condition_json,
        channels=request.channels,
        priority=request.priority,
        db=db
    )


@router.get("/businesses/{business_id}/alerts/rules")
def get_alert_rules(
    business_id: UUID,
    enabled_only: bool = Query(True),
    db: Session = Depends(get_db)
):
    """Get alert rules."""
    return NotificationService.get_alert_rules(
        business_id=business_id,
        enabled_only=enabled_only,
        db=db
    )


@router.patch("/alerts/{rule_id}")
def update_alert_rule(
    rule_id: UUID,
    updates: Dict,
    db: Session = Depends(get_db)
):
    """Update alert rule."""
    return NotificationService.update_alert_rule(
        rule_id=rule_id,
        updates=updates,
        db=db
    )


@router.post("/businesses/{business_id}/alerts/trigger")
def trigger_alert(
    business_id: UUID,
    request: AlertTriggerRequest,
    db: Session = Depends(get_db)
):
    """Trigger alert."""
    return NotificationService.trigger_alert(
        business_id=business_id,
        alert_type=request.alert_type,
        alert_title=request.alert_title,
        alert_message=request.alert_message,
        priority=request.priority,
        target_user_ids=request.target_user_ids,
        db=db
    )


@router.get("/users/{user_id}/notifications/history")
def get_notification_history(
    user_id: UUID,
    business_id: UUID = Query(...),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get notification history."""
    return NotificationService.get_notification_history(
        user_id=user_id,
        business_id=business_id,
        days=days,
        db=db
    )


@router.post("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: UUID,
    action: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Mark notification as read."""
    return NotificationService.mark_as_read(
        notification_id=notification_id,
        action=action,
        db=db
    )


@router.get("/businesses/{business_id}/notifications/metrics")
def get_notification_metrics(
    business_id: UUID,
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db)
):
    """Get notification metrics."""
    return NotificationService.get_notification_metrics(
        business_id=business_id,
        days=days,
        db=db
    )
