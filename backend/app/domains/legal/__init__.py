"""Legal automation — compliance, contracts, documentation."""

from app.domains.legal.models import LEGAL_TABLES, AuditLog, ComplianceChecklistItem, ContractTemplate
from app.domains.legal.router import router
from app.domains.legal.service import AuditLogService, ComplianceService, ContractService

__all__ = [
    "LEGAL_TABLES",
    "ComplianceChecklistItem",
    "ContractTemplate",
    "AuditLog",
    "ComplianceService",
    "ContractService",
    "AuditLogService",
    "router",
]
