"""BI schemas for offline analytics dashboards."""

from pydantic import BaseModel
from uuid import UUID
from decimal import Decimal
from typing import Optional, List, Dict


class FootTrafficMetrics(BaseModel):
    """Foot traffic metrics for location."""
    location_id: UUID
    location_name: str
    period: str
    date_range: str
    total_visits: int
    walk_in_visits: int
    qr_scans: int
    scheduled_visits: int
    peak_hour: str
    peak_day: Optional[str]
    avg_dwell_minutes: int
    hourly_breakdown: Dict[str, int]
    daily_visits_trend: List[Dict]


class OfflineConversionMetrics(BaseModel):
    """Conversion metrics from offline visits."""
    location_id: UUID
    location_name: str
    total_visits: int
    visits_converted: int
    conversion_rate: float
    total_revenue: Decimal
    avg_order_value: Decimal
    avg_transaction_value: Decimal
    by_visit_type: Dict[str, dict]


class OnlineOfflineAttributionMetrics(BaseModel):
    """Attribution metrics: online→offline→purchase."""
    business_id: UUID
    period: str
    total_online_leads: int
    leads_near_location: int
    proximity_invites_sent: int
    location_visits: int
    location_purchases: int
    online_to_proximity_rate: float
    proximity_to_visit_rate: float
    visit_to_purchase_rate: float
    full_funnel_rate: float
    attributed_revenue: float
    attributed_orders: int
    avg_attributed_order_value: Decimal
    top_online_channels: List[Dict]


class LocationComparisonMetrics(BaseModel):
    """Compare foot traffic + conversion across locations."""
    business_id: UUID
    period: str
    locations: List[Dict]
    highest_traffic: str
    highest_conversion: str
    best_performing_hour: str
    best_performing_day: str


class ProximityTriggerROI(BaseModel):
    """ROI metrics for proximity trigger."""
    business_id: UUID
    trigger_name: str
    period: str
    proximity_events: int
    automations_executed: int
    execution_rate: float
    visits_from_trigger: int
    proximity_to_visit_rate: float
    purchases_from_trigger: int
    proximity_to_purchase_rate: float
    revenue_attributed: Decimal
    cost_per_visit: Decimal
    roi: float


class DashboardSummary(BaseModel):
    """High-level summary for main BI dashboard."""
    business_id: UUID
    period: str
    total_visits: int
    visit_trend: str
    total_conversions: int
    conversion_rate: float
    conversion_trend: str
    total_revenue: Decimal
    revenue_trend: str
    top_location: str
    top_location_visits: int
    best_trigger: str
    best_trigger_roi: float
    peak_hour: str
    peak_day: str
    avg_dwell_minutes: int
    actionable_insights: List[str]


class LocationAnalyticsDetailedReport(BaseModel):
    """Detailed analytics report for single location."""
    location_id: UUID
    location_name: str
    location_address: str
    period_start: str
    period_end: str
    period_days: int
    total_visits: int
    walk_in: int
    qr_scan: int
    scheduled: int
    avg_dwell_minutes: int
    max_dwell_minutes: int
    visitors_purchased: int
    conversion_rate: float
    total_revenue: Decimal
    avg_purchase_value: Decimal
    contact_collection_rate: float
    high_engagement_visitors: int
    hourly_traffic: Dict[str, int]
    daily_visits_trend: List[Dict]
    conversion_trend: List[Dict]
    top_proximity_triggers: List[Dict]
    optimization_recommendations: List[str]
