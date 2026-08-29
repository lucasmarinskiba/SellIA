"""Procurement services — vendors, RFQs, purchase orders."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.procurement.models import PurchaseOrder, RFQ, Vendor

logger = get_logger(__name__)


class VendorService:
    """Manage vendors and scoring."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_vendor(
        self,
        business_id: uuid.UUID,
        name: str,
        category: str,
        contact_email: str,
        contact_phone: Optional[str] = None,
    ) -> Vendor:
        """Create vendor."""
        vendor = Vendor(
            business_id=business_id,
            name=name,
            category=category,
            contact_email=contact_email,
            contact_phone=contact_phone,
        )
        self.db.add(vendor)
        await self.db.commit()
        return vendor

    async def list_vendors(self, business_id: uuid.UUID) -> list[Vendor]:
        """List active vendors."""
        vendors = (
            await self.db.execute(
                select(Vendor).where(
                    and_(
                        Vendor.business_id == business_id,
                        Vendor.is_active == True,
                    )
                )
            )
        ).scalars().all()
        return vendors

    async def update_scores(
        self,
        vendor_id: uuid.UUID,
        quality_score: Decimal,
        cost_score: Decimal,
        delivery_score: Decimal,
    ) -> Vendor:
        """Update vendor scores and calculate weighted overall score."""
        vendor = (
            await self.db.execute(select(Vendor).where(Vendor.id == vendor_id))
        ).scalar_one_or_none()
        if not vendor:
            raise ValueError(f"Vendor {vendor_id} not found")

        vendor.quality_score = quality_score
        vendor.cost_score = cost_score
        vendor.delivery_score = delivery_score
        # Weighted average: 40% quality, 35% cost, 25% delivery
        vendor.overall_score = (
            quality_score * Decimal("0.40") +
            cost_score * Decimal("0.35") +
            delivery_score * Decimal("0.25")
        )
        await self.db.commit()
        logger.info(f"Vendor {vendor_id} scored: {vendor.overall_score}")
        return vendor


class RFQService:
    """Manage Requests for Quotation."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_rfq(
        self,
        business_id: uuid.UUID,
        vendor_id: Optional[uuid.UUID],
        description: str,
        quantity: int,
        unit: str,
        expected_delivery_date: date,
    ) -> RFQ:
        """Create RFQ."""
        # Same collision risk as po_number above — see that comment.
        rfq_number = f"RFQ-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        rfq = RFQ(
            business_id=business_id,
            rfq_number=rfq_number,
            vendor_id=vendor_id,
            description=description,
            quantity=quantity,
            unit=unit,
            expected_delivery_date=expected_delivery_date,
            status="sent",
        )
        self.db.add(rfq)
        await self.db.commit()
        logger.info(f"RFQ created: {rfq_number}")
        return rfq

    async def get_rfq(self, rfq_id: uuid.UUID) -> RFQ:
        """Fetch RFQ."""
        rfq = (
            await self.db.execute(select(RFQ).where(RFQ.id == rfq_id))
        ).scalar_one_or_none()
        if not rfq:
            raise ValueError(f"RFQ {rfq_id} not found")
        return rfq

    async def accept_response(
        self,
        rfq_id: uuid.UUID,
        quote_amount_aed: Decimal,
    ) -> RFQ:
        """Accept RFQ response with quote."""
        rfq = await self.get_rfq(rfq_id)
        rfq.status = "received"
        rfq.quote_amount_aed = quote_amount_aed
        rfq.response_received_at = datetime.now(timezone.utc)
        await self.db.commit()
        return rfq


class PurchaseOrderService:
    """Manage Purchase Orders."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_po(
        self,
        business_id: uuid.UUID,
        vendor_id: uuid.UUID,
        rfq_id: Optional[uuid.UUID],
        description: str,
        quantity: int,
        unit_price_aed: Decimal,
        expected_delivery_date: date,
    ) -> PurchaseOrder:
        """Create purchase order."""
        # Second-precision timestamp alone collides whenever two POs are
        # created within the same wall-clock second — same fix as
        # invoicing.service.create_invoice's invoice_number.
        po_number = f"PO-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"
        total_amount = quantity * unit_price_aed

        po = PurchaseOrder(
            business_id=business_id,
            po_number=po_number,
            vendor_id=vendor_id,
            rfq_id=rfq_id,
            description=description,
            quantity=quantity,
            unit_price_aed=unit_price_aed,
            total_amount_aed=total_amount,
            expected_delivery_date=expected_delivery_date,
            status="issued",
        )
        self.db.add(po)
        await self.db.commit()
        logger.info(f"PO created: {po_number}, total: {total_amount} AED")
        return po

    async def get_po(self, po_id: uuid.UUID) -> PurchaseOrder:
        """Fetch PO."""
        po = (
            await self.db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
        ).scalar_one_or_none()
        if not po:
            raise ValueError(f"PO {po_id} not found")
        return po

    async def update_status(
        self,
        po_id: uuid.UUID,
        status: str,
        actual_delivery_date: Optional[date] = None,
        invoice_number: Optional[str] = None,
        invoice_amount_aed: Optional[Decimal] = None,
    ) -> PurchaseOrder:
        """Update PO status."""
        po = await self.get_po(po_id)
        old_status = po.status
        po.status = status

        if actual_delivery_date:
            po.actual_delivery_date = actual_delivery_date

        if status == "invoiced" and invoice_number:
            po.invoice_number = invoice_number
            po.invoice_amount_aed = invoice_amount_aed or po.total_amount_aed

        if status == "paid":
            po.paid_at = datetime.now(timezone.utc)

        await self.db.commit()
        logger.info(f"PO {po_id} status: {old_status} → {status}")
        return po

    async def po_summary(self, business_id: uuid.UUID) -> dict:
        """Summary of POs by status."""
        pos = (
            await self.db.execute(
                select(PurchaseOrder).where(PurchaseOrder.business_id == business_id)
            )
        ).scalars().all()

        issued = sum(1 for p in pos if p.status == "issued")
        received = sum(1 for p in pos if p.status == "received")
        invoiced = sum(1 for p in pos if p.status == "invoiced")
        paid = sum(1 for p in pos if p.status == "paid")
        total_amount = sum(p.total_amount_aed for p in pos)

        return {
            "total_pos": len(pos),
            "issued": issued,
            "received": received,
            "invoiced": invoiced,
            "paid": paid,
            "total_amount_aed": float(total_amount),
        }
