"""Legal domain models."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ComplianceChecklistItem(Base):
    """Compliance requirement (labor, tax, privacy, etc.)."""
    __tablename__ = "compliance_checklist_items"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    category: Mapped[str] = mapped_column(String(100))  # labor_law, tax, data_privacy, contract, etc.
    requirement: Mapped[str] = mapped_column(String(500))
    jurisdiction: Mapped[str] = mapped_column(String(50), default="AE")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending, compliant, non_compliant, waived
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ContractTemplate(Base):
    """Contract template for employment, NDA, vendor agreements."""
    __tablename__ = "contract_templates"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    contract_type: Mapped[str] = mapped_column(String(50))  # employment, nda, vendor, etc.
    template_html: Mapped[str] = mapped_column(Text)  # HTML with {{variable}} placeholders
    version: Mapped[int] = mapped_column(default=1)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    """Audit trail for compliance events.

    Table is named `legal_audit_logs`, not `audit_logs` — 7 files across the
    codebase claim that name on the shared Base (compliance, tenancy, db,
    core.multi_tenant, core.database.security_models, core.security
    .audit_logger, plus this one). Whichever imports first wins; this
    domain's AuditLog was the loser, which meant legal.router had been
    silently dead on every app boot (confirmed via main.py's "Skipped extra
    router ... Table already defined" warning — same failure mode fixed for
    invoicing's Invoice/Payment tables, see that domain's models.py).
    No Alembic migration creates any of the 7 `audit_logs` variants (only
    referenced in alembic/env.py's autogenerate-ignore list), so renaming
    this one is zero-risk.
    """
    __tablename__ = "legal_audit_logs"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=func.gen_random_uuid())
    business_id: Mapped[UUID] = mapped_column(ForeignKey("businesses.id", ondelete="CASCADE"))
    entity_type: Mapped[str] = mapped_column(String(50))  # employee, contract, compliance_item, etc.
    entity_id: Mapped[UUID] = mapped_column()
    action: Mapped[str] = mapped_column(String(50))  # created, updated, approved, signed, etc.
    actor: Mapped[str] = mapped_column(String(255))
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


LEGAL_TABLES = [ComplianceChecklistItem.__table__, ContractTemplate.__table__, AuditLog.__table__]
