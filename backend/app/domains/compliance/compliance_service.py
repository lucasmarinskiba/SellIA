"""Compliance service."""

import logging
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domains.compliance.compliance_models import ConsentRecord, DataDeletionRequest, DataExportRequest, AuditLog

logger = logging.getLogger(__name__)


class ComplianceService:
    """GDPR/CCPA compliance.

    Was written against the legacy sync Session API (db.query(...), bare
    db.commit() with no await) while api/v1/compliance.py injects the
    app's real async AsyncSession -- get_consent_status would raise
    AttributeError (AsyncSession has no .query()), and the three write
    methods would silently no-op (db.commit() returns an unawaited
    coroutine on AsyncSession, never actually executed). This entire
    GDPR/CCPA compliance module -- consent tracking, data export and
    deletion requests -- has been non-functional in production
    independent of the auth issue it was originally flagged for.
    Ported to the real async API throughout.
    """

    @staticmethod
    async def set_consent(business_id: UUID, customer_id: UUID, consent_type: str, consented: bool, db: AsyncSession = None) -> dict:
        if not db:
            raise ValueError("Database session required")

        record = ConsentRecord(business_id=business_id, customer_id=customer_id, consent_type=consent_type, consented=consented)
        db.add(record)

        await ComplianceService._audit_log(business_id, "consent_updated", "customer", customer_id, None, db)
        await db.commit()
        logger.info(f"Consent set: {customer_id} | {consent_type}={consented}")
        return {"consent_id": str(record.id), "consent_type": consent_type}

    @staticmethod
    async def request_data_export(business_id: UUID, customer_id: UUID, export_format: str = "json", db: AsyncSession = None) -> dict:
        if not db:
            raise ValueError("Database session required")

        request = DataExportRequest(business_id=business_id, customer_id=customer_id, export_format=export_format)
        db.add(request)

        await ComplianceService._audit_log(business_id, "data_export_requested", "customer", customer_id, None, db)
        await db.commit()
        logger.info(f"Export requested: {customer_id}")
        return {"request_id": str(request.id), "status": "pending"}

    @staticmethod
    async def request_data_deletion(business_id: UUID, customer_id: UUID, deletion_type: str = "full", db: AsyncSession = None) -> dict:
        if not db:
            raise ValueError("Database session required")

        request = DataDeletionRequest(business_id=business_id, customer_id=customer_id, deletion_type=deletion_type)
        db.add(request)

        await ComplianceService._audit_log(business_id, "data_deletion_requested", "customer", customer_id, None, db)
        await db.commit()
        logger.info(f"Deletion requested: {customer_id}")
        return {"request_id": str(request.id), "status": "pending"}

    @staticmethod
    async def get_consent_status(business_id: UUID, customer_id: UUID, db: AsyncSession = None) -> dict:
        if not db:
            raise ValueError("Database session required")

        result = await db.execute(
            select(ConsentRecord).where(
                ConsentRecord.business_id == business_id,
                ConsentRecord.customer_id == customer_id
            )
        )
        records = result.scalars().all()

        return {"consents": [{"type": r.consent_type, "consented": r.consented} for r in records]}

    @staticmethod
    async def _audit_log(business_id: UUID, event_type: str, resource_type: str, resource_id: UUID, details: dict, db: AsyncSession) -> None:
        log = AuditLog(business_id=business_id, event_type=event_type, resource_type=resource_type, resource_id=resource_id, details=details)
        db.add(log)
