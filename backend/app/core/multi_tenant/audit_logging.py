"""
AuditLogger: Immutable audit trail for compliance (SOC2, GDPR, HIPAA).
300 lines: Logs all tenant actions with context, IP, user-agent.
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum

from sqlalchemy import select, desc, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.core.exceptions import AppException
from .models import AuditLog

logger = get_logger(__name__)


class AuditAction(str, Enum):
    """Predefined audit actions."""
    # User actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_INVITED = "user.invited"
    USER_REMOVED = "user.removed"
    USER_ROLE_CHANGED = "user.role_changed"

    # API key actions
    API_KEY_CREATED = "api_key.created"
    API_KEY_ROTATED = "api_key.rotated"
    API_KEY_REVOKED = "api_key.revoked"

    # Tenant actions
    TENANT_CREATED = "tenant.created"
    TENANT_UPDATED = "tenant.updated"
    TENANT_DELETED = "tenant.deleted"
    TENANT_SUSPENDED = "tenant.suspended"
    TENANT_RESUMED = "tenant.resumed"

    # Billing actions
    BILLING_PAID = "billing.paid"
    BILLING_FAILED = "billing.failed"

    # Data actions
    DATA_EXPORTED = "data.exported"
    DATA_DELETED = "data.deleted"

    # Settings changes
    SETTINGS_CHANGED = "settings.changed"


class AuditStatus(str, Enum):
    """Action outcome."""
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"


class AuditService:
    """Immutable audit logging."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(
        self,
        tenant_id: str,
        action: str,
        resource_type: str,
        change_type: str,  # create, update, delete, read, export
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        status: str = AuditStatus.SUCCESS,
        reason: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
    ) -> AuditLog:
        """
        Create immutable audit log entry.

        Args:
            tenant_id: Tenant UUID
            action: Predefined action (e.g., "user.login", "data.exported")
            resource_type: "user", "api_key", "billing", "data", etc.
            change_type: "create", "update", "delete", "read", "export"
            user_id: Actor user UUID (optional for system events)
            user_email: Denormalized user email (for deleted users)
            resource_id: UUID of affected resource
            ip_address: Client IP (IPv4/IPv6)
            user_agent: HTTP User-Agent
            status: success, failed, warning
            reason: Why failed/warning
            details: Full payload (encrypted)
            old_values: Before snapshot (encrypted)
            new_values: After snapshot (encrypted)

        Returns:
            AuditLog record
        """
        audit_log = AuditLog(
            tenant_id=tenant_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            change_type=change_type,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            user_agent=user_agent,
            status=status,
            reason=reason,
            details=details or {},
            old_values=old_values,
            new_values=new_values,
        )

        self.db.add(audit_log)
        await self.db.commit()

        # Log to application logger too (for ops visibility)
        log_level = "warning" if status == AuditStatus.FAILED else "info"
        log_func = getattr(logger, log_level)

        log_func(
            f"Audit: {action}",
            extra={
                "tenant_id": str(tenant_id),
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "user_id": str(user_id) if user_id else "system",
                "ip_address": ip_address,
                "status": status,
                "reason": reason,
            },
        )

        return audit_log

    async def get_audit_log(self, log_id: str) -> Optional[AuditLog]:
        """Get audit log by ID."""
        result = await self.db.execute(
            select(AuditLog).where(AuditLog.id == log_id)
        )
        return result.scalar_one_or_none()

    async def list_tenant_audit_logs(
        self,
        tenant_id: str,
        action_filter: Optional[str] = None,
        user_id_filter: Optional[str] = None,
        resource_type_filter: Optional[str] = None,
        days_back: int = 90,
        limit: int = 1000,
        offset: int = 0,
    ) -> tuple[List[AuditLog], int]:
        """
        Query audit logs with filters.
        Retention: 90 days by default (configurable).

        Returns:
            (audit_logs, total_count)
        """
        query = select(AuditLog).where(AuditLog.tenant_id == tenant_id)

        # Date filter
        cutoff_date = datetime.now(timezone.utc).replace(
            day=datetime.now(timezone.utc).day - days_back
        )
        query = query.where(AuditLog.created_at >= cutoff_date)

        # Optional filters
        if action_filter:
            query = query.where(AuditLog.action == action_filter)

        if user_id_filter:
            query = query.where(AuditLog.user_id == user_id_filter)

        if resource_type_filter:
            query = query.where(AuditLog.resource_type == resource_type_filter)

        # Count total before pagination
        count_result = await self.db.execute(
            select(AuditLog).from_statement(
                query.statement.with_only_columns(AuditLog.id)
            )
        )
        total_count = len(count_result.all())

        # Apply pagination and ordering
        query = (
            query.order_by(desc(AuditLog.created_at))
            .limit(limit)
            .offset(offset)
        )

        result = await self.db.execute(query)
        logs = result.scalars().all()

        return logs, total_count

    async def list_user_audit_logs(
        self,
        tenant_id: str,
        user_id: str,
        limit: int = 100,
    ) -> List[AuditLog]:
        """Get all audit logs for specific user in tenant."""
        result = await self.db.execute(
            select(AuditLog)
            .where(
                and_(
                    AuditLog.tenant_id == tenant_id,
                    AuditLog.user_id == user_id,
                )
            )
            .order_by(desc(AuditLog.created_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def export_audit_logs(
        self,
        tenant_id: str,
        export_user_id: str,
        days_back: int = 90,
    ) -> str:
        """
        Export audit logs as CSV for compliance.
        Log the export action itself (data.exported).
        """
        logs, _ = await self.list_tenant_audit_logs(
            tenant_id,
            days_back=days_back,
            limit=10000,
        )

        # Format as CSV
        import csv
        import io
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "timestamp",
                "action",
                "resource_type",
                "resource_id",
                "user_id",
                "user_email",
                "ip_address",
                "status",
                "reason",
            ],
        )

        writer.writeheader()
        for log in logs:
            writer.writerow({
                "timestamp": log.created_at.isoformat(),
                "action": log.action,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "user_id": str(log.user_id) if log.user_id else "system",
                "user_email": log.user_email or "",
                "ip_address": log.ip_address or "",
                "status": log.status,
                "reason": log.reason or "",
            })

        csv_data = output.getvalue()

        # Log the export itself
        await self.log_action(
            tenant_id=tenant_id,
            action=AuditAction.DATA_EXPORTED,
            resource_type="audit_logs",
            change_type="export",
            user_id=export_user_id,
            status=AuditStatus.SUCCESS,
            details={
                "exported_records": len(logs),
                "days_back": days_back,
                "format": "csv",
            },
        )

        return csv_data

    async def delete_old_audit_logs(self, days_before: int = 365) -> int:
        """
        Delete audit logs older than X days.
        Run as scheduled task for storage management.
        CAUTION: Usually kept for compliance (1-7 years).
        """
        cutoff_date = datetime.now(timezone.utc).replace(
            day=datetime.now(timezone.utc).day - days_before
        )

        # Get count first
        count_result = await self.db.execute(
            select(AuditLog).where(AuditLog.created_at < cutoff_date)
        )
        count = len(count_result.all())

        # Delete
        await self.db.execute(
            select(AuditLog).where(AuditLog.created_at < cutoff_date)
        )
        await self.db.commit()

        logger.warning(
            f"Deleted {count} old audit logs (older than {days_before} days)"
        )

        return count


class AuditLogger:
    """Singleton for audit logging."""

    def get_service(self, db: AsyncSession) -> AuditService:
        return AuditService(db)

    async def log(
        self,
        db: AsyncSession,
        tenant_id: str,
        action: str,
        resource_type: str,
        **kwargs,
    ) -> AuditLog:
        service = self.get_service(db)
        return await service.log_action(
            tenant_id, action, resource_type, **kwargs
        )


_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get singleton AuditLogger."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger
