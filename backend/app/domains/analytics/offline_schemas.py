"""Pydantic schemas for offline conversion API."""

from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from typing import Optional

from app.domains.analytics.offline_models import VisitType, DemographicSource


class OfflineConversionCreate(BaseModel):
    """Create offline conversion record."""
    location_id: UUID
    visit_type: VisitType = VisitType.WALK_IN
    visitor_phone: Optional[str] = None
    visitor_email: Optional[str] = None
    visitor_name: Optional[str] = None
    visitor_latitude: Optional[float] = None
    visitor_longitude: Optional[float] = None
    visitor_ip_address: Optional[str] = None
    demographic_source: Optional[DemographicSource] = None
    confidence_score: float = Field(default=0.5, ge=0, le=1)
    conversation_id: Optional[UUID] = None
    purchased: bool = False
    purchase_amount: Optional[Decimal] = None
    contact_collected: bool = False
    staff_notes: Optional[str] = None


class OfflineConversionUpdate(BaseModel):
    """End visit or update conversion details."""
    exit_time: Optional[datetime] = None
    purchased: Optional[bool] = None
    purchase_amount: Optional[Decimal] = None
    staff_notes: Optional[str] = None


class OfflineConversionResponse(BaseModel):
    """Offline conversion response."""
    id: UUID
    business_id: UUID
    location_id: Optional[UUID]
    visit_type: VisitType
    visitor_phone: Optional[str]
    visitor_email: Optional[str]
    visitor_name: Optional[str]
    visitor_latitude: Optional[float]
    visitor_longitude: Optional[float]
    demographic_source: Optional[DemographicSource]
    confidence_score: float
    entry_time: datetime
    exit_time: Optional[datetime]
    dwell_minutes: Optional[int]
    purchased: bool
    purchase_amount: Optional[Decimal]
    staff_notes: Optional[str]
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
    visitor_phone: Optional[str] = None
    visitor_email: Optional[str] = None
    automation_id: Optional[UUID] = None


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
    automation_executed_at: Optional[datetime]
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
