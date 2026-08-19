"""QR code generation endpoints."""

from fastapi import APIRouter, HTTPException
from uuid import UUID

from app.domains.locations.qr_generator import LocationQRGenerator

router = APIRouter(prefix="/api/v1", tags=["location-qr"])


@router.get("/locations/{location_id}/qr-codes")
async def get_location_qr_codes(location_id: UUID) -> dict:
    """Generate QR codes for location check-in (batch).

    Returns 3 QR payloads: visitor_checkin, feedback, staff_checkin
    """
    try:
        result = LocationQRGenerator.generate_location_qr_batch(location_id)
        return {
            "location_id": str(location_id),
            "qr_codes": result["qr_codes"],
            "print_ready": True,
            "usage": {
                "visitor_checkin": "Customers scan to check in",
                "feedback": "Customers scan to submit NPS feedback",
                "staff_checkin": "Staff scans to start shift"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/locations/{location_id}/qr-code")
async def get_single_qr(
    location_id: UUID,
    qr_type: str = "visitor_checkin"
) -> dict:
    """Generate single QR code by type."""
    valid_types = ["visitor_checkin", "feedback", "staff_checkin"]
    if qr_type not in valid_types:
        raise HTTPException(status_code=400, detail=f"QR type must be one of: {valid_types}")

    try:
        result = LocationQRGenerator.generate_checkin_qr(location_id, None, qr_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/qr-parse")
async def parse_qr(payload: str) -> dict:
    """Parse QR code payload from mobile scan."""
    try:
        result = LocationQRGenerator.parse_qr_payload(payload)
        if not result["valid"]:
            raise HTTPException(status_code=400, detail=result.get("error", "Invalid QR"))
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
