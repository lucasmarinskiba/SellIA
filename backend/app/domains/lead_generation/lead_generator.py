"""Lead data types shared by the lead generation and enrichment helpers.

The synthetic generator that used to live here (random names, emails and phones)
is gone. Real prospects come from places_source.py (Google Places) and from
prospect_capture.py (CSV imports), never from invented data.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional
from datetime import datetime
from enum import Enum


class LeadSource(str, Enum):
    GOOGLE_MAPS = "google_maps"
    GOOGLE_SEARCH = "google_search"
    LINKEDIN = "linkedin"
    INSTAGRAM = "instagram"
    FACEBOOK = "facebook"
    WHATSAPP = "whatsapp"
    MARKETPLACE = "marketplace"
    EMAIL = "email"
    DIRECTORY = "directory"
    REFERRAL = "referral"
    COLD_OUTREACH = "cold_outreach"


class LeadQuality(str, Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


@dataclass
class Lead:
    lead_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    source: LeadSource = LeadSource.GOOGLE_SEARCH
    quality: LeadQuality = LeadQuality.WARM
    estimated_budget: Optional[float] = None
    estimated_timeline: Optional[str] = None
    contact_method: str = "email"
    raw_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    enriched: bool = False
