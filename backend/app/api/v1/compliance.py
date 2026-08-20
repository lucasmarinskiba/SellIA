"""Compliance API."""

from uuid import UUID
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.domains.compliance.compliance_service import ComplianceService

router = APIRouter(prefix="/api/v1", tags=["compliance"])


class SetConsentRequest(BaseModel):
    consent_type: str
    consented: bool


class ExportRequest(BaseModel):
    export_format: str = "json"


class DeletionRequest(BaseModel):
    deletion_type: str = "full"


@router.post("/customers/{customer_id}/consent")
def set_consent(customer_id: UUID, business_id: UUID, request: SetConsentRequest, db: Session = Depends(get_db)):
    return ComplianceService.set_consent(business_id, customer_id, request.consent_type, request.consented, db)


@router.post("/customers/{customer_id}/export-data")
def request_export(customer_id: UUID, business_id: UUID, request: ExportRequest, db: Session = Depends(get_db)):
    return ComplianceService.request_data_export(business_id, customer_id, request.export_format, db)


@router.post("/customers/{customer_id}/delete-data")
def request_deletion(customer_id: UUID, business_id: UUID, request: DeletionRequest, db: Session = Depends(get_db)):
    return ComplianceService.request_data_deletion(business_id, customer_id, request.deletion_type, db)


@router.get("/customers/{customer_id}/consent-status")
def get_consent_status(customer_id: UUID, business_id: UUID, db: Session = Depends(get_db)):
    return ComplianceService.get_consent_status(business_id, customer_id, db)
