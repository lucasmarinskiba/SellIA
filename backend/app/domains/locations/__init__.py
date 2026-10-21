"""Locations domain — physical location management."""

from .checkin_models import (
    CheckinStatus,
    CheckinType,
    LocationCheckin,
    LocationFeedback,
    StaffCheckin,
)
from .checkin_service import LocationCheckinService

__all__ = [
    "CheckinStatus",
    "CheckinType",
    "LocationCheckin",
    "LocationCheckinService",
    "LocationFeedback",
    "StaffCheckin",
]
