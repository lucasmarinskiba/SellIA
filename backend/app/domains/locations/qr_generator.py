"""QR code generation for location check-ins."""

import logging
from uuid import UUID
from typing import Optional

logger = logging.getLogger(__name__)


class LocationQRGenerator:
    """Generate QR codes for location check-in."""

    @staticmethod
    def generate_checkin_qr(
        location_id: UUID,
        business_id: UUID,
        qr_type: str = "visitor_checkin"  # visitor_checkin, staff_checkin, feedback
    ) -> dict:
        """Generate QR code data for location check-in.

        Returns QR payload that mobile app can scan.
        """
        # QR payload format: selliaapp://checkin?location={id}&type={type}&timestamp={ts}
        payload = f"selliaapp://checkin?location={location_id}&business={business_id}&type={qr_type}"

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
        """Parse QR code payload from mobile app scan."""
        # Extract from "selliaapp://checkin?location={id}&type={type}"
        if not payload.startswith("selliaapp://"):
            return {"valid": False, "error": "Invalid QR format"}

        try:
            params_str = payload.split("?", 1)[1]
            params = dict(param.split("=") for param in params_str.split("&"))

            return {
                "valid": True,
                "location_id": params.get("location"),
                "type": params.get("type", "visitor_checkin"),
                "business_id": params.get("business")
            }
        except Exception as e:
            logger.error(f"Failed to parse QR payload: {e}")
            return {"valid": False, "error": str(e)}
