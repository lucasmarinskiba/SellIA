"""Tests for Procurement domain — isolated SQLite."""

import json
import os
import uuid
from datetime import date, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
import pytest_asyncio

os.environ.setdefault("ENVIRONMENT", "testing")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32-chars-long-1234567890")

from sqlalchemy import Column, String, Table, text
from sqlalchemy.dialects.postgresql import JSONB as PGJSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool


@compiles(PGUUID, "sqlite")
def _uuid_sqlite(el, comp, **kw):  # noqa: ANN001
    return "CHAR(36)"


@compiles(PGJSONB, "sqlite")
def _jsonb_sqlite(el, comp, **kw):  # noqa: ANN001
    return "TEXT"


PGUUID.bind_processor = lambda self, d: (lambda v: None if v is None else str(v))
PGUUID.result_processor = lambda self, d, c: (
    lambda v: None if v is None else (_try_uuid(v))
)
PGJSONB.bind_processor = lambda self, d: (lambda v: None if v is None else json.dumps(v))
PGJSONB.result_processor = lambda self, d, c: (
    lambda v: None if v in (None, "") else (v if isinstance(v, (dict, list)) else json.loads(v))
)


def _try_uuid(v):
    try:
        return uuid.UUID(v)
    except (ValueError, TypeError, AttributeError):
        return v


from app.core.database import Base  # noqa: E402
from app.domains.procurement.models import PROCUREMENT_TABLES  # noqa: E402
from app.domains.procurement.models import PurchaseOrder, RFQ, Vendor  # noqa: E402
from app.domains.procurement.service import PurchaseOrderService, RFQService, VendorService  # noqa: E402


@pytest_asyncio.fixture
async def db() -> AsyncSession:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    if "businesses" not in Base.metadata.tables:
        Table("businesses", Base.metadata, Column("id", String(36), primary_key=True))
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.tables["businesses"].create(bind=c, checkfirst=True))
        for t in PROCUREMENT_TABLES:
            await conn.run_sync(lambda c, t=t: t.create(bind=c, checkfirst=True))
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as s:
        yield s
    await engine.dispose()


class TestVendorService:
    """Test vendor management."""

    @pytest.mark.asyncio
    async def test_create_vendor(self, db: AsyncSession):
        """Create vendor."""
        business_id = uuid4()
        svc = VendorService(db)

        vendor = await svc.create_vendor(
            business_id,
            "TechCorp",
            "it_hardware",
            "contact@techcorp.ae",
            "+971501234567"
        )

        assert vendor.name == "TechCorp"
        assert vendor.category == "it_hardware"
        assert vendor.is_active == True

    @pytest.mark.asyncio
    async def test_list_vendors(self, db: AsyncSession):
        """List vendors."""
        business_id = uuid4()
        svc = VendorService(db)

        await svc.create_vendor(business_id, "Vendor1", "cat1", "v1@ae.ae")
        await svc.create_vendor(business_id, "Vendor2", "cat2", "v2@ae.ae")

        vendors = await svc.list_vendors(business_id)

        assert len(vendors) == 2

    @pytest.mark.asyncio
    async def test_update_scores(self, db: AsyncSession):
        """Update vendor scores."""
        business_id = uuid4()
        svc = VendorService(db)

        vendor = await svc.create_vendor(business_id, "TestVendor", "cat", "test@ae.ae")

        updated = await svc.update_scores(
            vendor.id,
            Decimal("80"),  # quality
            Decimal("75"),  # cost
            Decimal("90"),  # delivery
        )

        assert updated.quality_score == Decimal("80")
        assert updated.cost_score == Decimal("75")
        assert updated.delivery_score == Decimal("90")
        # 80*0.40 + 75*0.35 + 90*0.25 = 32 + 26.25 + 22.5 = 80.75
        assert updated.overall_score == Decimal("80.75")


class TestRFQService:
    """Test RFQ management."""

    @pytest.mark.asyncio
    async def test_create_rfq(self, db: AsyncSession):
        """Create RFQ."""
        business_id = uuid4()
        vendor_id = uuid4()
        delivery_date = date.today() + timedelta(days=30)
        svc = RFQService(db)

        rfq = await svc.create_rfq(
            business_id,
            vendor_id,
            "100 office chairs",
            100,
            "pieces",
            delivery_date
        )

        assert rfq.status == "sent"
        assert rfq.quantity == 100
        assert "RFQ-" in rfq.rfq_number

    @pytest.mark.asyncio
    async def test_accept_response(self, db: AsyncSession):
        """Accept RFQ response."""
        business_id = uuid4()
        delivery_date = date.today() + timedelta(days=30)
        svc = RFQService(db)

        rfq = await svc.create_rfq(business_id, None, "Materials", 50, "kg", delivery_date)

        updated = await svc.accept_response(rfq.id, Decimal("5000.50"))

        assert updated.status == "received"
        assert updated.quote_amount_aed == Decimal("5000.50")
        assert updated.response_received_at is not None


class TestPurchaseOrderService:
    """Test purchase order management."""

    @pytest.mark.asyncio
    async def test_create_po(self, db: AsyncSession):
        """Create PO."""
        business_id = uuid4()
        vendor_id = uuid4()
        delivery_date = date.today() + timedelta(days=14)
        svc = PurchaseOrderService(db)

        po = await svc.create_po(
            business_id,
            vendor_id,
            None,
            "Laptop computers",
            10,
            Decimal("3500.00"),
            delivery_date
        )

        assert po.status == "issued"
        assert po.quantity == 10
        assert po.unit_price_aed == Decimal("3500.00")
        assert po.total_amount_aed == Decimal("35000.00")
        assert "PO-" in po.po_number

    @pytest.mark.asyncio
    async def test_update_po_status(self, db: AsyncSession):
        """Update PO status."""
        business_id = uuid4()
        vendor_id = uuid4()
        delivery_date = date.today() + timedelta(days=14)
        svc = PurchaseOrderService(db)

        po = await svc.create_po(
            business_id,
            vendor_id,
            None,
            "Items",
            5,
            Decimal("100.00"),
            delivery_date
        )

        # Mark as received
        received = await svc.update_status(po.id, "received", date.today())
        assert received.status == "received"
        assert received.actual_delivery_date == date.today()

        # Mark as invoiced
        invoiced = await svc.update_status(
            po.id,
            "invoiced",
            invoice_number="INV-001",
            invoice_amount_aed=Decimal("500.00")
        )
        assert invoiced.status == "invoiced"
        assert invoiced.invoice_number == "INV-001"

        # Mark as paid
        paid = await svc.update_status(po.id, "paid")
        assert paid.status == "paid"
        assert paid.paid_at is not None

    @pytest.mark.asyncio
    async def test_po_summary(self, db: AsyncSession):
        """Get PO summary."""
        business_id = uuid4()
        vendor_id = uuid4()
        delivery_date = date.today() + timedelta(days=30)
        svc = PurchaseOrderService(db)

        # Create multiple POs
        po1 = await svc.create_po(business_id, vendor_id, None, "Item1", 1, Decimal("100"), delivery_date)
        po2 = await svc.create_po(business_id, vendor_id, None, "Item2", 2, Decimal("200"), delivery_date)
        po3 = await svc.create_po(business_id, vendor_id, None, "Item3", 3, Decimal("300"), delivery_date)

        # Update statuses
        await svc.update_status(po1.id, "received")
        await svc.update_status(po2.id, "invoiced")
        await svc.update_status(po3.id, "paid")

        summary = await svc.po_summary(business_id)

        assert summary["total_pos"] == 3
        assert summary["issued"] == 0
        assert summary["received"] == 1
        assert summary["invoiced"] == 1
        assert summary["paid"] == 1
        assert summary["total_amount_aed"] == 1400.0  # 100 + 400 + 900
