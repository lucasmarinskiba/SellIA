"""Audit logging for security events and data access.

Tracks:
- User authentication (login, logout, session)
- API calls (endpoint, method, status)
- Data access (who accessed what, when)
- Payment operations
- Settings changes
- Admin actions
"""

from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta, timezone
from enum import Enum
from sqlalchemy import Column, String, DateTime, JSON, Integer, Boolean, Text, Index
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
import json
import logging

Base = declarative_base()
logger = logging.getLogger(__name__)


class AuditEventType(str, Enum):
    """Audit event categories."""

    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    SESSION_CREATED = "session_created"
    SESSION_EXPIRED = "session_expired"
    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET = "password_reset"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_VERIFIED = "mfa_verified"
    MFA_FAILED = "mfa_failed"

    # API Access
    API_CALL = "api_call"
    API_RATE_LIMIT = "api_rate_limit"
    API_ERROR = "api_error"
    WEBHOOK_RECEIVED = "webhook_received"

    # Data Access
    DATA_READ = "data_read"
    DATA_CREATED = "data_created"
    DATA_UPDATED = "data_updated"
    DATA_DELETED = "data_deleted"
    DATA_EXPORTED = "data_exported"

    # Financial
    PAYMENT_INITIATED = "payment_initiated"
    PAYMENT_COMPLETED = "payment_completed"
    PAYMENT_FAILED = "payment_failed"
    REFUND_INITIATED = "refund_initiated"
    REFUND_COMPLETED = "refund_completed"
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"

    # Settings & Admin
    SETTINGS_CHANGED = "settings_changed"
    API_KEY_CREATED = "api_key_created"
    API_KEY_ROTATED = "api_key_rotated"
    API_KEY_REVOKED = "api_key_revoked"
    ADMIN_ACTION = "admin_action"
    PERMISSION_CHANGED = "permission_changed"

    # Security
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    LOCATION_CHANGE = "location_change"
    DEVICE_ADDED = "device_added"
    DEVICE_REMOVED = "device_removed"
    ENCRYPTION_KEY_ROTATED = "encryption_key_rotated"


class AuditLog(Base):
    """Audit log table for tracking all security-relevant events."""

    __tablename__ = "audit_logs"
    __table_args__ = (
        Index("idx_seller_id", "seller_id"),
        Index("idx_event_type", "event_type"),
        Index("idx_created_at", "created_at"),
        Index("idx_seller_event_date", "seller_id", "event_type", "created_at"),
    )

    id = Column(String(50), primary_key=True)
    seller_id = Column(String(255), nullable=False, index=True)
    user_id = Column(String(255), nullable=True, index=True)  # Who performed action
    event_type = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)  # e.g., "order", "user", "settings"
    resource_id = Column(String(255), nullable=True)
    action = Column(String(100), nullable=False)  # e.g., "GET", "POST", "DELETE"
    status = Column(String(20), nullable=False)  # success, failure, pending
    status_code = Column(Integer, nullable=True)  # HTTP status code

    # Request context
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    request_id = Column(String(50), nullable=True, index=True)

    # Details
    message = Column(Text, nullable=True)
    details = Column(JSON, nullable=True)  # Additional context
    error_details = Column(JSON, nullable=True)  # Error info if failed

    # Data access
    data_accessed = Column(JSON, nullable=True)  # What fields were accessed
    data_modified = Column(JSON, nullable=True)  # Old -> new values
    rows_affected = Column(Integer, nullable=True)

    # Security info
    is_risk = Column(Boolean, default=False, index=True)
    risk_score = Column(Integer, nullable=True)
    risk_reason = Column(String(255), nullable=True)

    # Retention
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    expires_at = Column(DateTime, nullable=True)  # For automatic cleanup

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "seller_id": self.seller_id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "status": self.status,
            "status_code": self.status_code,
            "ip_address": self.ip_address,
            "message": self.message,
            "details": self.details,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AuditLogger:
    """Service for recording audit events."""

    def __init__(self):
        self.logger = logging.getLogger("audit")

    async def log_event(
        self,
        db: Session,
        seller_id: str,
        event_type: AuditEventType,
        action: str,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_id: Optional[str] = None,
        message: Optional[str] = None,
        status: str = "success",
        status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
        data_accessed: Optional[List[str]] = None,
        data_modified: Optional[Dict[str, Any]] = None,
        rows_affected: Optional[int] = None,
        is_risk: bool = False,
        risk_score: Optional[int] = None,
        risk_reason: Optional[str] = None,
        error_details: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Log an audit event.

        Args:
            db: Database session
            seller_id: Seller/tenant ID
            event_type: Type of event (enum)
            action: HTTP method or action type
            user_id: User who performed action
            resource_type: Type of resource affected (order, user, etc)
            resource_id: ID of resource affected
            ip_address: Client IP
            user_agent: Client user agent
            request_id: Correlation request ID
            message: Human-readable message
            status: success, failure, pending
            status_code: HTTP status code
            details: Additional structured data
            data_accessed: Fields that were read
            data_modified: Fields that were changed (old -> new)
            rows_affected: Number of rows affected
            is_risk: Whether this is a suspicious event
            risk_score: Risk score (0-100)
            risk_reason: Why flagged as risk
            error_details: Error info if failed

        Returns:
            AuditLog record
        """
        import uuid

        audit_log = AuditLog(
            id=str(uuid.uuid4()),
            seller_id=seller_id,
            user_id=user_id,
            event_type=event_type.value,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            status=status,
            status_code=status_code,
            ip_address=ip_address,
            user_agent=user_agent,
            request_id=request_id,
            message=message,
            details=details or {},
            data_accessed=data_accessed,
            data_modified=data_modified,
            rows_affected=rows_affected,
            is_risk=is_risk,
            risk_score=risk_score,
            risk_reason=risk_reason,
            error_details=error_details,
            # Auto-expire logs after 90 days
            expires_at=datetime.now(timezone.utc) + timedelta(days=90),
        )

        try:
            db.add(audit_log)
            db.commit()
            db.refresh(audit_log)
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to log audit event: {e}", exc_info=True)
            # Don't raise - audit failure shouldn't break app

        # Also log to structured logger for real-time monitoring
        self._log_to_structured_logger(audit_log)

        return audit_log

    def _log_to_structured_logger(self, audit_log: AuditLog) -> None:
        """Log to structured logger for real-time monitoring."""
        log_level = logging.WARNING if audit_log.is_risk else logging.INFO

        self.logger.log(
            log_level,
            f"{audit_log.event_type}: {audit_log.action} {audit_log.resource_type}/{audit_log.resource_id}",
            extra={
                "seller_id": audit_log.seller_id,
                "user_id": audit_log.user_id,
                "event_type": audit_log.event_type,
                "status": audit_log.status,
                "ip": audit_log.ip_address,
                "risk": audit_log.is_risk,
                "risk_score": audit_log.risk_score,
            },
        )

    async def get_events(
        self,
        db: Session,
        seller_id: str,
        event_type: Optional[str] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[List[AuditLog], int]:
        """Get audit events with filtering."""
        query = db.query(AuditLog).filter(AuditLog.seller_id == seller_id)

        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if resource_type:
            query = query.filter(AuditLog.resource_type == resource_type)
        if start_date:
            query = query.filter(AuditLog.created_at >= start_date)
        if end_date:
            query = query.filter(AuditLog.created_at <= end_date)

        total = query.count()
        events = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset).all()

        return events, total

    async def cleanup_expired_logs(self, db: Session, batch_size: int = 1000) -> int:
        """Clean up logs older than retention period. Call periodically."""
        from sqlalchemy import delete

        cutoff = datetime.now(timezone.utc) - timedelta(days=90)
        deleted = db.execute(
            delete(AuditLog).where(AuditLog.expires_at <= cutoff)
        ).rowcount

        db.commit()
        logger.info(f"Cleaned up {deleted} expired audit logs")
        return deleted


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
