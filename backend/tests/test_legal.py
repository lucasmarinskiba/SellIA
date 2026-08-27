"""Tests for Legal domain."""

from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.legal.models import AuditLog, ComplianceChecklistItem, ContractTemplate
from app.domains.legal.service import AuditLogService, ComplianceService, ContractService


class TestComplianceService:
    """Test compliance requirement tracking."""

    @pytest.mark.asyncio
    async def test_add_requirement(self, db: AsyncSession):
        """Add compliance requirement."""
        business_id = uuid4()
        svc = ComplianceService(db)
        item = await svc.add_requirement(business_id, "tax", "File annual tax return", "AE")

        assert item.business_id == business_id
        assert item.category == "tax"
        assert item.requirement == "File annual tax return"
        assert item.status == "pending"

    @pytest.mark.asyncio
    async def test_update_status(self, db: AsyncSession):
        """Update compliance status."""
        business_id = uuid4()
        svc = ComplianceService(db)
        item = await svc.add_requirement(business_id, "labor_law", "Provide safe working environment")

        updated = await svc.update_status(item.id, "compliant", "legal_team", "Verified")

        assert updated.status == "compliant"
        assert updated.verified_by == "legal_team"
        assert updated.notes == "Verified"
        assert updated.verified_at is not None

    @pytest.mark.asyncio
    async def test_compliance_status(self, db: AsyncSession):
        """Get compliance overview."""
        business_id = uuid4()
        svc = ComplianceService(db)

        # Add requirements
        item1 = await svc.add_requirement(business_id, "tax", "File annual return")
        item2 = await svc.add_requirement(business_id, "labor", "Pay minimum wage")
        await svc.update_status(item1.id, "compliant", "legal")
        await svc.update_status(item2.id, "non_compliant", "audit")

        status = await svc.compliance_status(business_id)

        assert status["total_requirements"] == 2
        assert status["compliant"] == 1
        assert status["non_compliant"] == 1
        assert status["compliance_pct"] == 50.0


class TestContractService:
    """Test contract templates."""

    @pytest.mark.asyncio
    async def test_create_template(self, db: AsyncSession):
        """Create contract template."""
        business_id = uuid4()
        svc = ContractService(db)

        template = await svc.create_template(
            business_id,
            "Employment Contract",
            "employment",
            "<html>Employee: {{employee_name}}, Salary: {{salary}}</html>"
        )

        assert template.name == "Employment Contract"
        assert template.contract_type == "employment"
        assert template.is_active == True
        assert "{{employee_name}}" in template.template_html

    @pytest.mark.asyncio
    async def test_list_templates(self, db: AsyncSession):
        """List templates."""
        business_id = uuid4()
        svc = ContractService(db)

        await svc.create_template(business_id, "NDA", "nda", "<html>NDA</html>")
        await svc.create_template(business_id, "Vendor", "vendor", "<html>Vendor</html>")

        templates = await svc.list_templates(business_id)

        assert len(templates) == 2

    @pytest.mark.asyncio
    async def test_render_contract(self, db: AsyncSession):
        """Render contract with variables."""
        business_id = uuid4()
        svc = ContractService(db)

        template = await svc.create_template(
            business_id,
            "Employment",
            "employment",
            "Employee: {{name}}, Salary: {{salary}} AED"
        )

        rendered = await svc.render_contract(template.id, {"name": "John Doe", "salary": "50000"})

        assert "John Doe" in rendered["rendered_html"]
        assert "50000" in rendered["rendered_html"]


class TestAuditLogService:
    """Test audit logging."""

    @pytest.mark.asyncio
    async def test_log_event(self, db: AsyncSession):
        """Log audit event."""
        business_id = uuid4()
        entity_id = uuid4()
        svc = AuditLogService(db)

        log = await svc.log(
            business_id,
            "compliance_item",
            entity_id,
            "created",
            "system",
            {"category": "tax"}
        )

        assert log.entity_type == "compliance_item"
        assert log.action == "created"
        assert log.details["category"] == "tax"

    @pytest.mark.asyncio
    async def test_get_logs(self, db: AsyncSession):
        """Fetch audit logs."""
        business_id = uuid4()
        svc = AuditLogService(db)

        for i in range(5):
            await svc.log(business_id, "compliance_item", uuid4(), "updated", "user", {})

        logs = await svc.get_logs(business_id, limit=10)

        assert len(logs) == 5
        # Most recent first
        assert logs[0].timestamp >= logs[-1].timestamp
