"""Auto-posting engine — business events -> balanced journal entries.

Every method is idempotent: calling it twice for the same source event
returns the already-posted entry instead of double-counting. Callers
(order webhooks, payout jobs, the ad-budget engine, subscription billing)
should invoke these rather than touching LedgerService.post_entry directly
so the account mapping stays in one place.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.ledger.models import JournalSource
from app.domains.ledger.service import LedgerService, _q

logger = get_logger(__name__)

# gateway -> cash account subtype
GATEWAY_CASH_SUBTYPE = {
    "mercadopago": "cash_mercadopago",
    "mercado_pago": "cash_mercadopago",
    "stripe": "cash_stripe",
}

AD_PLATFORM_SUBTYPE = {
    "meta": "ad_spend_meta",
    "facebook": "ad_spend_meta",
    "instagram": "ad_spend_meta",
    "google": "ad_spend_google",
    "google_ads": "ad_spend_google",
    "tiktok": "ad_spend_tiktok",
    "tiktok_ads": "ad_spend_tiktok",
}


class PostingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.ledger = LedgerService(db)

    def _cash_subtype(self, gateway: Optional[str]) -> str:
        if not gateway:
            return "cash"
        return GATEWAY_CASH_SUBTYPE.get(gateway.lower().strip(), "cash")

    # ------------------------------------------------------------------
    async def post_order_paid(
        self,
        business_id: uuid.UUID,
        *,
        order_id: uuid.UUID,
        total_amount: Decimal,
        tax_amount: Optional[Decimal] = None,
        discount_amount: Optional[Decimal] = None,
        processing_fee: Optional[Decimal] = None,
        gateway: Optional[str] = None,
        currency: str = "ARS",
        is_service: bool = False,
        entry_date: Optional[datetime] = None,
        customer_id: Optional[uuid.UUID] = None,
    ) -> Any:
        """Revenue recognition for a paid order.

        Dr  Cash/clearing        total received
        Dr  Sales discounts      discount (contra-revenue)
        Dr  Processing fees      gateway fee              (optional)
            Cr  Product/Service revenue   net of tax & discount
            Cr  VAT output                tax
            Cr  Cash/clearing             gateway fee     (optional)
        """
        total = _q(total_amount)
        tax = _q(tax_amount or 0)
        discount = _q(discount_amount or 0)
        fee = _q(processing_fee or 0)
        net_revenue = _q(total - tax + discount)
        rev_subtype = "service_sales" if is_service else "product_sales"
        cash_subtype = self._cash_subtype(gateway)

        lines: list[dict[str, Any]] = [
            {"account_subtype": cash_subtype, "debit": total,
             "description": f"Cobro orden {order_id}"},
            {"account_subtype": rev_subtype, "credit": net_revenue,
             "description": "Venta neta", "contact_type": "customer", "contact_id": customer_id},
        ]
        if tax > 0:
            lines.append({"account_subtype": "vat_output", "credit": tax,
                          "description": "IVA débito fiscal"})
        if discount > 0:
            lines.append({"account_subtype": "sales_discounts", "debit": discount,
                          "description": "Descuento otorgado"})
        if fee > 0:
            lines.append({"account_subtype": "payment_processing_fees", "debit": fee,
                          "description": f"Comisión {gateway or 'pasarela'}"})
            lines.append({"account_subtype": cash_subtype, "credit": fee,
                          "description": "Retención de comisión"})

        return await self.ledger.post_entry(
            business_id,
            lines,
            entry_date=entry_date,
            memo=f"Orden pagada {order_id}",
            source=JournalSource.ORDER.value,
            source_ref=str(order_id),
            idempotency_key=f"order_paid:{business_id}:{order_id}",
            currency=currency,
        )

    # ------------------------------------------------------------------
    async def post_refund(
        self,
        business_id: uuid.UUID,
        *,
        order_id: uuid.UUID,
        amount: Decimal,
        tax_amount: Optional[Decimal] = None,
        gateway: Optional[str] = None,
        currency: str = "ARS",
        is_service: bool = False,
        entry_date: Optional[datetime] = None,
        refund_ref: Optional[str] = None,
    ) -> Any:
        amt = _q(amount)
        tax = _q(tax_amount or 0)
        net = _q(amt - tax)
        rev_subtype = "service_sales" if is_service else "product_sales"
        cash_subtype = self._cash_subtype(gateway)
        ref = refund_ref or str(order_id)

        lines: list[dict[str, Any]] = [
            {"account_subtype": rev_subtype, "debit": net, "description": "Reversión de venta"},
            {"account_subtype": cash_subtype, "credit": amt, "description": f"Reembolso orden {order_id}"},
        ]
        if tax > 0:
            lines.append({"account_subtype": "vat_output", "debit": tax,
                          "description": "Reversión IVA débito"})

        return await self.ledger.post_entry(
            business_id,
            lines,
            entry_date=entry_date,
            memo=f"Reembolso orden {order_id}",
            source=JournalSource.REFUND.value,
            source_ref=ref,
            idempotency_key=f"refund:{business_id}:{ref}",
            currency=currency,
        )

    # ------------------------------------------------------------------
    async def post_ad_spend(
        self,
        business_id: uuid.UUID,
        *,
        platform: str,
        amount: Decimal,
        spend_ref: str,
        on_credit: bool = False,
        currency: str = "ARS",
        entry_date: Optional[datetime] = None,
        campaign: Optional[str] = None,
    ) -> Any:
        amt = _q(amount)
        subtype = AD_PLATFORM_SUBTYPE.get((platform or "").lower().strip(), "ad_spend_other")
        credit_subtype = "accounts_payable" if on_credit else "cash"
        lines = [
            {"account_subtype": subtype, "debit": amt,
             "description": f"Ads {platform}" + (f" — {campaign}" if campaign else "")},
            {"account_subtype": credit_subtype, "credit": amt,
             "description": f"Pago ads {platform}"},
        ]
        return await self.ledger.post_entry(
            business_id,
            lines,
            entry_date=entry_date,
            memo=f"Inversión publicitaria {platform}",
            source=JournalSource.AD_SPEND.value,
            source_ref=spend_ref,
            idempotency_key=f"ad_spend:{business_id}:{platform}:{spend_ref}",
            currency=currency,
        )

    # ------------------------------------------------------------------
    async def post_subscription_charge(
        self,
        business_id: uuid.UUID,
        *,
        charge_ref: str,
        amount: Decimal,
        tax_amount: Optional[Decimal] = None,
        gateway: Optional[str] = None,
        currency: str = "ARS",
        deferred: bool = False,
        entry_date: Optional[datetime] = None,
    ) -> Any:
        amt = _q(amount)
        tax = _q(tax_amount or 0)
        net = _q(amt - tax)
        cash_subtype = self._cash_subtype(gateway)
        rev_subtype = "deferred_revenue" if deferred else "subscription_revenue"
        lines = [
            {"account_subtype": cash_subtype, "debit": amt, "description": "Cobro suscripción"},
            {"account_subtype": rev_subtype, "credit": net, "description": "Ingreso suscripción"},
        ]
        if tax > 0:
            lines.append({"account_subtype": "vat_output", "credit": tax,
                          "description": "IVA débito"})
        return await self.ledger.post_entry(
            business_id,
            lines,
            entry_date=entry_date,
            memo="Cobro de suscripción",
            source=JournalSource.SUBSCRIPTION.value,
            source_ref=charge_ref,
            idempotency_key=f"subscription:{business_id}:{charge_ref}",
            currency=currency,
        )

    # ------------------------------------------------------------------
    async def post_expense(
        self,
        business_id: uuid.UUID,
        *,
        expense_subtype: str,
        amount: Decimal,
        expense_ref: str,
        vat_credit: Optional[Decimal] = None,
        on_credit: bool = False,
        currency: str = "ARS",
        entry_date: Optional[datetime] = None,
        vendor_id: Optional[uuid.UUID] = None,
        memo: Optional[str] = None,
    ) -> Any:
        amt = _q(amount)
        vat = _q(vat_credit or 0)
        net = _q(amt - vat)
        credit_subtype = "accounts_payable" if on_credit else "cash"
        lines: list[dict[str, Any]] = [
            {"account_subtype": expense_subtype, "debit": net,
             "description": memo or expense_subtype,
             "contact_type": "vendor", "contact_id": vendor_id},
        ]
        if vat > 0:
            lines.append({"account_subtype": "vat_input", "debit": vat,
                          "description": "IVA crédito fiscal"})
        lines.append({"account_subtype": credit_subtype, "credit": amt,
                      "description": "Pago" if not on_credit else "A pagar",
                      "contact_type": "vendor", "contact_id": vendor_id})
        return await self.ledger.post_entry(
            business_id,
            lines,
            entry_date=entry_date,
            memo=memo or f"Gasto {expense_subtype}",
            source=JournalSource.ADJUSTMENT.value if expense_subtype == "misc_expenses"
            else JournalSource.MANUAL.value,
            source_ref=expense_ref,
            idempotency_key=f"expense:{business_id}:{expense_ref}",
            currency=currency,
        )

    # ------------------------------------------------------------------
    async def backfill_orders(self, business_id: uuid.UUID, limit: int = 500) -> dict[str, Any]:
        """One-shot: post ledger entries for already-paid orders that predate
        the ledger going live. Safe to re-run (idempotent per order)."""
        from sqlalchemy import select

        from app.domains.orders.models import Order, PaymentStatus

        res = await self.db.execute(
            select(Order).where(
                Order.business_id == business_id,
                Order.payment_status == PaymentStatus.COMPLETED,
            ).limit(limit)
        )
        orders = res.scalars().all()
        posted = 0
        for o in orders:
            try:
                await self.post_order_paid(
                    business_id,
                    order_id=o.id,
                    total_amount=o.total_amount or Decimal("0"),
                    tax_amount=o.tax_amount,
                    discount_amount=o.discount_amount,
                    gateway=o.payment_gateway or o.payment_method,
                    currency=o.currency or "ARS",
                    entry_date=o.paid_at,
                )
                posted += 1
            except Exception as e:  # noqa: BLE001
                logger.warning("backfill_orders: skipped order %s: %s", o.id, e)
        return {"orders_seen": len(orders), "entries_posted_or_existing": posted}
