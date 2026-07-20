"""Commission Tracker — Track affiliates sales, payouts, performance."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CommissionStatus(Enum):
    """Commission statuses."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAID = "paid"


@dataclass
class AffiliateCommission:
    """Single commission record."""
    commission_id: str
    affiliate_id: str
    product_id: str
    sale_amount: float
    commission_percentage: float
    commission_amount: float
    platform: str  # hotmart|meli|amazon|etc
    sale_date: str
    status: CommissionStatus = CommissionStatus.PENDING
    approval_date: Optional[str] = None
    payout_date: Optional[str] = None
    notes: str = ""


@dataclass
class AffiliatePerformance:
    """Performance metrics for affiliate."""
    affiliate_id: str
    total_clicks: int = 0
    total_conversions: int = 0
    total_sales_amount: float = 0.0
    total_commissions: float = 0.0
    conversion_rate: float = 0.0
    average_order_value: float = 0.0
    active_products: List[str] = field(default_factory=list)
    top_performing_product: Optional[str] = None
    top_performing_method: Optional[str] = None
    last_sale_date: Optional[str] = None


class CommissionTracker:
    """Track affiliate commissions and performance."""

    def __init__(self):
        self.commissions: Dict[str, AffiliateCommission] = {}
        self.affiliate_performance: Dict[str, AffiliatePerformance] = {}
        self.payout_history: List[Dict[str, Any]] = []

    def record_commission(
        self,
        affiliate_id: str,
        product_id: str,
        sale_amount: float,
        commission_percentage: float,
        platform: str,
    ) -> AffiliateCommission:
        """Record new commission."""
        commission_amount = sale_amount * commission_percentage
        commission_id = f"comm_{affiliate_id}_{product_id}_{len(self.commissions)}"

        commission = AffiliateCommission(
            commission_id=commission_id,
            affiliate_id=affiliate_id,
            product_id=product_id,
            sale_amount=sale_amount,
            commission_percentage=commission_percentage,
            commission_amount=commission_amount,
            platform=platform,
            sale_date=datetime.utcnow().isoformat(),
        )

        self.commissions[commission_id] = commission
        self._update_performance(affiliate_id, commission)

        logger.info(
            f"Recorded commission: {commission_id} (${commission_amount:.2f})"
        )
        return commission

    def approve_commission(self, commission_id: str) -> bool:
        """Approve commission for payout."""
        if commission_id not in self.commissions:
            return False

        commission = self.commissions[commission_id]
        commission.status = CommissionStatus.APPROVED
        commission.approval_date = datetime.utcnow().isoformat()

        logger.info(f"Approved commission: {commission_id}")
        return True

    def process_payout(
        self, affiliate_id: str, method: str = "bank_transfer"
    ) -> Dict[str, Any]:
        """Process payout for affiliate."""
        affiliate_comms = [
            c
            for c in self.commissions.values()
            if c.affiliate_id == affiliate_id and c.status == CommissionStatus.APPROVED
        ]

        if not affiliate_comms:
            return {"status": "no_pending", "amount": 0}

        total_amount = sum(c.commission_amount for c in affiliate_comms)

        payout = {
            "payout_id": f"payout_{affiliate_id}_{datetime.utcnow().timestamp()}",
            "affiliate_id": affiliate_id,
            "amount": total_amount,
            "method": method,
            "commissions": len(affiliate_comms),
            "payout_date": datetime.utcnow().isoformat(),
            "status": "pending",
        }

        self.payout_history.append(payout)

        # Mark commissions as paid
        for comm in affiliate_comms:
            comm.status = CommissionStatus.PAID
            comm.payout_date = payout["payout_date"]

        logger.info(
            f"Processed payout {payout['payout_id']}: ${total_amount:.2f}"
        )
        return payout

    def _update_performance(
        self, affiliate_id: str, commission: AffiliateCommission
    ):
        """Update affiliate performance metrics."""
        if affiliate_id not in self.affiliate_performance:
            self.affiliate_performance[affiliate_id] = AffiliatePerformance(
                affiliate_id=affiliate_id
            )

        perf = self.affiliate_performance[affiliate_id]
        perf.total_conversions += 1
        perf.total_sales_amount += commission.sale_amount
        perf.total_commissions += commission.commission_amount
        perf.last_sale_date = commission.sale_date

        if commission.product_id not in perf.active_products:
            perf.active_products.append(commission.product_id)

        perf.conversion_rate = (
            perf.total_conversions / max(perf.total_clicks, 1)
        )
        perf.average_order_value = (
            perf.total_sales_amount / perf.total_conversions
        )

        # Find top product
        product_commissions = [
            c
            for c in self.commissions.values()
            if c.affiliate_id == affiliate_id
        ]
        if product_commissions:
            top_product = max(
                set(c.product_id for c in product_commissions),
                key=lambda p: sum(
                    c.commission_amount
                    for c in product_commissions
                    if c.product_id == p
                ),
            )
            perf.top_performing_product = top_product

    def get_affiliate_earnings(self, affiliate_id: str) -> Dict[str, Any]:
        """Get total earnings for affiliate."""
        affiliate_comms = [
            c
            for c in self.commissions.values()
            if c.affiliate_id == affiliate_id
        ]

        if not affiliate_comms:
            return {"earned": 0, "pending": 0, "paid": 0}

        earned = sum(c.commission_amount for c in affiliate_comms)
        pending = sum(
            c.commission_amount
            for c in affiliate_comms
            if c.status == CommissionStatus.PENDING
        )
        paid = sum(
            c.commission_amount
            for c in affiliate_comms
            if c.status == CommissionStatus.PAID
        )

        return {
            "total_earned": earned,
            "pending_approval": pending,
            "paid": paid,
            "approved_not_paid": earned - paid - pending,
        }

    def get_leaderboard(self, period_days: int = 30, top_n: int = 10) -> List[Dict]:
        """Get top affiliates by earnings in period."""
        cutoff_date = datetime.utcnow() - timedelta(days=period_days)
        cutoff_iso = cutoff_date.isoformat()

        earnings_by_affiliate = {}
        for comm in self.commissions.values():
            if comm.sale_date >= cutoff_iso:
                if comm.affiliate_id not in earnings_by_affiliate:
                    earnings_by_affiliate[comm.affiliate_id] = 0
                earnings_by_affiliate[comm.affiliate_id] += comm.commission_amount

        sorted_affiliates = sorted(
            earnings_by_affiliate.items(), key=lambda x: x[1], reverse=True
        )

        leaderboard = []
        for rank, (affiliate_id, earnings) in enumerate(sorted_affiliates[:top_n], 1):
            perf = self.affiliate_performance.get(affiliate_id)
            leaderboard.append(
                {
                    "rank": rank,
                    "affiliate_id": affiliate_id,
                    "earnings": earnings,
                    "conversions": perf.total_conversions if perf else 0,
                    "conversion_rate": perf.conversion_rate if perf else 0,
                    "top_product": perf.top_performing_product if perf else None,
                }
            )

        return leaderboard

    def get_performance_report(self, affiliate_id: str) -> Dict[str, Any]:
        """Get detailed performance report for affiliate."""
        perf = self.affiliate_performance.get(affiliate_id)
        earnings = self.get_affiliate_earnings(affiliate_id)

        if not perf:
            return {"status": "no_data"}

        return {
            "affiliate_id": affiliate_id,
            "total_clicks": perf.total_clicks,
            "total_conversions": perf.total_conversions,
            "conversion_rate": f"{perf.conversion_rate * 100:.2f}%",
            "average_order_value": f"${perf.average_order_value:.2f}",
            "total_sales": f"${perf.total_sales_amount:.2f}",
            "earnings": earnings,
            "active_products": perf.active_products,
            "top_product": perf.top_performing_product,
            "last_sale": perf.last_sale_date,
        }

    def get_product_performance(self, product_id: str) -> Dict[str, Any]:
        """Get performance metrics for product across all affiliates."""
        product_comms = [
            c for c in self.commissions.values() if c.product_id == product_id
        ]

        if not product_comms:
            return {"status": "no_data"}

        total_conversions = len(product_comms)
        total_commission = sum(c.commission_amount for c in product_comms)
        total_sales = sum(c.sale_amount for c in product_comms)

        top_affiliate = max(
            set(c.affiliate_id for c in product_comms),
            key=lambda a: sum(
                c.commission_amount for c in product_comms if c.affiliate_id == a
            ),
        )

        return {
            "product_id": product_id,
            "total_conversions": total_conversions,
            "total_sales": f"${total_sales:.2f}",
            "total_commissions_paid": f"${total_commission:.2f}",
            "average_commission_per_sale": f"${total_commission / total_conversions:.2f}",
            "top_affiliate": top_affiliate,
            "affiliate_count": len(set(c.affiliate_id for c in product_comms)),
        }

    def export_commission_report(self, filename: str) -> bool:
        """Export commission report to CSV."""
        try:
            import csv

            with open(filename, "w", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=[
                        "commission_id",
                        "affiliate_id",
                        "product_id",
                        "sale_amount",
                        "commission_amount",
                        "status",
                        "sale_date",
                    ],
                )
                writer.writeheader()
                for comm in self.commissions.values():
                    writer.writerow(
                        {
                            "commission_id": comm.commission_id,
                            "affiliate_id": comm.affiliate_id,
                            "product_id": comm.product_id,
                            "sale_amount": comm.sale_amount,
                            "commission_amount": comm.commission_amount,
                            "status": comm.status.value,
                            "sale_date": comm.sale_date,
                        }
                    )

            logger.info(f"Exported commission report: {filename}")
            return True
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            return False
