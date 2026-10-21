"""Pydantic schemas for offline conversion API."""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from app.domains.analytics.offline_models import DemographicSource, VisitType


class OfflineConversionCreate(BaseModel):
    """Create offline conversion record."""

    location_id: UUID
    visit_type: VisitType = VisitType.WALK_IN
    visitor_phone: str | None = None
    visitor_email: str | None = None
    visitor_name: str | None = None
    visitor_latitude: float | None = None
    visitor_longitude: float | None = None
    visitor_ip_address: str | None = None
    demographic_source: DemographicSource | None = None
    confidence_score: float = Field(default=0.5, ge=0, le=1)
    conversation_id: UUID | None = None
    purchased: bool = False
    purchase_amount: Decimal | None = None
    contact_collected: bool = False
    staff_notes: str | None = None


class OfflineConversionUpdate(BaseModel):
    """End visit or update conversion details."""

    exit_time: datetime | None = None
    purchased: bool | None = None
    purchase_amount: Decimal | None = None
    staff_notes: str | None = None


class OfflineConversionResponse(BaseModel):
    """Offline conversion response."""

    id: UUID
    business_id: UUID
    location_id: UUID | None
    visit_type: VisitType
    visitor_phone: str | None
    visitor_email: str | None
    visitor_name: str | None
    visitor_latitude: float | None
    visitor_longitude: float | None
    demographic_source: DemographicSource | None
    confidence_score: float
    entry_time: datetime
    exit_time: datetime | None
    dwell_minutes: int | None
    purchased: bool
    purchase_amount: Decimal | None
    staff_notes: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class ProximityEventCreate(BaseModel):
    """Log proximity trigger event."""

    location_id: UUID
    conversation_id: UUID
    user_latitude: float
    user_longitude: float
    distance_km: float
    trigger_name: str
    visitor_phone: str | None = None
    visitor_email: str | None = None
    automation_id: UUID | None = None


class ProximityEventResponse(BaseModel):
    """Proximity event response."""

    id: UUID
    business_id: UUID
    location_id: UUID
    conversation_id: UUID
    user_latitude: float
    user_longitude: float
    distance_km: float
    trigger_name: str
    automation_triggered: bool
    automation_executed_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class LocationVisitMetricsResponse(BaseModel):
    """Daily metrics for a location."""

    location_id: UUID
    metric_date: str
    total_visits: int
    walk_in_visits: int
    qr_scans: int
    scheduled_visits: int
    visitors_converted: int
    total_purchase_value: Decimal
    avg_purchase_value: Decimal
    avg_dwell_minutes: int
    contact_collection_rate: float
    hourly_heatmap: dict

    class Config:
        from_attributes = True


class FootTrafficHeatmapResponse(BaseModel):
    """Hourly foot traffic heatmap."""

    location_id: UUID
    period_days: int
    hourly_heatmap: dict  # {"09": 5, "10": 8, ...}


class ConversionFunnelResponse(BaseModel):
    """Online→Offline→Purchase funnel metrics."""

    period_days: int
    total_visits: int
    visits_linked_to_online: int
    visits_converted_to_purchase: int
    conversion_rate: float
    total_revenue: float
    avg_transaction_value: float


class ProximityEffectivenessResponse(BaseModel):
    """Effectiveness metrics for a proximity trigger."""

    trigger_name: str
    period_days: int
    total_proximity_events: int
    automations_executed: int
    execution_rate: float
    visitor_contacts_captured: int
    visits_from_trigger: int
    trigger_to_visit_rate: float
