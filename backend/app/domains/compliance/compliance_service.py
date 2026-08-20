"""Compliance service."""

import logging
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy.orm import Session
from app.domains.compliance.compliance_models import ConsentRecord, DataDeletionRequest, DataExportRequest, AuditLog

logger = logging.getLogger(__name__)


class ComplianceService:
    """GDPR/CCPA compliance."""

    @staticmethod
    def set_consent(business_id: UUID, customer_id: UUID, consent_type: str, consented: bool, db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        record = ConsentRecord(business_id=business_id, customer_id=customer_id, consent_type=consent_type, consented=consented)
        db.add(record)
        
        ComplianceService._audit_log(business_id, "consent_updated", "customer", customer_id, None, db)
        db.commit()
        logger.info(f"Consent set: {customer_id} | {consent_type}={consented}")
        return {"consent_id": str(record.id), "consent_type": consent_type}

    @staticmethod
    def request_data_export(business_id: UUID, customer_id: UUID, export_format: str = "json", db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        request = DataExportRequest(business_id=business_id, customer_id=customer_id, export_format=export_format)
        db.add(request)
        
        ComplianceService._audit_log(business_id, "data_export_requested", "customer", customer_id, None, db)
        db.commit()
        logger.info(f"Export requested: {customer_id}")
        return {"request_id": str(request.id), "status": "pending"}

    @staticmethod
    def request_data_deletion(business_id: UUID, customer_id: UUID, deletion_type: str = "full", db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        request = DataDeletionRequest(business_id=business_id, customer_id=customer_id, deletion_type=deletion_type)
        db.add(request)
        
        ComplianceService._audit_log(business_id, "data_deletion_requested", "customer", customer_id, None, db)
        db.commit()
        logger.info(f"Deletion requested: {customer_id}")
        return {"request_id": str(request.id), "status": "pending"}

    @staticmethod
    def get_consent_status(business_id: UUID, customer_id: UUID, db: Session = None) -> dict:
        if not db:
            raise ValueError("Database session required")
        
        records = db.query(ConsentRecord).filter(
            ConsentRecord.business_id == business_id,
            ConsentRecord.customer_id == customer_id
        ).all()
        
        return {"consents": [{"type": r.consent_type, "consented": r.consented} for r in records]}

    @staticmethod
    def _audit_log(business_id: UUID, event_type: str, resource_type: str, resource_id: UUID, details: dict, db: Session) -> None:
        log = AuditLog(business_id=business_id, event_type=event_type, resource_type=resource_type, resource_id=resource_id, details=details)
        db.add(log)
