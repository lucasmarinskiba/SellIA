"""Legal services — compliance, contracts, audit logging."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.legal.models import AuditLog, ComplianceChecklistItem, ContractTemplate

logger = get_logger(__name__)


class ComplianceService:
    """Manage compliance requirements and tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_requirement(
        self,
        business_id: uuid.UUID,
        category: str,
        requirement: str,
        jurisdiction: str = "AE",
    ) -> ComplianceChecklistItem:
        """Add compliance requirement."""
        item = ComplianceChecklistItem(
            business_id=business_id,
            category=category,
            requirement=requirement,
            jurisdiction=jurisdiction,
            status="pending",
        )
        self.db.add(item)
        await self.db.commit()
        audit_svc = AuditLogService(self.db)
        await audit_svc.log(business_id, "compliance_item", item.id, "created", "system")
        return item

    async def get_requirement(self, item_id: uuid.UUID) -> ComplianceChecklistItem:
        """Fetch compliance requirement."""
        item = (
            await self.db.execute(select(ComplianceChecklistItem).where(ComplianceChecklistItem.id == item_id))
        ).scalar_one_or_none()
        if not item:
            raise ValueError(f"Compliance item {item_id} not found")
        return item

    async def update_status(
        self,
        item_id: uuid.UUID,
        status: str,
        verified_by: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> ComplianceChecklistItem:
        """Update compliance status (pending, compliant, non_compliant, waived)."""
        item = await self.get_requirement(item_id)
        old_status = item.status
        item.status = status
        if status in ("compliant", "non_compliant", "waived"):
            item.verified_at = datetime.now(timezone.utc)
            item.verified_by = verified_by or "system"
        if notes:
            item.notes = notes
        await self.db.commit()
        audit_svc = AuditLogService(self.db)
        await audit_svc.log(
            item.business_id,
            "compliance_item",
            item_id,
            "updated",
            verified_by or "system",
            {"old_status": old_status, "new_status": status},
        )
        return item

    async def compliance_status(self, business_id: uuid.UUID) -> dict:
        """Get compliance overview for business."""
        items = (
            await self.db.execute(
                select(ComplianceChecklistItem).where(ComplianceChecklistItem.business_id == business_id)
            )
        ).scalars().all()

        total = len(items)
        compliant = sum(1 for i in items if i.status == "compliant")
        non_compliant = sum(1 for i in items if i.status == "non_compliant")
        pending = sum(1 for i in items if i.status == "pending")
        waived = sum(1 for i in items if i.status == "waived")

        non_compliant_items = [i for i in items if i.status == "non_compliant"]

        return {
            "total_requirements": total,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "pending": pending,
            "waived": waived,
            "compliance_pct": (compliant / total * 100) if total else 0,
            "non_compliant_items": non_compliant_items,
        }


class ContractService:
    """Manage contract templates."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_template(
        self,
        business_id: uuid.UUID,
        name: str,
        contract_type: str,
        template_html: str,
    ) -> ContractTemplate:
        """Create contract template."""
        template = ContractTemplate(
            business_id=business_id,
            name=name,
            contract_type=contract_type,
            template_html=template_html,
        )
        self.db.add(template)
        await self.db.commit()
        return template

    async def list_templates(self, business_id: uuid.UUID) -> list[ContractTemplate]:
        """List active contract templates."""
        templates = (
            await self.db.execute(
                select(ContractTemplate).where(
                    and_(
                        ContractTemplate.business_id == business_id,
                        ContractTemplate.is_active,
                    )
                )
            )
        ).scalars().all()
        return templates

    async def get_template(self, template_id: uuid.UUID) -> ContractTemplate:
        """Fetch template by ID."""
        template = (
            await self.db.execute(select(ContractTemplate).where(ContractTemplate.id == template_id))
        ).scalar_one_or_none()
        if not template:
            raise ValueError(f"Template {template_id} not found")
        return template

    async def render_contract(self, template_id: uuid.UUID, variables: dict[str, str]) -> dict:
        """Render contract with variables (simple {{key}} replacement)."""
        template = await self.get_template(template_id)
        rendered_html = template.template_html
        for key, value in variables.items():
            rendered_html = rendered_html.replace(f"{{{{{key}}}}}", value)
        return {
            "template_id": template_id,
            "contract_type": template.contract_type,
            "rendered_html": rendered_html,
            "created_at": datetime.now(timezone.utc),
        }


class AuditLogService:
    """Manage audit trail."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        business_id: uuid.UUID,
        entity_type: str,
        entity_id: uuid.UUID,
        action: str,
        actor: str,
        details: Optional[dict] = None,
    ) -> AuditLog:
        """Log an audit event."""
        log = AuditLog(
            business_id=business_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor,
            details=details,
        )
        self.db.add(log)
        await self.db.commit()
        return log

    async def get_logs(self, business_id: uuid.UUID, limit: int = 100) -> list[AuditLog]:
        """Fetch recent audit logs."""
        logs = (
            await self.db.execute(
                select(AuditLog).where(AuditLog.business_id == business_id).order_by(AuditLog.timestamp.desc()).limit(limit)
            )
        ).scalars().all()
        return logs
