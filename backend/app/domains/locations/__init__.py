"""Locations domain — physical location management."""

from .checkin_models import LocationCheckin, StaffCheckin, LocationFeedback, CheckinType, CheckinStatus
from .checkin_service import LocationCheckinService

__all__ = [
    "LocationCheckin", "StaffCheckin", "LocationFeedback",
    "CheckinType", "CheckinStatus",
    "LocationCheckinService"
]
