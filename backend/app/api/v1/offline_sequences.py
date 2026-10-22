"""API endpoints for offline-triggered re-engagement sequences."""

from enum import Enum
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_business_access
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.analytics.offline_models import OfflineConversion
from app.domains.users.models import User

router = APIRouter(prefix="", tags=["offline-sequences"])


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
    dwell_minutes: int | None = None


class OfflineSequenceTriggerResponse(BaseModel):
    """Response from sequence trigger."""
    success: bool
    message: str
    sequence_id: UUID | None = None
    next_action: str | None = None


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
)
async def trigger_offline_sequence(
    request: OfflineSequenceTriggerRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> OfflineSequenceTriggerResponse:
    """Pick the post-visit sequence for an offline visit (owner or admin).

    This endpoint only SELECTS the template. Nothing is queued or sent: the delivery worker does not exist yet,
    so the response says so with success=false rather than claiming the sequence was scheduled.
    """
    await require_business_access(db, request.business_id, current_user, manage=True)

    conversion = await db.get(OfflineConversion, request.conversion_id)
    if (
        conversion is None
        or conversion.business_id != request.business_id
        or conversion.location_id != request.location_id
    ):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visita no encontrada")

    # The stored visit is the source of truth for its type and dwell time, not the request body.
    visit_type = conversion.visit_type.value
    dwell = conversion.dwell_minutes if conversion.dwell_minutes is not None else request.dwell_minutes
    if visit_type == "qr_scan":
        wanted = OfflineTriggerType.QR_SCAN
    elif visit_type == "scheduled_demo":
        wanted = OfflineTriggerType.DEMO_ATTENDED
    elif dwell and dwell > 30:
        wanted = OfflineTriggerType.LONG_DWELL_TIME
    else:
        wanted = OfflineTriggerType.VISIT_WITHOUT_PURCHASE
    template = next((tpl for tpl in OFFLINE_TEMPLATES if tpl.trigger_type == wanted), None)

    if template is None:
        return OfflineSequenceTriggerResponse(success=False, message="No hay plantilla para este tipo de visita")
    return OfflineSequenceTriggerResponse(
        success=False,
        message=(
            f"Plantilla '{template.name}' seleccionada para la visita. El envío todavía no está conectado: "
            "no se encoló nada."
        ),
    )


@router.get(
    "/offline-sequences/templates",
    response_model=list[OfflineSequenceTemplate],
)
async def list_sequence_templates(
    current_user: User = Depends(get_current_user),
) -> list[OfflineSequenceTemplate]:
    """List all available offline sequence templates."""
    return OFFLINE_TEMPLATES


@router.get(
    "/offline-sequences/triggers",
    response_model=list[dict],
)
async def list_trigger_types(
    current_user: User = Depends(get_current_user),
) -> list[dict]:
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
