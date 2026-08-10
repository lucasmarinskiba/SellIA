"""Phase 14: Real-time analytics and seller dashboard."""

from dataclasses import dataclass, field
from typing import Dict, Any, List
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class SellerMetrics:
    seller_id: str
    period: str  # daily, weekly, monthly
    leads_generated: int = 0
    leads_qualified: int = 0
    conversion_rate: float = 0.0
    deals_closed: int = 0
    revenue_generated: float = 0.0
    avg_deal_size: float = 0.0
    sales_cycle_days: float = 0.0
    churn_rate: float = 0.0
    expansion_rate: float = 0.0
    customer_satisfaction: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ChannelPerformance:
    channel: str
    leads_generated: int = 0
    conversion_rate: float = 0.0
    cost_per_lead: float = 0.0
    roi: float = 0.0
    rank: int = 0  # 1-5, higher is better


@dataclass
class DashboardData:
    seller_id: str
    current_metrics: SellerMetrics
    period_metrics: Dict[str, SellerMetrics]
    channel_performance: List[ChannelPerformance]
    daily_trend: List[Dict[str, Any]]
    top_products: List[Dict[str, Any]]
    top_customers: List[Dict[str, Any]]
    revenue_forecast: Dict[str, float]
    alerts: List[Dict[str, str]]


class SellerAnalyticsEngine:
    """Real-time analytics for sellers"""

    def calculate_metrics(self, seller_id: str, period: str = "daily") -> SellerMetrics:
        """Calculate seller metrics for period"""

        # Mock data - en producción traería de DB
        metrics = SellerMetrics(
            seller_id=seller_id,
            period=period,
            leads_generated=45 if period == "daily" else 315,
            leads_qualified=32,
            conversion_rate=0.71,
            deals_closed=8 if period == "daily" else 45,
            revenue_generated=12500.0 if period == "daily" else 87500.0,
            avg_deal_size=1562.50,
            sales_cycle_days=14.3,
            churn_rate=0.08,
            expansion_rate=0.25,
            customer_satisfaction=4.6
        )

        return metrics

    def get_channel_performance(self, seller_id: str) -> List[ChannelPerformance]:
        """Rank channels by performance"""

        channels = [
            ChannelPerformance(
                channel="google_maps",
                leads_generated=150,
                conversion_rate=0.68,
                cost_per_lead=15.0,
                roi=2.8,
                rank=1
            ),
            ChannelPerformance(
                channel="instagram",
                leads_generated=120,
                conversion_rate=0.55,
                cost_per_lead=8.0,
                roi=2.1,
                rank=2
            ),
            ChannelPerformance(
                channel="whatsapp",
                leads_generated=85,
                conversion_rate=0.72,
                cost_per_lead=0.0,
                roi=3.2,
                rank=1
            ),
            ChannelPerformance(
                channel="email",
                leads_generated=60,
                conversion_rate=0.50,
                cost_per_lead=2.0,
                roi=1.5,
                rank=4
            ),
            ChannelPerformance(
                channel="linkedin",
                leads_generated=40,
                conversion_rate=0.65,
                cost_per_lead=25.0,
                roi=1.3,
                rank=5
            ),
        ]

        return sorted(channels, key=lambda x: x.roi, reverse=True)

    def generate_dashboard(self, seller_id: str) -> DashboardData:
        """Generate complete dashboard data"""

        current = self.calculate_metrics(seller_id, "daily")
        weekly = self.calculate_metrics(seller_id, "weekly")
        monthly = self.calculate_metrics(seller_id, "monthly")

        channels = self.get_channel_performance(seller_id)

        daily_trend = [
            {
                "date": (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d"),
                "leads": 45 + (i * 2),
                "deals": 8 + (i // 2),
                "revenue": 12500 + (i * 500)
            }
            for i in range(7)
        ]

        dashboard = DashboardData(
            seller_id=seller_id,
            current_metrics=current,
            period_metrics={
                "daily": current,
                "weekly": weekly,
                "monthly": monthly
            },
            channel_performance=channels,
            daily_trend=daily_trend,
            top_products=[
                {"product": "Premium Plan", "revenue": 25000, "units_sold": 15},
                {"product": "Standard Plan", "revenue": 18000, "units_sold": 30},
                {"product": "Starter Plan", "revenue": 12000, "units_sold": 40},
            ],
            top_customers=[
                {"customer": "Acme Corp", "lifetime_value": 50000, "deals": 8},
                {"customer": "Tech Solutions", "lifetime_value": 35000, "deals": 5},
                {"customer": "Digital Services", "lifetime_value": 28000, "deals": 4},
            ],
            revenue_forecast={
                "7_days": 87500,
                "30_days": 375000,
                "90_days": 1125000,
                "annual": 4500000
            },
            alerts=[
                {"type": "warning", "message": "Conversion rate down 5% this week"},
                {"type": "info", "message": "WhatsApp channel performing best"},
                {"type": "success", "message": "Revenue up 12% vs last month"},
            ]
        )

        return dashboard
