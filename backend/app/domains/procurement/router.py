"""Procurement API — /api/v1/businesses/{business_id}/procurement/*"""

from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.procurement.schemas import (
    PurchaseOrderCreate,
    PurchaseOrderOut,
    PurchaseOrderUpdate,
    RFQAccept,
    RFQCreate,
    RFQOut,
    VendorCreate,
    VendorOut,
    VendorScoreUpdate,
)
from app.domains.procurement.service import PurchaseOrderService, RFQService, VendorService
from app.domains.users.models import User

router = APIRouter(prefix="/{business_id}/procurement", tags=["Procurement"])


# Vendors
@router.post("/vendors", response_model=VendorOut)
async def create_vendor(
    business_id: UUID,
    body: VendorCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create vendor."""
    svc = VendorService(db)
    return await svc.create_vendor(business_id, body.name, body.category, body.contact_email, body.contact_phone)


@router.get("/vendors", response_model=list[VendorOut])
async def list_vendors(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List vendors."""
    svc = VendorService(db)
    return await svc.list_vendors(business_id)


@router.patch("/vendors/{vendor_id}/score", response_model=VendorOut)
async def score_vendor(
    business_id: UUID,
    vendor_id: UUID,
    body: VendorScoreUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update vendor scores."""
    svc = VendorService(db)
    return await svc.update_scores(vendor_id, body.quality_score, body.cost_score, body.delivery_score)


# RFQs
@router.post("/rfqs", response_model=RFQOut)
async def create_rfq(
    business_id: UUID,
    body: RFQCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create RFQ."""
    svc = RFQService(db)
    return await svc.create_rfq(
        business_id,
        body.vendor_id,
        body.description,
        body.quantity,
        body.unit,
        body.expected_delivery_date,
    )


@router.get("/rfqs/{rfq_id}", response_model=RFQOut)
async def get_rfq(
    business_id: UUID,
    rfq_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get RFQ."""
    svc = RFQService(db)
    return await svc.get_rfq(rfq_id)


@router.post("/rfqs/{rfq_id}/accept", response_model=RFQOut)
async def accept_rfq_response(
    business_id: UUID,
    rfq_id: UUID,
    body: RFQAccept,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Accept RFQ response."""
    svc = RFQService(db)
    return await svc.accept_response(rfq_id, body.quote_amount_aed)


# Purchase Orders
@router.post("/purchase-orders", response_model=PurchaseOrderOut)
async def create_po(
    business_id: UUID,
    body: PurchaseOrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create purchase order."""
    svc = PurchaseOrderService(db)
    return await svc.create_po(
        business_id,
        body.vendor_id,
        body.rfq_id,
        body.description,
        body.quantity,
        body.unit_price_aed,
        body.expected_delivery_date,
    )


@router.get("/purchase-orders/{po_id}", response_model=PurchaseOrderOut)
async def get_po(
    business_id: UUID,
    po_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get purchase order."""
    svc = PurchaseOrderService(db)
    return await svc.get_po(po_id)


@router.patch("/purchase-orders/{po_id}", response_model=PurchaseOrderOut)
async def update_po_status(
    business_id: UUID,
    po_id: UUID,
    body: PurchaseOrderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update PO status."""
    svc = PurchaseOrderService(db)
    return await svc.update_status(
        po_id,
        body.status,
        body.actual_delivery_date,
        body.invoice_number,
        body.invoice_amount_aed,
    )


@router.get("/purchase-orders/summary")
async def po_summary(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get PO summary."""
    svc = PurchaseOrderService(db)
    return await svc.po_summary(business_id)
