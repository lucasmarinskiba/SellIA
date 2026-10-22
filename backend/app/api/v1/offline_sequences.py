"""API endpoints for offline-triggered re-engagement sequences."""

from datetime import datetime, timezone
from enum import Enum
from html import escape
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_business_access
from app.core.config import get_settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.analytics.offline_models import OfflineConversion
from app.domains.businesses.location_models import Location
from app.domains.businesses.models import Business
from app.domains.sequences.offline_sequence_jobs import (
    DEFAULT_LANGUAGE,
    queue_post_visit,
    record_opt_out,
    render,
    resolve_language,
    verify_opt_out,
)
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


class OfflineCopy(BaseModel):
    """Subject and body in one language. {negocio} and {sucursal} are filled when the message is queued."""
    subject: str
    body: str


class OfflineSequenceTemplate(BaseModel):
    """Email template triggered by offline visit."""
    name: str
    trigger_type: OfflineTriggerType
    delay_hours: int
    copies: dict[str, OfflineCopy]  # language code -> copy
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
        copies={
            "es": OfflineCopy(
                subject="Gracias por visitarnos",
                body="Hola, gracias por pasar por {sucursal}. Fue un gusto recibirte. Si querés que te ayudemos con algo de lo que viste, respondé este mensaje.",
            ),
            "en": OfflineCopy(
                subject="Thanks for visiting us",
                body="Hi, thanks for stopping by {sucursal}. It was a pleasure having you. If we can help with anything you saw, just reply to this email.",
            ),
        },
        cta_text="Shop Now",
        cta_url="/shop",
    ),
    OfflineSequenceTemplate(
        name="demo_follow_up",
        trigger_type=OfflineTriggerType.DEMO_ATTENDED,
        delay_hours=2,
        copies={
            "es": OfflineCopy(
                subject="Gracias por asistir a la demo",
                body="Gracias por asistir a la demo en {sucursal}. Si querés que te enviemos un resumen y los próximos pasos, respondé este mensaje.",
            ),
            "en": OfflineCopy(
                subject="Thanks for attending the demo",
                body="Thanks for attending the demo at {sucursal}. If you'd like a summary and the next steps, just reply to this email.",
            ),
        },
        cta_text="View Report",
        cta_url="/reports",
    ),
    OfflineSequenceTemplate(
        name="extended_visit_offer",
        trigger_type=OfflineTriggerType.LONG_DWELL_TIME,
        delay_hours=3,
        copies={
            "es": OfflineCopy(
                subject="Gracias por tu tiempo en {sucursal}",
                body="Si tenés alguna duda sobre lo que viste, con gusto te ayudamos a decidir.",
            ),
            "en": OfflineCopy(
                subject="Thanks for your time at {sucursal}",
                body="If you have any questions about what you saw, we're happy to help you decide.",
            ),
        },
        cta_text="Complete Order",
        cta_url="/checkout",
    ),
    OfflineSequenceTemplate(
        name="qr_scan_reward",
        trigger_type=OfflineTriggerType.QR_SCAN,
        delay_hours=1,
        copies={
            "es": OfflineCopy(
                subject="Gracias por escanear el QR",
                body="Gracias por escanear el código en {sucursal}. Si necesitás algo, respondé este mensaje.",
            ),
            "en": OfflineCopy(
                subject="Thanks for scanning our QR code",
                body="Thanks for scanning the code at {sucursal}. If you need anything, just reply to this email.",
            ),
        },
        cta_text="Claim Bonus",
        cta_url="/rewards",
    ),
    OfflineSequenceTemplate(
        name="geofence_reminder",
        trigger_type=OfflineTriggerType.GEOFENCE_ENTRY,
        delay_hours=4,
        copies={
            "es": OfflineCopy(
                subject="Te esperamos de nuevo",
                body="Gracias por visitarnos en {sucursal}. Si querés agendar otra visita, respondé este mensaje.",
            ),
            "en": OfflineCopy(
                subject="We'd love to see you again",
                body="Thanks for visiting {sucursal}. If you'd like to plan another visit, just reply to this email.",
            ),
        },
        cta_text="Reserve Time",
        cta_url="/book",
    ),
    OfflineSequenceTemplate(
        name="appointment_follow_up",
        trigger_type=OfflineTriggerType.SCHEDULED_APPOINTMENT_ATTENDED,
        delay_hours=1,
        copies={
            "es": OfflineCopy(
                subject="Gracias por tu turno",
                body="Gracias por tu turno en {sucursal}. Si necesitás reprogramarlo, respondé este mensaje.",
            ),
            "en": OfflineCopy(
                subject="Thanks for your appointment",
                body="Thanks for your appointment at {sucursal}. If you need to reschedule, just reply to this email.",
            ),
        },
        cta_text="View Summary",
        cta_url="/appointments",
    ),
    OfflineSequenceTemplate(
        name="high_traffic_upsell",
        trigger_type=OfflineTriggerType.FOOT_TRAFFIC_HIGH,
        delay_hours=6,
        copies={
            "es": OfflineCopy(
                subject="Gracias por tu visita a {negocio}",
                body="Si querés saber más sobre nuestros productos, respondé este mensaje.",
            ),
            "en": OfflineCopy(
                subject="Thanks for visiting {negocio}",
                body="If you'd like to know more about our products, just reply to this email.",
            ),
        },
        cta_text="See Recommendations",
        cta_url="/recommendations",
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
    """Queue the post-visit message for an offline visit (owner or admin).

    The message is queued only when sending is enabled and the visit has a contact email. The beat task
    process_offline_sequence_jobs sends it once due. The response says whether anything was queued.
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
    business = await db.get(Business, request.business_id)
    location = await db.get(Location, request.location_id)
    language = resolve_language(business.config if business else None)
    copy = template.copies.get(language, template.copies[DEFAULT_LANGUAGE])
    fill = {
        "business_name": business.name if business else "",
        "location_name": location.name if location else None,
    }
    queued = await queue_post_visit(
        db,
        conversion=conversion,
        template_name=template.name,
        subject=render(copy.subject, **fill),
        body_text=render(copy.body, **fill),
        delay_hours=template.delay_hours,
        enabled=get_settings().OFFLINE_SEQUENCE_SEND_ENABLED,
        now=datetime.now(timezone.utc),
    )
    return OfflineSequenceTriggerResponse(
        success=queued.queued,
        message=f"Plantilla '{template.name}': {queued.message}",
    )


_OPT_OUT_COPY = {
    "es": {
        "ask": "¿Querés dejar de recibir mensajes de {negocio}?",
        "button": "Dar de baja",
        "done": "Listo. No vas a recibir más mensajes de {negocio}.",
    },
    "en": {
        "ask": "Stop receiving messages from {negocio}?",
        "button": "Unsubscribe",
        "done": "Done. You won't receive more messages from {negocio}.",
    },
}


async def _verified_business(db: AsyncSession, business_id: UUID, digest: str, signature: str) -> Business:
    if not verify_opt_out(get_settings().SECRET_KEY, business_id, digest, signature):
        raise HTTPException(status_code=403, detail="Enlace inválido")
    business = await db.get(Business, business_id)
    if business is None:
        raise HTTPException(status_code=404, detail="Negocio no encontrado")
    return business


def _opt_out_page(name: str, language: str, *, done: bool) -> HTMLResponse:
    copy = _OPT_OUT_COPY[language]
    if done:
        body = f"<p>{escape(render(copy['done'], business_name=name))}</p>"
    else:
        # GET changes nothing: mail scanners open links, and must not unsubscribe anyone.
        body = (
            f"<p>{escape(render(copy['ask'], business_name=name))}</p>"
            f'<form method="post"><button type="submit">{escape(copy["button"])}</button></form>'
        )
    return HTMLResponse(
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{escape(name)}</title></head>"
        f'<body style="font-family:sans-serif;padding:24px">{body}</body></html>'
    )


@router.get("/offline-sequences/opt-out", response_class=HTMLResponse)
async def opt_out_page(
    b: UUID,
    h: str = Query(pattern=r"^[0-9a-f]{64}$"),
    s: str = Query(pattern=r"^[0-9a-f]{64}$"),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Confirmation page behind the unsubscribe link in a post-visit message. Public: the signature is the credential."""
    business = await _verified_business(db, b, h, s)
    return _opt_out_page(business.name, resolve_language(business.config), done=False)


@router.post("/offline-sequences/opt-out", response_class=HTMLResponse)
async def opt_out(
    b: UUID,
    h: str = Query(pattern=r"^[0-9a-f]{64}$"),
    s: str = Query(pattern=r"^[0-9a-f]{64}$"),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """Record the unsubscribe. Snapshot the page values first: recording commits, and that can expire the business."""
    business = await _verified_business(db, b, h, s)
    name, language = business.name, resolve_language(business.config)
    await record_opt_out(db, b, h)
    return _opt_out_page(name, language, done=True)


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
