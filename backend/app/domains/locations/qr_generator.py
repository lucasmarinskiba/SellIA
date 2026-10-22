"""QR code generation for location check-ins."""

import logging
from urllib.parse import parse_qs, urlsplit
from uuid import UUID

logger = logging.getLogger(__name__)

VALID_QR_TYPES = ("visitor_checkin", "feedback", "staff_checkin")


class LocationQRGenerator:
    """Generate QR codes for location check-in."""

    @staticmethod
    def generate_checkin_qr(
        location_id: UUID,
        business_id: UUID | None = None,
        qr_type: str = "visitor_checkin"  # visitor_checkin, staff_checkin, feedback
    ) -> dict:
        """Generate QR code data for location check-in.

        Returns QR payload that mobile app can scan.
        """
        if qr_type not in VALID_QR_TYPES:
            raise ValueError(f"QR type must be one of: {list(VALID_QR_TYPES)}")

        # QR payload format: selliaapp://checkin?location={id}&type={type}
        # The business id is only added when given: this is printed on a poster in a public place and the
        # app does not need it (the location already says which business it is). It used to be written
        # unconditionally, so every payload carried the literal text "business=None".
        payload = f"selliaapp://checkin?location={location_id}"
        if business_id is not None:
            payload += f"&business={business_id}"
        payload += f"&type={qr_type}"

        logger.info(f"Generated QR payload for location {location_id}")

        return {
            "qr_payload": payload,
            "qr_type": qr_type,
            "location_id": str(location_id),
            "url_safe": True,
            "encoding": "UTF-8"
        }

    @staticmethod
    def generate_location_qr_batch(
        location_id: UUID,
        qr_types: list[str] = None
    ) -> dict:
        """Generate multiple QR codes for one location.

        Creates QRs for: visitor checkin, feedback, staff checkin
        """
        if not qr_types:
            qr_types = ["visitor_checkin", "feedback", "staff_checkin"]

        qr_codes = {}

        for qr_type in qr_types:
            qr = LocationQRGenerator.generate_checkin_qr(location_id, None, qr_type)
            qr_codes[qr_type] = qr["qr_payload"]

        return {
            "location_id": str(location_id),
            "qr_codes": qr_codes,
            "print_ready": True  # Can be printed as physical posters
        }

    @staticmethod
    def parse_qr_payload(payload: str) -> dict:
        """Parse QR code payload from mobile app scan.

        Strict on purpose: the scheme and host must match, ``location`` (and ``business`` when present) must
        be UUIDs and ``type`` one of the known QR types.
        """
        try:
            parts = urlsplit(payload)
        except ValueError:
            return {"valid": False, "error": "Invalid QR format"}
        if parts.scheme != "selliaapp" or parts.netloc != "checkin":
            return {"valid": False, "error": "Invalid QR format"}

        params = {key: values[-1] for key, values in parse_qs(parts.query).items()}
        try:
            location_id = UUID(params["location"])
            business_id = UUID(params["business"]) if "business" in params else None
        except (KeyError, ValueError):
            return {"valid": False, "error": "QR needs a valid location (and business, when present) id"}

        qr_type = params.get("type", "visitor_checkin")
        if qr_type not in VALID_QR_TYPES:
            return {"valid": False, "error": f"QR type must be one of: {list(VALID_QR_TYPES)}"}

        return {
            "valid": True,
            "location_id": str(location_id),
            "type": qr_type,
            "business_id": str(business_id) if business_id else None,
        }
