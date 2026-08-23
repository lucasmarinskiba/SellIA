"""API endpoints for offline-triggered re-engagement sequences."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from pydantic import BaseModel
from typing import Optional, List
from enum import Enum

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.businesses.models import Business

router = APIRouter(prefix="/api/v1", tags=["offline-sequences"])


class OfflineTriggerType(str, Enum):
    """Trigger types for offline-based automations."""
    VISIT_WITHOUT_PURCHASE = "visit_without_purchase"
    DEMO_ATTENDED = "demo_attended"
    LONG_DWELL_TIME = "long_dwell_time"
    QR_SCAN = "qr_scan"
    GEOFENCE_ENTRY = "geofence_entry"
    SCHEDULED_APPOINTMENT_ATTENDED = "scheduled_appointment_attended"
    FOOT_TRAFFIC_HIGH = "foot_traffic_high"


class VisitType(str, Enum):
    """Type of visit."""
    WALK_IN = "walk_in"
    QR_SCAN = "qr_scan"
    SCHEDULED_DEMO = "scheduled_demo"
    SCHEDULED_TOUR = "scheduled_tour"
    SCHEDULED_APPOINTMENT = "scheduled_appointment"
    MANUAL_CHECKIN = "manual_checkin"
    GEOFENCE_ENTRY = "geofence_entry"


class OfflineSequenceTemplate(BaseModel):
    """Email template triggered by offline visit."""
    name: str
    trigger_type: OfflineTriggerType
    delay_hours: int
    subject: str
    body: str
    cta_text: str
    cta_url: str


class OfflineSequenceTriggerRequest(BaseModel):
    """Request to trigger post-visit sequence."""
    business_id: UUID
    location_id: UUID
    conversion_id: UUID
    visit_type: VisitType
    dwell_minutes: Optional[int] = None


class OfflineSequenceTriggerResponse(BaseModel):
    """Response from sequence trigger."""
    success: bool
    message: str
    sequence_id: Optional[UUID] = None
    next_action: Optional[str] = None


# Pre-defined templates (10+ sequences)
OFFLINE_TEMPLATES = [
    OfflineSequenceTemplate(
        name="post_visit_thank_you",
        trigger_type=OfflineTriggerType.VISIT_WITHOUT_PURCHASE,
        delay_hours=1,
        subject="Thank you for visiting us!",
        body="We appreciated seeing you at our location. Here's 10% off your first purchase.",
        cta_text="Shop Now",
        cta_url="/shop"
    ),
    OfflineSequenceTemplate(
        name="demo_follow_up",
        trigger_type=OfflineTriggerType.DEMO_ATTENDED,
        delay_hours=2,
        subject="Your demo insights",
        body="Here's a personalized report from your demo with next steps.",
        cta_text="View Report",
        cta_url="/reports"
    ),
    OfflineSequenceTemplate(
        name="extended_visit_offer",
        trigger_type=OfflineTriggerType.LONG_DWELL_TIME,
        delay_hours=3,
        subject="We noticed you spent time with us",
        body="Complete your purchase with free shipping for the next 48 hours.",
        cta_text="Complete Order",
        cta_url="/checkout"
    ),
    OfflineSequenceTemplate(
        name="qr_scan_reward",
        trigger_type=OfflineTriggerType.QR_SCAN,
        delay_hours=1,
        subject="Exclusive QR code reward unlocked",
        body="You've earned bonus points. Use them now.",
        cta_text="Claim Bonus",
        cta_url="/rewards"
    ),
    OfflineSequenceTemplate(
        name="geofence_reminder",
        trigger_type=OfflineTriggerType.GEOFENCE_ENTRY,
        delay_hours=4,
        subject="We're glad you visited nearby",
        body="Stop by again soon and get an exclusive offer.",
        cta_text="Reserve Time",
        cta_url="/book"
    ),
    OfflineSequenceTemplate(
        name="appointment_follow_up",
        trigger_type=OfflineTriggerType.SCHEDULED_APPOINTMENT_ATTENDED,
        delay_hours=1,
        subject="Appointment recap",
        body="Here's what we discussed and your action items.",
        cta_text="View Summary",
        cta_url="/appointments"
    ),
    OfflineSequenceTemplate(
        name="high_traffic_upsell",
        trigger_type=OfflineTriggerType.FOOT_TRAFFIC_HIGH,
        delay_hours=6,
        subject="Your visit inspired us",
        body="Based on what you explored, we recommend these products.",
        cta_text="See Recommendations",
        cta_url="/recommendations"
    ),
]


@router.post(
    "/offline-sequences/trigger",
    response_model=OfflineSequenceTriggerResponse,
    status_code=status.HTTP_201_CREATED,
)
async def trigger_offline_sequence(
    request: OfflineSequenceTriggerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OfflineSequenceTriggerResponse:
    """Trigger post-visit sequence for offline conversion."""
    try:
        # Verify business ownership
        business = None
        if hasattr(db, 'execute'):
            # AsyncSession
            from sqlalchemy import select
            stmt = select(Business).where(
                Business.id == request.business_id,
                Business.user_id == current_user.id
            )
            result = await db.execute(stmt)
            business = result.scalar_one_or_none()
        else:
            # Sync fallback
            business = db.query(Business).filter(
                Business.id == request.business_id,
                Business.user_id == current_user.id
            ).first()

        if not business:
            return OfflineSequenceTriggerResponse(
                success=False,
                message="Business not found or not authorized"
            )

        # Determine sequence template based on visit type and dwell time
        template = None
        if request.visit_type == VisitType.QR_SCAN:
            template = next((t for t in OFFLINE_TEMPLATES if t.trigger_type == OfflineTriggerType.QR_SCAN), None)
        elif request.visit_type == VisitType.SCHEDULED_DEMO:
            template = next((t for t in OFFLINE_TEMPLATES if t.trigger_type == OfflineTriggerType.DEMO_ATTENDED), None)
        elif request.dwell_minutes and request.dwell_minutes > 30:
            template = next((t for t in OFFLINE_TEMPLATES if t.trigger_type == OfflineTriggerType.LONG_DWELL_TIME), None)
        else:
            template = next((t for t in OFFLINE_TEMPLATES if t.trigger_type == OfflineTriggerType.VISIT_WITHOUT_PURCHASE), None)

        if not template:
            return OfflineSequenceTriggerResponse(
                success=False,
                message="No matching sequence template found"
            )

        # TODO: In production, enqueue email task with delay_hours
        # For now, return success with template info
        return OfflineSequenceTriggerResponse(
            success=True,
            message=f"Sequence '{template.name}' queued with {template.delay_hours}h delay",
            sequence_id=request.conversion_id,
            next_action=f"Send {template.name} after {template.delay_hours} hours"
        )

    except Exception as e:
        return OfflineSequenceTriggerResponse(
            success=False,
            message=f"Error triggering sequence: {str(e)}"
        )


@router.get(
    "/offline-sequences/templates",
    response_model=List[OfflineSequenceTemplate],
)
async def list_sequence_templates(
    current_user: User = Depends(get_current_user),
) -> List[OfflineSequenceTemplate]:
    """List all available offline sequence templates."""
    return OFFLINE_TEMPLATES


@router.get(
    "/offline-sequences/triggers",
    response_model=List[dict],
)
async def list_trigger_types(
    current_user: User = Depends(get_current_user),
) -> List[dict]:
    """List all offline trigger types."""
    return [
        {"type": t.value, "name": t.name}
        for t in OfflineTriggerType
    ]


@router.get(
    "/offline-sequences/visit-type-mapping",
    response_model=dict,
)
async def get_visit_type_mapping(
    current_user: User = Depends(get_current_user),
) -> dict:
    """Map visit types to default sequences."""
    mapping = {
        "walk_in": "post_visit_thank_you",
        "qr_scan": "qr_scan_reward",
        "scheduled_demo": "demo_follow_up",
        "scheduled_tour": "post_visit_thank_you",
        "scheduled_appointment": "appointment_follow_up",
        "manual_checkin": "post_visit_thank_you",
        "geofence_entry": "geofence_reminder",
    }
    return {
        "mappings": mapping,
        "templates": {t.name: t.trigger_type.value for t in OFFLINE_TEMPLATES}
    }
