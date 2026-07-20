"""
Commission Tracker v1.0
========================

Track affiliate sales, revenue, and performance:
- Sales per product
- Revenue by method
- ROI per channel
- Seasonality analysis
- Conversion rates
- Customer LTV
- Dashboard & reports

Status: 400L comprehensive tracker
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json

logger = logging.getLogger(__name__)


class SaleStatus(Enum):
    """Sale status."""
    PENDING = "pending"
    APPROVED = "approved"
    PAID = "paid"
    REJECTED = "rejected"
    REFUNDED = "refunded"


class MethodCategory(Enum):
    """Affiliate method categories."""
    EMAIL = "email"
    CONTENT = "content"
    PAID_ADS = "paid_ads"
    PARTNERSHIP = "partnership"
    ORGANIC = "organic"


@dataclass
class AffiliateProduct:
    """Affiliate product information."""
    product_id: str
    name: str
    platform: str  # hotmart, mercado_libre, amazon
    category: str
    price: float
    commission_pct: float
    link: str
    date_added: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "product_id": self.product_id,
            "name": self.name,
            "platform": self.platform,
            "category": self.category,
            "price": self.price,
            "commission_pct": self.commission_pct,
            "link": self.link,
            "date_added": self.date_added.isoformat(),
        }


@dataclass
class AffiliateSale:
    """Individual affiliate sale."""
    sale_id: str
    product_id: str
    method: str  # blog_reviews, email, youtube, etc.
    channel: str  # email_list, blog, twitter, etc.
    sale_date: datetime
    sale_amount: float
    commission_pct: float
    commission_earned: float
    customer_id: Optional[str] = None
    status: SaleStatus = SaleStatus.PENDING
    cost: float = 0.0  # advertising cost or affiliate payout if partnership
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sale_id": self.sale_id,
            "product_id": self.product_id,
            "method": self.method,
            "channel": self.channel,
            "sale_date": self.sale_date.isoformat(),
            "sale_amount": self.sale_amount,
            "commission_pct": self.commission_pct,
            "commission_earned": self.commission_earned,
            "customer_id": self.customer_id,
            "status": self.status.value,
            "cost": self.cost,
            "profit": self.commission_earned - self.cost,
            "roi": ((self.commission_earned - self.cost) / self.cost) if self.cost > 0 else None,
            "notes": self.notes,
        }


class CommissionTracker:
    """Track affiliate sales and performance."""

    def __init__(self):
        self.products: Dict[str, AffiliateProduct] = {}
        self.sales: List[AffiliateSale] = []
        self.created_at = datetime.utcnow()

    def add_product(self, product: AffiliateProduct) -> None:
        """Add affiliate product to track."""
        self.products[product.product_id] = product
        logger.info(f"Added product: {product.name} ({product.product_id})")

    def record_sale(self, sale: AffiliateSale) -> None:
        """Record affiliate sale."""
        if sale.product_id not in self.products:
            logger.warning(f"Product {sale.product_id} not found")
        self.sales.append(sale)
        logger.info(f"Recorded sale: {sale.sale_id} - ${sale.commission_earned:.2f}")

    def get_sales_by_product(self, product_id: str) -> List[AffiliateSale]:
        """Get all sales for a product."""
        return [s for s in self.sales if s.product_id == product_id]

    def get_sales_by_method(self, method: str) -> List[AffiliateSale]:
        """Get all sales for a method."""
        return [s for s in self.sales if s.method == method]

    def get_sales_by_channel(self, channel: str) -> List[AffiliateSale]:
        """Get all sales for a channel."""
        return [s for s in self.sales if s.channel == channel]

    def get_sales_by_status(self, status: SaleStatus) -> List[AffiliateSale]:
        """Get all sales with status."""
        return [s for s in self.sales if s.status == status]

    def get_sales_by_date_range(self, start: datetime, end: datetime) -> List[AffiliateSale]:
        """Get sales in date range."""
        return [s for s in self.sales if start <= s.sale_date <= end]

    def get_product_performance(self, product_id: str) -> Dict[str, Any]:
        """Get detailed performance for a product."""
        product = self.products.get(product_id)
        if not product:
            return {}

        sales = self.get_sales_by_product(product_id)
        approved_sales = [s for s in sales if s.status in [SaleStatus.APPROVED, SaleStatus.PAID]]

        total_sales = len(sales)
        total_approved = len(approved_sales)
        total_commission = sum(s.commission_earned for s in approved_sales)
        total_cost = sum(s.cost for s in approved_sales)
        net_profit = total_commission - total_cost

        approval_rate = (total_approved / total_sales * 100) if total_sales > 0 else 0

        return {
            "product_id": product_id,
            "product_name": product.name,
            "platform": product.platform,
            "commission_pct": product.commission_pct,
            "total_sales": total_sales,
            "approved_sales": total_approved,
            "approval_rate": f"{approval_rate:.1f}%",
            "total_commission_earned": f"${total_commission:.2f}",
            "total_cost": f"${total_cost:.2f}",
            "net_profit": f"${net_profit:.2f}",
            "average_commission_per_sale": f"${total_commission / total_approved:.2f}" if total_approved > 0 else "$0",
            "roi": f"{(net_profit / total_cost * 100):.1f}%" if total_cost > 0 else "0%",
        }

    def get_method_performance(self, method: str) -> Dict[str, Any]:
        """Get performance for a method."""
        sales = self.get_sales_by_method(method)
        approved_sales = [s for s in sales if s.status in [SaleStatus.APPROVED, SaleStatus.PAID]]

        total_sales = len(sales)
        total_commission = sum(s.commission_earned for s in approved_sales)
        total_cost = sum(s.cost for s in approved_sales)
        net_profit = total_commission - total_cost

        methods_breakdown = {}
        for sale in approved_sales:
            if sale.channel not in methods_breakdown:
                methods_breakdown[sale.channel] = {"count": 0, "commission": 0}
            methods_breakdown[sale.channel]["count"] += 1
            methods_breakdown[sale.channel]["commission"] += sale.commission_earned

        return {
            "method": method,
            "total_sales": total_sales,
            "approved_sales": len(approved_sales),
            "total_commission_earned": f"${total_commission:.2f}",
            "total_cost": f"${total_cost:.2f}",
            "net_profit": f"${net_profit:.2f}",
            "average_commission_per_sale": f"${total_commission / len(approved_sales):.2f}" if approved_sales else "$0",
            "roi": f"{(net_profit / total_cost * 100):.1f}%" if total_cost > 0 else "0%",
            "channel_breakdown": methods_breakdown,
        }

    def get_channel_performance(self, channel: str) -> Dict[str, Any]:
        """Get performance for a channel (email, blog, youtube, etc.)."""
        sales = self.get_sales_by_channel(channel)
        approved_sales = [s for s in sales if s.status in [SaleStatus.APPROVED, SaleStatus.PAID]]

        total_sales = len(sales)
        total_commission = sum(s.commission_earned for s in approved_sales)
        total_cost = sum(s.cost for s in approved_sales)
        net_profit = total_commission - total_cost

        # Group by product
        by_product = {}
        for sale in approved_sales:
            if sale.product_id not in by_product:
                by_product[sale.product_id] = {"count": 0, "commission": 0}
            by_product[sale.product_id]["count"] += 1
            by_product[sale.product_id]["commission"] += sale.commission_earned

        return {
            "channel": channel,
            "total_sales": total_sales,
            "approved_sales": len(approved_sales),
            "total_commission_earned": f"${total_commission:.2f}",
            "total_cost": f"${total_cost:.2f}",
            "net_profit": f"${net_profit:.2f}",
            "average_commission_per_sale": f"${total_commission / len(approved_sales):.2f}" if approved_sales else "$0",
            "roi": f"{(net_profit / total_cost * 100):.1f}%" if total_cost > 0 else "0%",
            "top_products_by_channel": sorted(
                [(pid, data["commission"]) for pid, data in by_product.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5],
        }

    def get_conversion_rates(self) -> Dict[str, Any]:
        """Get conversion rates by method and channel."""
        approved_sales = self.get_sales_by_status(SaleStatus.APPROVED)
        approved_sales.extend(self.get_sales_by_status(SaleStatus.PAID))

        # By method
        by_method = {}
        for sale in self.sales:
            if sale.method not in by_method:
                by_method[sale.method] = {"total": 0, "converted": 0}
            by_method[sale.method]["total"] += 1
            if sale.status in [SaleStatus.APPROVED, SaleStatus.PAID]:
                by_method[sale.method]["converted"] += 1

        # By channel
        by_channel = {}
        for sale in self.sales:
            if sale.channel not in by_channel:
                by_channel[sale.channel] = {"total": 0, "converted": 0}
            by_channel[sale.channel]["total"] += 1
            if sale.status in [SaleStatus.APPROVED, SaleStatus.PAID]:
                by_channel[sale.channel]["converted"] += 1

        return {
            "by_method": {
                m: f"{(data['converted'] / data['total'] * 100):.2f}%" if data['total'] > 0 else "0%"
                for m, data in by_method.items()
            },
            "by_channel": {
                c: f"{(data['converted'] / data['total'] * 100):.2f}%" if data['total'] > 0 else "0%"
                for c, data in by_channel.items()
            },
        }

    def get_seasonality(self) -> Dict[str, Any]:
        """Analyze seasonality patterns."""
        approved_sales = self.get_sales_by_status(SaleStatus.APPROVED)
        approved_sales.extend(self.get_sales_by_status(SaleStatus.PAID))

        # Group by month
        by_month = {}
        for sale in approved_sales:
            month_key = sale.sale_date.strftime("%Y-%m")
            if month_key not in by_month:
                by_month[month_key] = {"count": 0, "commission": 0}
            by_month[month_key]["count"] += 1
            by_month[month_key]["commission"] += sale.commission_earned

        # Group by month of year (for seasonality)
        by_month_of_year = {}
        for sale in approved_sales:
            month = sale.sale_date.strftime("%B")
            if month not in by_month_of_year:
                by_month_of_year[month] = {"count": 0, "commission": 0}
            by_month_of_year[month]["count"] += 1
            by_month_of_year[month]["commission"] += sale.commission_earned

        return {
            "by_month": {
                m: {
                    "sales": data["count"],
                    "commission": f"${data['commission']:.2f}"
                }
                for m, data in sorted(by_month.items())
            },
            "by_season": {
                m: f"${data['commission']:.2f}"
                for m, data in sorted(by_month_of_year.items(), key=lambda x: x[1]["commission"], reverse=True)
            },
        }

    def estimate_customer_ltv(self) -> Dict[str, Any]:
        """Estimate customer lifetime value."""
        # Group sales by customer
        by_customer = {}
        for sale in self.sales:
            if sale.customer_id:
                if sale.customer_id not in by_customer:
                    by_customer[sale.customer_id] = []
                by_customer[sale.customer_id].append(sale)

        # Calculate LTV
        ltv_values = []
        repeat_customers = 0
        for customer_id, customer_sales in by_customer.items():
            approved = [s for s in customer_sales if s.status in [SaleStatus.APPROVED, SaleStatus.PAID]]
            if len(approved) > 0:
                ltv = sum(s.commission_earned for s in approved)
                ltv_values.append(ltv)
                if len(approved) > 1:
                    repeat_customers += 1

        if not ltv_values:
            return {
                "unique_customers": 0,
                "repeat_customers": 0,
                "average_ltv": "$0",
                "max_ltv": "$0",
                "repeat_customer_rate": "0%",
            }

        return {
            "unique_customers": len(by_customer),
            "repeat_customers": repeat_customers,
            "repeat_customer_rate": f"{(repeat_customers / len(by_customer) * 100):.1f}%",
            "average_ltv": f"${sum(ltv_values) / len(ltv_values):.2f}",
            "max_ltv": f"${max(ltv_values):.2f}",
            "total_ltv": f"${sum(ltv_values):.2f}",
        }

    def get_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive dashboard."""
        approved_sales = self.get_sales_by_status(SaleStatus.APPROVED)
        approved_sales.extend(self.get_sales_by_status(SaleStatus.PAID))

        total_commission = sum(s.commission_earned for s in approved_sales)
        total_cost = sum(s.cost for s in approved_sales)
        net_profit = total_commission - total_cost

        # Top products
        product_commission = {}
        for sale in approved_sales:
            product_name = self.products.get(sale.product_id, AffiliateProduct(
                sale.product_id, "Unknown", "", "", 0, 0, ""
            )).name
            if product_name not in product_commission:
                product_commission[product_name] = 0
            product_commission[product_name] += sale.commission_earned

        # Top methods
        method_commission = {}
        for sale in approved_sales:
            if sale.method not in method_commission:
                method_commission[sale.method] = 0
            method_commission[sale.method] += sale.commission_earned

        # Top channels
        channel_commission = {}
        for sale in approved_sales:
            if sale.channel not in channel_commission:
                channel_commission[sale.channel] = 0
            channel_commission[sale.channel] += sale.commission_earned

        return {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_sales": len(self.sales),
                "approved_sales": len(approved_sales),
                "total_commission_earned": f"${total_commission:.2f}",
                "total_cost": f"${total_cost:.2f}",
                "net_profit": f"${net_profit:.2f}",
                "approval_rate": f"{(len(approved_sales) / len(self.sales) * 100):.1f}%" if self.sales else "0%",
                "roi": f"{(net_profit / total_cost * 100):.1f}%" if total_cost > 0 else "0%",
            },
            "top_products": sorted(
                [(p, f"${c:.2f}") for p, c in product_commission.items()],
                key=lambda x: float(x[1].replace("$", "")),
                reverse=True
            )[:5],
            "top_methods": sorted(
                [(m, f"${c:.2f}") for m, c in method_commission.items()],
                key=lambda x: float(x[1].replace("$", "")),
                reverse=True
            )[:5],
            "top_channels": sorted(
                [(c, f"${com:.2f}") for c, com in channel_commission.items()],
                key=lambda x: float(x[1].replace("$", "")),
                reverse=True
            )[:5],
            "ltv": self.estimate_customer_ltv(),
            "conversion_rates": self.get_conversion_rates(),
        }

    def get_monthly_report(self, month: int, year: int) -> Dict[str, Any]:
        """Get monthly performance report."""
        start = datetime(year, month, 1)
        if month == 12:
            end = datetime(year + 1, 1, 1)
        else:
            end = datetime(year, month + 1, 1)

        month_sales = self.get_sales_by_date_range(start, end)
        approved_month = [s for s in month_sales if s.status in [SaleStatus.APPROVED, SaleStatus.PAID]]

        total_commission = sum(s.commission_earned for s in approved_month)
        total_cost = sum(s.cost for s in approved_month)

        return {
            "month": f"{start.strftime('%B %Y')}",
            "total_sales": len(month_sales),
            "approved_sales": len(approved_month),
            "total_commission": f"${total_commission:.2f}",
            "total_cost": f"${total_cost:.2f}",
            "net_profit": f"${total_commission - total_cost:.2f}",
            "daily_average": f"${total_commission / (end - start).days:.2f}",
        }


# ============================================================================
# FACTORY FUNCTIONS
# ============================================================================

def create_commission_tracker() -> CommissionTracker:
    """Factory to create commission tracker."""
    return CommissionTracker()


if __name__ == "__main__":
    tracker = create_commission_tracker()

    # Add sample products
    product1 = AffiliateProduct("prod_1", "AI Marketing Course", "hotmart", "courses", 297, 0.40, "https://...")
    product2 = AffiliateProduct("prod_2", "Social Media Templates", "hotmart", "templates", 47, 0.35, "https://...")

    tracker.add_product(product1)
    tracker.add_product(product2)

    # Add sample sales
    now = datetime.utcnow()
    sale1 = AffiliateSale(
        "sale_1", "prod_1", "blog_reviews", "blog",
        now - timedelta(days=5),
        297, 0.40, 118.80,
        customer_id="cust_1",
        status=SaleStatus.APPROVED,
        cost=50
    )
    sale2 = AffiliateSale(
        "sale_2", "prod_1", "email", "newsletter",
        now - timedelta(days=3),
        297, 0.40, 118.80,
        customer_id="cust_2",
        status=SaleStatus.APPROVED,
        cost=0
    )

    tracker.record_sale(sale1)
    tracker.record_sale(sale2)

    print("=== AFFILIATE DASHBOARD ===")
    print(json.dumps(tracker.get_dashboard(), indent=2))
