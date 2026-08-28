"""Invoicing API — /api/v1/businesses/{business_id}/invoicing/*"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.invoicing.schemas import (
    InvoiceCreate,
    InvoiceOut,
    InvoiceUpdate,
    PaymentCreate,
    PaymentOut,
    InvoiceTemplateCreate,
    InvoiceTemplateOut,
    InvoiceStatsResponse,
    InvoiceSend,
)
from app.domains.invoicing.service import (
    InvoicingService,
    PaymentService,
    InvoiceTemplateService,
)
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/invoicing", tags=["Invoicing"])


# Invoices
@router.post("/invoices", response_model=InvoiceOut)
async def create_invoice(
    business_id: UUID,
    body: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create invoice."""
    svc = InvoicingService(db)
    total = body.amount_aed + body.tax_aed
    return await svc.create_invoice(
        business_id,
        body.customer_id,
        body.amount_aed,
        body.tax_aed,
        body.due_date,
        body.items,
        body.notes,
    )


@router.get("/invoices", response_model=list[InvoiceOut])
async def list_invoices(
    business_id: UUID,
    status: str | None = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List invoices."""
    svc = InvoicingService(db)
    return await svc.list_invoices(business_id, status, limit)


@router.get("/invoices/{invoice_id}", response_model=InvoiceOut)
async def get_invoice(
    business_id: UUID,
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get invoice."""
    svc = InvoicingService(db)
    return await svc.get_invoice(invoice_id)


@router.patch("/invoices/{invoice_id}", response_model=InvoiceOut)
async def update_invoice(
    business_id: UUID,
    invoice_id: UUID,
    body: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update invoice."""
    svc = InvoicingService(db)
    return await svc.update_invoice(invoice_id, body.status, body.due_date, body.notes)


@router.post("/invoices/{invoice_id}/send", response_model=InvoiceOut)
async def send_invoice(
    business_id: UUID,
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Send invoice."""
    svc = InvoicingService(db)
    return await svc.send_invoice(invoice_id)


@router.post("/invoices/{invoice_id}/viewed", response_model=InvoiceOut)
async def mark_viewed(
    business_id: UUID,
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Mark invoice as viewed."""
    svc = InvoicingService(db)
    return await svc.mark_viewed(invoice_id)


@router.get("/invoices/stats", response_model=InvoiceStatsResponse)
async def get_stats(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get invoice statistics."""
    svc = InvoicingService(db)
    stats = await svc.invoice_stats(business_id)
    return InvoiceStatsResponse(**stats)


# Payments
@router.post("/invoices/{invoice_id}/payments", response_model=PaymentOut)
async def record_payment(
    business_id: UUID,
    invoice_id: UUID,
    body: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Record payment."""
    svc = PaymentService(db)
    return await svc.record_payment(invoice_id, body.amount_aed, body.method, body.reference)


@router.get("/payments", response_model=list[PaymentOut])
async def list_payments(
    business_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List payments."""
    svc = PaymentService(db)
    return await svc.list_payments(business_id, limit)


# Templates
@router.post("/templates", response_model=InvoiceTemplateOut)
async def create_template(
    business_id: UUID,
    body: InvoiceTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create invoice template."""
    svc = InvoiceTemplateService(db)
    return await svc.create_template(
        business_id, body.name, body.template_html, body.is_default
    )


@router.get("/templates", response_model=list[InvoiceTemplateOut])
async def list_templates(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List templates."""
    svc = InvoiceTemplateService(db)
    return await svc.list_templates(business_id)
