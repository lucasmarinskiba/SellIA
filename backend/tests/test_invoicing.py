"""Tests for Invoicing domain — isolated SQLite."""

import json
import os
import uuid
from datetime import datetime, timedelta
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

# Import models directly, not through __init__
from app.domains.invoicing.models import INVOICING_TABLES  # noqa: E402, F401
from app.domains.invoicing.service import InvoicingService, PaymentService  # noqa: E402


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
        for t in INVOICING_TABLES:
            await conn.run_sync(lambda c, t=t: t.create(bind=c, checkfirst=True))
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as s:
        yield s
    await engine.dispose()


class TestInvoicing:
    """Test invoicing service."""

    @pytest.mark.asyncio
    async def test_create_invoice(self, db: AsyncSession):
        """Create invoice."""
        business_id = uuid4()
        customer_id = uuid4()
        svc = InvoicingService(db)

        invoice = await svc.create_invoice(
            business_id,
            customer_id,
            Decimal("1000.00"),
            Decimal("100.00"),
            datetime.now() + timedelta(days=30),
            items=[{"desc": "Item 1", "qty": 2, "price": 500}],
            notes="Test invoice",
        )

        assert invoice.invoice_number.startswith("INV-")
        assert invoice.amount_aed == Decimal("1000.00")
        assert invoice.tax_aed == Decimal("100.00")
        assert invoice.total_aed == Decimal("1100.00")
        assert invoice.status == "draft"

    @pytest.mark.asyncio
    async def test_send_invoice(self, db: AsyncSession):
        """Send invoice."""
        business_id = uuid4()
        svc = InvoicingService(db)

        invoice = await svc.create_invoice(
            business_id,
            None,
            Decimal("500.00"),
            Decimal("50.00"),
            datetime.now() + timedelta(days=7),
        )

        sent = await svc.send_invoice(invoice.id)
        assert sent.status == "sent"
        assert sent.sent_at is not None

    @pytest.mark.asyncio
    async def test_invoice_stats(self, db: AsyncSession):
        """Get invoice statistics."""
        business_id = uuid4()
        svc = InvoicingService(db)

        # Create invoices
        inv1 = await svc.create_invoice(business_id, None, Decimal("1000"), Decimal("100"), datetime.now() + timedelta(days=30))
        inv2 = await svc.create_invoice(business_id, None, Decimal("500"), Decimal("50"), datetime.now() + timedelta(days=30))

        # Send first
        await svc.send_invoice(inv1.id)

        stats = await svc.invoice_stats(business_id)

        assert stats["total_invoices"] == 2
        assert stats["total_revenue_aed"] == 1650.0  # 1100 + 550
        assert stats["pending_revenue_aed"] == 1650.0  # Both not paid


class TestPayment:
    """Test payment service."""

    @pytest.mark.asyncio
    async def test_record_payment(self, db: AsyncSession):
        """Record payment."""
        business_id = uuid4()
        inv_svc = InvoicingService(db)
        pay_svc = PaymentService(db)

        invoice = await inv_svc.create_invoice(
            business_id, None, Decimal("1000"), Decimal("100"), datetime.now() + timedelta(days=30)
        )

        payment = await pay_svc.record_payment(invoice.id, Decimal("1100"), "bank_transfer", "TRX123")

        assert payment.amount_aed == Decimal("1100")
        assert payment.method == "bank_transfer"
        assert payment.status == "completed"

        # Check invoice marked as paid
        paid_inv = await inv_svc.get_invoice(invoice.id)
        assert paid_inv.status == "paid"
        assert paid_inv.paid_at is not None

    @pytest.mark.asyncio
    async def test_list_payments(self, db: AsyncSession):
        """List payments."""
        business_id = uuid4()
        inv_svc = InvoicingService(db)
        pay_svc = PaymentService(db)

        # Create invoices and payments
        for i in range(3):
            inv = await inv_svc.create_invoice(
                business_id, None, Decimal("100"), Decimal("10"), datetime.now() + timedelta(days=30)
            )
            await pay_svc.record_payment(inv.id, Decimal("110"), "card")

        payments = await pay_svc.list_payments(business_id)
        assert len(payments) == 3
