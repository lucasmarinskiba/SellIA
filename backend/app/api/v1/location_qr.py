"""QR code generation endpoints.

The QR codes are printed on posters at the location and scanned by the mobile app, so generating them is
for the business's own people: the owner or any active member of the location's business. Parsing needs a
login too (it is a pure function with no data behind it, but nothing calls it anonymously).
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.business_access import require_location_access
from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.locations.qr_generator import VALID_QR_TYPES, LocationQRGenerator
from app.domains.users.models import User

router = APIRouter(prefix="", tags=["location-qr"])


@router.get("/locations/{location_id}/qr-codes")
async def get_location_qr_codes(
    location_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate QR codes for location check-in (batch).

    Returns 3 QR payloads: visitor_checkin, feedback, staff_checkin
    """
    await require_location_access(db, location_id, current_user)

    try:
        result = LocationQRGenerator.generate_location_qr_batch(location_id)
        return {
            "location_id": str(location_id),
            "qr_codes": result["qr_codes"],
            "print_ready": True,
            "usage": {
                "visitor_checkin": "Customers scan to check in",
                "feedback": "Customers scan to submit NPS feedback",
                "staff_checkin": "Staff scans to start shift",
            },
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/qr-code")
async def get_single_qr(
    location_id: UUID,
    qr_type: str = "visitor_checkin",
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Generate single QR code by type."""
    await require_location_access(db, location_id, current_user)
    if qr_type not in VALID_QR_TYPES:
        raise HTTPException(
            status_code=400, detail=f"QR type must be one of: {list(VALID_QR_TYPES)}"
        )

    try:
        return LocationQRGenerator.generate_checkin_qr(location_id, None, qr_type)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/qr-parse")
async def parse_qr(
    payload: str = Query(..., max_length=512),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Parse QR code payload from mobile scan."""
    result = LocationQRGenerator.parse_qr_payload(payload)
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result.get("error", "Invalid QR"))
    return result
