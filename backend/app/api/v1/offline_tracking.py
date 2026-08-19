"""API endpoints for offline conversion tracking and analytics."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.core.security import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business
from app.domains.analytics.offline_service import OfflineAnalyticsService
from app.domains.analytics.offline_schemas import (
    OfflineConversionCreate, OfflineConversionResponse, ProximityEventCreate,
    ProximityEventResponse, FootTrafficHeatmapResponse, ConversionFunnelResponse,
    ProximityEffectivenessResponse
)
from app.domains.analytics.offline_models import VisitType, DemographicSource

router = APIRouter(prefix="/api/v1", tags=["offline-tracking"])


@router.post("/offline-conversions", response_model=OfflineConversionResponse, status_code=status.HTTP_201_CREATED)
async def log_offline_visit(
    conversion_data: OfflineConversionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OfflineConversionResponse:
    """Log a visitor to physical location."""

    # Verify business ownership via location
    location = db.query("Location").filter("Location.id" == conversion_data.location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    business = db.query(Business).filter(
        Business.id == location.business_id,
        Business.user_id == current_user.id
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this location"
        )

    # Log the visit
    conversion = OfflineAnalyticsService.log_visit(
        business_id=business.id,
        location_id=conversion_data.location_id,
        visit_type=conversion_data.visit_type,
        visitor_phone=conversion_data.visitor_phone,
        visitor_email=conversion_data.visitor_email,
        visitor_name=conversion_data.visitor_name,
        visitor_latitude=conversion_data.visitor_latitude,
        visitor_longitude=conversion_data.visitor_longitude,
        visitor_ip=conversion_data.visitor_ip_address,
        demographic_source=conversion_data.demographic_source,
        confidence_score=conversion_data.confidence_score,
        conversation_id=conversion_data.conversation_id,
        purchased=conversion_data.purchased,
        purchase_amount=conversion_data.purchase_amount,
        db=db
    )

    return OfflineConversionResponse.model_validate(conversion)


@router.patch("/offline-conversions/{conversion_id}", response_model=OfflineConversionResponse)
async def end_offline_visit(
    conversion_id: UUID,
    purchased: bool = Query(False),
    purchase_amount: float = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> OfflineConversionResponse:
    """Mark end of visit or update purchase info."""

    from app.domains.analytics.offline_models import OfflineConversion
    from decimal import Decimal

    conversion = db.query(OfflineConversion).filter(OfflineConversion.id == conversion_id).first()

    if not conversion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Offline conversion not found"
        )

    # Verify authorization
    business = db.query(Business).filter(
        Business.id == conversion.business_id,
        Business.user_id == current_user.id
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    # End the visit
    updated = OfflineAnalyticsService.end_visit(
        conversion_id=conversion_id,
        purchased=purchased,
        purchase_amount=Decimal(str(purchase_amount)) if purchase_amount else None,
        db=db
    )

    return OfflineConversionResponse.model_validate(updated)


@router.post("/proximity-events", response_model=ProximityEventResponse, status_code=status.HTTP_201_CREATED)
async def log_proximity_event(
    event_data: ProximityEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProximityEventResponse:
    """Log proximity trigger event."""

    from app.domains.businesses.location_models import Location

    # Verify business ownership
    location = db.query(Location).filter(Location.id == event_data.location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    business = db.query(Business).filter(
        Business.id == location.business_id,
        Business.user_id == current_user.id
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    # Log the proximity event
    event = OfflineAnalyticsService.log_proximity_event(
        business_id=business.id,
        location_id=event_data.location_id,
        conversation_id=event_data.conversation_id,
        user_latitude=event_data.user_latitude,
        user_longitude=event_data.user_longitude,
        distance_km=event_data.distance_km,
        trigger_name=event_data.trigger_name,
        visitor_phone=event_data.visitor_phone,
        visitor_email=event_data.visitor_email,
        automation_id=event_data.automation_id,
        db=db
    )

    return ProximityEventResponse.model_validate(event)


@router.get("/locations/{location_id}/foot-traffic-heatmap", response_model=FootTrafficHeatmapResponse)
async def get_foot_traffic_heatmap(
    location_id: UUID,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FootTrafficHeatmapResponse:
    """Get hourly foot traffic heatmap for location."""

    from app.domains.businesses.location_models import Location

    location = db.query(Location).filter(Location.id == location_id).first()
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Location not found"
        )

    business = db.query(Business).filter(
        Business.id == location.business_id,
        Business.user_id == current_user.id
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    heatmap = OfflineAnalyticsService.get_foot_traffic_heatmap(location_id, days, db)

    return FootTrafficHeatmapResponse(
        location_id=heatmap["location_id"],
        period_days=heatmap["period_days"],
        hourly_heatmap=heatmap["hourly_heatmap"]
    )


@router.get("/businesses/{business_id}/conversion-funnel", response_model=ConversionFunnelResponse)
async def get_conversion_funnel(
    business_id: UUID,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConversionFunnelResponse:
    """Get online→offline→purchase funnel for business."""

    business = db.query(Business).filter(
        Business.id == business_id,
        Business.user_id == current_user.id
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    funnel = OfflineAnalyticsService.get_conversion_funnel(business_id, days, db)

    return ConversionFunnelResponse(**funnel)


@router.get(
    "/proximity-triggers/{trigger_name}/effectiveness",
    response_model=ProximityEffectivenessResponse
)
async def get_trigger_effectiveness(
    business_id: UUID = Query(...),
    trigger_name: str = Query(...),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ProximityEffectivenessResponse:
    """Get effectiveness of proximity trigger."""

    business = db.query(Business).filter(
        Business.id == business_id,
        Business.user_id == current_user.id
    ).first()

    if not business:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized"
        )

    effectiveness = OfflineAnalyticsService.get_proximity_trigger_effectiveness(
        business_id, trigger_name, days, db
    )

    return ProximityEffectivenessResponse(**effectiveness)
