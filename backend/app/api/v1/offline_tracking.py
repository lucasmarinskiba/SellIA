"""API endpoints for offline conversion tracking and analytics.

Who may do what (see app.core.business_access):

* record a visit, end it or add its purchase, log a proximity event -> any active member of the location's
  business (the staff at the door); a visit or event can only point at a conversation of the same business;
* the heatmap, the conversion funnel and a trigger's effectiveness are dashboards -> the owner or an ADMIN
  member.

The services are sync (Session.query / commit) while get_db yields an AsyncSession, so every DB touch runs
inside ``await db.run_sync(...)``. Access checks run before the try block so a 403/404 is not turned into a
400 by the broad except. The response is built inside the sync call: the ORM objects are expired after the
commit and must not be read back in async code.
"""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_business_access, require_location_access
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.analytics.offline_models import OfflineConversion
from app.domains.analytics.offline_schemas import (
    ConversionFunnelResponse,
    FootTrafficHeatmapResponse,
    OfflineConversionCreate,
    OfflineConversionResponse,
    ProximityEffectivenessResponse,
    ProximityEventCreate,
    ProximityEventResponse,
)
from app.domains.analytics.offline_service import OfflineAnalyticsService
from app.domains.bi import offline_metrics
from app.domains.channels.models import Conversation
from app.domains.users.models import User

router = APIRouter(prefix="", tags=["offline-tracking"])


async def _require_same_business_conversation(
    db: AsyncSession, conversation_id: UUID | None, business_id: UUID
) -> None:
    """A conversation id from the request must belong to the business the visit is recorded for."""
    if conversation_id is None:
        return
    conversation = await db.get(Conversation, conversation_id)
    if conversation is None or conversation.business_id != business_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversación no encontrada")


@router.post("/offline-conversions", response_model=OfflineConversionResponse, status_code=status.HTTP_201_CREATED)
async def log_offline_visit(
    conversion_data: OfflineConversionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OfflineConversionResponse:
    """Log a visitor to a physical location."""
    location = await require_location_access(db, conversion_data.location_id, current_user)
    business_id, location_id = location.business_id, location.id
    await _require_same_business_conversation(db, conversion_data.conversation_id, business_id)

    try:
        return await db.run_sync(
            lambda sync_db: OfflineConversionResponse.model_validate(
                OfflineAnalyticsService.log_visit(
                    business_id=business_id,
                    location_id=location_id,
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
                    db=sync_db,
                )
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/offline-conversions/{conversion_id}", response_model=OfflineConversionResponse)
async def end_offline_visit(
    conversion_id: UUID,
    purchased: bool = Query(False),
    purchase_amount: float | None = Query(None, ge=0, le=10_000_000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OfflineConversionResponse:
    """Mark the end of a visit, or record its purchase (which may come after the visit ended)."""
    conversion = await db.get(OfflineConversion, conversion_id)
    if conversion is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visita no encontrada")
    if conversion.location_id is not None:
        await require_location_access(db, conversion.location_id, current_user)
    else:  # the location was deleted (ON DELETE SET NULL): the business still owns the record
        await require_business_access(db, conversion.business_id, current_user)

    try:
        return await db.run_sync(
            lambda sync_db: OfflineConversionResponse.model_validate(
                OfflineAnalyticsService.end_visit(
                    conversion_id=conversion_id,
                    purchased=purchased,
                    purchase_amount=Decimal(str(purchase_amount)) if purchase_amount is not None else None,
                    db=sync_db,
                )
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/proximity-events", response_model=ProximityEventResponse, status_code=status.HTTP_201_CREATED)
async def log_proximity_event(
    event_data: ProximityEventCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProximityEventResponse:
    """Log proximity trigger event."""
    location = await require_location_access(db, event_data.location_id, current_user)
    business_id, location_id = location.business_id, location.id
    await _require_same_business_conversation(db, event_data.conversation_id, business_id)

    try:
        return await db.run_sync(
            lambda sync_db: ProximityEventResponse.model_validate(
                OfflineAnalyticsService.log_proximity_event(
                    business_id=business_id,
                    location_id=location_id,
                    conversation_id=event_data.conversation_id,
                    user_latitude=event_data.user_latitude,
                    user_longitude=event_data.user_longitude,
                    distance_km=event_data.distance_km,
                    trigger_name=event_data.trigger_name,
                    visitor_phone=event_data.visitor_phone,
                    visitor_email=event_data.visitor_email,
                    automation_id=event_data.automation_id,
                    db=sync_db,
                )
            )
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/foot-traffic-heatmap", response_model=FootTrafficHeatmapResponse)
async def get_foot_traffic_heatmap(
    location_id: UUID,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FootTrafficHeatmapResponse:
    """Hourly foot traffic heatmap for a location (a dashboard: owner or admin)."""
    await require_location_access(db, location_id, current_user, manage=True)
    now = datetime.now(timezone.utc)

    metrics = await db.run_sync(
        lambda sync_db: offline_metrics.location_foot_traffic(sync_db, location_id, days, now)
    )
    return FootTrafficHeatmapResponse(
        location_id=location_id,
        period_days=days,
        hourly_heatmap=metrics["hourly_breakdown"],
    )


@router.get("/businesses/{business_id}/conversion-funnel", response_model=ConversionFunnelResponse)
async def get_conversion_funnel(
    business_id: UUID,
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversionFunnelResponse:
    """Online→offline→purchase funnel for a business (a dashboard: owner or admin)."""
    await require_business_access(db, business_id, current_user, manage=True)

    funnel = await db.run_sync(
        lambda sync_db: OfflineAnalyticsService.get_conversion_funnel(business_id, days, sync_db)
    )
    return ConversionFunnelResponse(**funnel)


@router.get(
    "/proximity-triggers/{trigger_name}/effectiveness",
    response_model=ProximityEffectivenessResponse,
)
async def get_trigger_effectiveness(
    trigger_name: str = Path(..., max_length=100),
    business_id: UUID = Query(...),
    days: int = Query(30, ge=1, le=365),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ProximityEffectivenessResponse:
    """Effectiveness of one proximity trigger (a dashboard: owner or admin)."""
    await require_business_access(db, business_id, current_user, manage=True)

    effectiveness = await db.run_sync(
        lambda sync_db: OfflineAnalyticsService.get_proximity_trigger_effectiveness(
            business_id, trigger_name, days, sync_db
        )
    )
    return ProximityEffectivenessResponse(**effectiveness)
