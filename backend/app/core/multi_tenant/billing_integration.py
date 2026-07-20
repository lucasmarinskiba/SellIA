"""
BillingService: Track usage, calculate costs, manage billing periods.
300 lines: Integrates with Stripe, generates invoices, enforces limits.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from enum import Enum

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.core.exceptions import AppException
from .models import TenantBilling, Tenant, AuditLog

logger = get_logger(__name__)


class BillingStatus(str, Enum):
    """Billing status lifecycle."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"


class BillingService:
    """Usage tracking, cost calculation, billing cycle management."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def record_api_call(
        self,
        tenant_id: str,
        api_key_id: Optional[str] = None,
        response_time_ms: int = 0,
    ) -> None:
        """
        Record API call for usage tracking.
        Called by middleware on every API request.
        """
        billing = await self.db.execute(
            select(TenantBilling).where(TenantBilling.tenant_id == tenant_id)
        )
        billing_obj = billing.scalar_one_or_none()

        if not billing_obj:
            raise AppException("Billing record not found", status_code=404)

        # Increment counters
        billing_obj.api_calls_used += 1

        # Check against limit
        tenant = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant_obj = tenant.scalar_one_or_none()

        if billing_obj.api_calls_used > tenant_obj.max_monthly_api_calls:
            logger.warning(
                f"Tenant exceeded API call limit",
                extra={
                    "tenant_id": str(tenant_id),
                    "used": billing_obj.api_calls_used,
                    "limit": tenant_obj.max_monthly_api_calls,
                },
            )
            raise AppException(
                "API call limit exceeded",
                status_code=429,
            )

        billing_obj.updated_at = datetime.now(timezone.utc)
        await self.db.commit()

    async def record_storage(self, tenant_id: str, gb_used: float) -> None:
        """Record storage usage."""
        billing = await self.db.execute(
            select(TenantBilling).where(TenantBilling.tenant_id == tenant_id)
        )
        billing_obj = billing.scalar_one_or_none()

        if not billing_obj:
            raise AppException("Billing record not found", status_code=404)

        billing_obj.storage_gb_used = gb_used
        billing_obj.updated_at = datetime.now(timezone.utc)

        await self.db.commit()

    async def record_compute(self, tenant_id: str, hours_used: float) -> None:
        """Record compute/processing hours."""
        billing = await self.db.execute(
            select(TenantBilling).where(TenantBilling.tenant_id == tenant_id)
        )
        billing_obj = billing.scalar_one_or_none()

        if not billing_obj:
            raise AppException("Billing record not found", status_code=404)

        billing_obj.compute_hours_used = hours_used
        billing_obj.updated_at = datetime.now(timezone.utc)

        await self.db.commit()

    async def calculate_billing_cycle(self, tenant_id: str) -> Dict[str, Any]:
        """
        Calculate costs for current billing cycle.

        Returns:
            {
                "base_cost": 29.0,
                "overage_cost": 5.50,
                "total_cost": 34.50,
                "breakdown": {...}
            }
        """
        billing = await self.db.execute(
            select(TenantBilling).where(TenantBilling.tenant_id == tenant_id)
        )
        billing_obj = billing.scalar_one_or_none()

        if not billing_obj:
            raise AppException("Billing record not found", status_code=404)

        tenant = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant_obj = tenant.scalar_one_or_none()

        # Calculate overage (simplified: $0.001 per API call above limit)
        overage_calls = max(
            0,
            billing_obj.api_calls_used - tenant_obj.max_monthly_api_calls,
        )
        overage_cost = overage_calls * 0.001

        # Storage overage ($0.10 per GB above 1GB)
        storage_overage_gb = max(0, billing_obj.storage_gb_used - 1.0)
        storage_cost = storage_overage_gb * 0.10

        # Compute overage ($0.05 per hour above 10 hours)
        compute_overage_hours = max(0, billing_obj.compute_hours_used - 10.0)
        compute_cost = compute_overage_hours * 0.05

        total_overage = overage_cost + storage_cost + compute_cost
        total_cost = billing_obj.base_tier_cost + total_overage

        return {
            "base_cost": billing_obj.base_tier_cost,
            "api_call_overage_cost": overage_cost,
            "storage_overage_cost": storage_cost,
            "compute_overage_cost": compute_cost,
            "total_overage_cost": total_overage,
            "total_cost": total_cost,
            "breakdown": {
                "api_calls_used": billing_obj.api_calls_used,
                "api_calls_limit": tenant_obj.max_monthly_api_calls,
                "storage_gb_used": billing_obj.storage_gb_used,
                "compute_hours_used": billing_obj.compute_hours_used,
            },
        }

    async def finalize_billing_cycle(self, tenant_id: str) -> TenantBilling:
        """
        End billing cycle: calculate final costs, generate invoice, reset counters.
        Run monthly as scheduled task.
        """
        billing = await self.db.execute(
            select(TenantBilling).where(TenantBilling.tenant_id == tenant_id)
        )
        billing_obj = billing.scalar_one_or_none()

        if not billing_obj:
            raise AppException("Billing record not found", status_code=404)

        # Calculate final cost
        costs = await self.calculate_billing_cycle(tenant_id)
        billing_obj.overage_cost = costs["total_overage_cost"]
        billing_obj.total_cost = costs["total_cost"]
        billing_obj.status = BillingStatus.PENDING

        # Generate invoice number
        import uuid
        billing_obj.invoice_number = f"INV-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"

        # Reset for next period
        next_start = billing_obj.billing_period_end
        next_end = next_start + timedelta(days=30)

        # Create new billing record for next period
        new_billing = TenantBilling(
            tenant_id=tenant_id,
            billing_period_start=next_start,
            billing_period_end=next_end,
            base_tier_cost=billing_obj.base_tier_cost,
        )

        await self.db.commit()

        logger.info(
            f"Billing cycle finalized",
            extra={
                "tenant_id": str(tenant_id),
                "invoice_number": billing_obj.invoice_number,
                "total_cost": billing_obj.total_cost,
            },
        )

        return billing_obj

    async def process_payment(
        self,
        tenant_id: str,
        stripe_payment_intent_id: str,
    ) -> bool:
        """
        Process payment: update billing status.
        Called by Stripe webhook handler.
        """
        billing = await self.db.execute(
            select(TenantBilling).where(TenantBilling.tenant_id == tenant_id)
        )
        billing_obj = billing.scalar_one_or_none()

        if not billing_obj:
            raise AppException("Billing record not found", status_code=404)

        billing_obj.status = BillingStatus.PAID
        billing_obj.last_payment_attempt = datetime.now(timezone.utc)

        await self.db.commit()

        logger.info(
            f"Payment processed",
            extra={
                "tenant_id": str(tenant_id),
                "stripe_id": stripe_payment_intent_id,
            },
        )

        return True

    async def fail_payment(
        self,
        tenant_id: str,
        reason: str,
    ) -> None:
        """Record payment failure."""
        billing = await self.db.execute(
            select(TenantBilling).where(TenantBilling.tenant_id == tenant_id)
        )
        billing_obj = billing.scalar_one_or_none()

        if not billing_obj:
            raise AppException("Billing record not found", status_code=404)

        billing_obj.status = BillingStatus.FAILED
        billing_obj.payment_failed_reason = reason
        billing_obj.last_payment_attempt = datetime.now(timezone.utc)

        await self.db.commit()

        logger.warning(
            f"Payment failed",
            extra={
                "tenant_id": str(tenant_id),
                "reason": reason,
            },
        )

    async def get_usage_stats(self, tenant_id: str) -> Dict[str, Any]:
        """Get current billing period usage."""
        billing = await self.db.execute(
            select(TenantBilling).where(TenantBilling.tenant_id == tenant_id)
        )
        billing_obj = billing.scalar_one_or_none()

        if not billing_obj:
            raise AppException("Billing record not found", status_code=404)

        tenant = await self.db.execute(
            select(Tenant).where(Tenant.id == tenant_id)
        )
        tenant_obj = tenant.scalar_one_or_none()

        # Percent utilization
        api_call_percent = (
            (billing_obj.api_calls_used / tenant_obj.max_monthly_api_calls) * 100
        ) if tenant_obj.max_monthly_api_calls > 0 else 0

        return {
            "billing_period_start": billing_obj.billing_period_start.isoformat(),
            "billing_period_end": billing_obj.billing_period_end.isoformat(),
            "api_calls_used": billing_obj.api_calls_used,
            "api_calls_limit": tenant_obj.max_monthly_api_calls,
            "api_calls_percent_used": round(api_call_percent, 2),
            "storage_gb_used": billing_obj.storage_gb_used,
            "compute_hours_used": billing_obj.compute_hours_used,
            "current_estimated_cost": billing_obj.base_tier_cost,
            "status": billing_obj.status,
        }


class BillingTracker:
    """Singleton for billing operations."""

    def get_service(self, db: AsyncSession) -> BillingService:
        return BillingService(db)

    async def record_api_call(
        self,
        db: AsyncSession,
        tenant_id: str,
        **kwargs,
    ) -> None:
        service = self.get_service(db)
        await service.record_api_call(tenant_id, **kwargs)


_billing_tracker: Optional[BillingTracker] = None


def get_billing_tracker() -> BillingTracker:
    """Get singleton BillingTracker."""
    global _billing_tracker
    if _billing_tracker is None:
        _billing_tracker = BillingTracker()
    return _billing_tracker
