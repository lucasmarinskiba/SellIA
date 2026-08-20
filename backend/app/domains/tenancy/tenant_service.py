"""Multi-tenant isolation service — data boundaries, audit, compliance."""

import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
from typing import Optional, List, Dict

from sqlalchemy.orm import Session
from sqlalchemy import func

from app.domains.tenancy.tenant_models import (
    TenantIsolationPolicy, AuditLog, TenantUser, DataAccessLog, ComplianceReport,
    AuditActionType, DataClassification
)

logger = logging.getLogger(__name__)


class TenantIsolationService:
    """Enforce multi-tenant data isolation and audit."""

    @staticmethod
    def setup_isolation_policy(
        business_id: UUID,
        isolation_level: str = "row_level",
        audit_enabled: bool = True,
        gdpr_mode: bool = False,
        ccpa_mode: bool = False,
        db: Session = None
    ) -> dict:
        """Configure tenant isolation policy."""
        if not db:
            raise ValueError("Database session required")

        policy = db.query(TenantIsolationPolicy).filter(
            TenantIsolationPolicy.business_id == business_id
        ).first()

        if policy:
            policy.isolation_level = isolation_level
            policy.audit_enabled = audit_enabled
            policy.gdpr_compliance_mode = gdpr_mode
            policy.ccpa_compliance_mode = ccpa_mode
        else:
            policy = TenantIsolationPolicy(
                business_id=business_id,
                isolation_level=isolation_level,
                audit_enabled=audit_enabled,
                gdpr_compliance_mode=gdpr_mode,
                ccpa_compliance_mode=ccpa_mode
            )
            db.add(policy)

        db.commit()

        logger.info(f"Isolation policy set: {business_id} - level={isolation_level}, audit={audit_enabled}")

        return {
            "business_id": str(business_id),
            "isolation_level": isolation_level,
            "audit_enabled": audit_enabled,
            "gdpr_mode": gdpr_mode,
            "ccpa_mode": ccpa_mode
        }

    @staticmethod
    def log_audit(
        business_id: UUID,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        user_id: Optional[str] = None,
        user_ip: Optional[str] = None,
        change_details: Optional[Dict] = None,
        api_key_id: Optional[str] = None,
        endpoint: Optional[str] = None,
        action_status: str = "success",
        error_message: Optional[str] = None,
        db: Session = None
    ) -> dict:
        """Log user action for audit trail."""
        if not db:
            raise ValueError("Database session required")

        # Check if audit enabled for this tenant
        policy = db.query(TenantIsolationPolicy).filter(
            TenantIsolationPolicy.business_id == business_id
        ).first()

        if policy and not policy.audit_enabled:
            return {"audit_logged": False, "reason": "Audit disabled for tenant"}

        # Skip logging READ actions if log_all_reads is False
        if action == AuditActionType.READ and policy and not policy.log_all_reads:
            return {"audit_logged": False, "reason": "Read actions not logged"}

        audit_log = AuditLog(
            business_id=business_id,
            user_id=user_id,
            user_ip_address=user_ip,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            change_details=change_details,
            api_key_id=api_key_id,
            endpoint=endpoint,
            action_status=action_status,
            error_message=error_message
        )

        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)

        logger.info(f"Audit logged: {business_id} - {action} on {resource_type}")

        return {
            "audit_id": str(audit_log.id),
            "action": action,
            "resource_type": resource_type,
            "status": action_status,
            "logged_at": audit_log.created_at.isoformat()
        }

    @staticmethod
    def add_tenant_user(
        business_id: UUID,
        email: str,
        role: str = "member",
        permissions: List[str] = None,
        db: Session = None
    ) -> dict:
        """Add user to business tenant."""
        if not db:
            raise ValueError("Database session required")

        user = TenantUser(
            business_id=business_id,
            email=email,
            role=role,
            permissions=permissions or []
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        logger.info(f"Tenant user added: {email} to {business_id} - role={role}")

        return {
            "user_id": str(user.id),
            "email": email,
            "role": role,
            "permissions": permissions or []
        }

    @staticmethod
    def log_data_access(
        business_id: UUID,
        access_type: str,
        data_type: str,
        user_email: str,
        user_ip: Optional[str] = None,
        rows_accessed: Optional[int] = None,
        pii_included: bool = False,
        db: Session = None
    ) -> dict:
        """Log data access event (export, download, api)."""
        if not db:
            raise ValueError("Database session required")

        access_log = DataAccessLog(
            business_id=business_id,
            access_type=access_type,
            data_type=data_type,
            user_email=user_email,
            user_ip=user_ip,
            rows_accessed=rows_accessed,
            pii_fields_included=pii_included,
            encrypted_in_transit=True
        )

        db.add(access_log)
        db.commit()

        logger.info(f"Data access logged: {business_id} - {access_type} of {data_type} by {user_email}")

        return {
            "access_id": str(access_log.id),
            "access_type": access_type,
            "data_type": data_type,
            "rows_accessed": rows_accessed,
            "pii_included": pii_included,
            "logged_at": access_log.created_at.isoformat()
        }

    @staticmethod
    def get_audit_trail(
        business_id: UUID,
        days: int = 30,
        action_filter: Optional[str] = None,
        user_filter: Optional[str] = None,
        db: Session = None
    ) -> dict:
        """Get audit trail for tenant."""
        if not db:
            raise ValueError("Database session required")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        query = db.query(AuditLog).filter(
            AuditLog.business_id == business_id,
            AuditLog.created_at >= cutoff
        )

        if action_filter:
            query = query.filter(AuditLog.action == action_filter)

        if user_filter:
            query = query.filter(AuditLog.user_id == user_filter)

        logs = query.order_by(AuditLog.created_at.desc()).limit(1000).all()

        # Summary
        actions = {}
        for log in logs:
            actions[log.action] = actions.get(log.action, 0) + 1

        failed = len([l for l in logs if l.action_status == "error"])

        return {
            "audit_trail_generated": True,
            "period_days": days,
            "total_actions": len(logs),
            "failed_actions": failed,
            "by_action": actions,
            "logs": [
                {
                    "action": l.action,
                    "resource": l.resource_type,
                    "user": l.user_id,
                    "status": l.action_status,
                    "timestamp": l.created_at.isoformat()
                }
                for l in logs[:50]
            ]
        }

    @staticmethod
    def generate_compliance_report(
        business_id: UUID,
        report_type: str,
        days: int = 30,
        db: Session = None
    ) -> dict:
        """Generate compliance report (audit, GDPR, CCPA)."""
        if not db:
            raise ValueError("Database session required")

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        period_start = cutoff.strftime("%Y-%m-%d")
        period_end = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Collect metrics
        if report_type == "audit_trail":
            logs = db.query(AuditLog).filter(
                AuditLog.business_id == business_id,
                AuditLog.created_at >= cutoff
            ).all()

            total_actions = len(logs)
            failed_actions = len([l for l in logs if l.action_status == "error"])
            users_active = len(set(l.user_id for l in logs if l.user_id))

        elif report_type in ["gdpr_dsar", "ccpa_dsar"]:
            # Data Subject Access Request report
            access_logs = db.query(DataAccessLog).filter(
                DataAccessLog.business_id == business_id,
                DataAccessLog.created_at >= cutoff
            ).all()

            total_actions = len(access_logs)
            data_accesses = len([a for a in access_logs if a.access_type in ["export", "download"]])
            pii_exposures = len([a for a in access_logs if a.pii_fields_included])
            users_active = len(set(a.user_email for a in access_logs))

        else:
            total_actions = 0
            failed_actions = 0
            data_accesses = 0
            users_active = 0

        report = ComplianceReport(
            business_id=business_id,
            report_type=report_type,
            report_period_start=period_start,
            report_period_end=period_end,
            total_actions=total_actions,
            data_accesses=data_accesses if report_type != "audit_trail" else 0,
            failed_access_attempts=failed_actions if report_type == "audit_trail" else 0,
            users_active=users_active
        )

        db.add(report)
        db.commit()

        logger.info(f"Compliance report generated: {business_id} - {report_type}")

        return {
            "report_id": str(report.id),
            "report_type": report_type,
            "period": f"{period_start} to {period_end}",
            "total_actions": total_actions,
            "data_accesses": data_accesses,
            "failed_actions": failed_actions,
            "users_active": users_active
        }

    @staticmethod
    def verify_cross_tenant_access_blocked(
        business_id: UUID,
        request_business_id: UUID,
        db: Session = None
    ) -> Tuple[bool, Optional[str]]:
        """Verify request is not accessing another tenant's data."""
        if not db:
            raise ValueError("Database session required")

        # Check if tenant isolation is enforced
        policy = db.query(TenantIsolationPolicy).filter(
            TenantIsolationPolicy.business_id == business_id
        ).first()

        if policy and policy.cross_tenant_data_access_blocked:
            if business_id != request_business_id:
                logger.warning(f"Cross-tenant access attempt: {business_id} -> {request_business_id}")
                return False, "Cross-tenant access denied"

        return True, None
