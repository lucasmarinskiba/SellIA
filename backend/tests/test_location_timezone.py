"""Per-location timezone: the schema accepts only IANA names, and local-time BI figures follow the location's zone.

Pure functions only, no database: the metric functions take plain visit objects, so these run anywhere.
The bootstrap that adds the column to a live table is checked against a real PostgreSQL separately.
"""

import uuid
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from app.domains.analytics.offline_models import VisitType
from app.domains.bi.offline_metrics import _zone, daily_trend, traffic_profile
from app.domains.businesses.location_models import LocationCreate, LocationUpdate

BUENOS_AIRES = "America/Argentina/Buenos_Aires"  # UTC-3 all year since DST was dropped in 2009


def _payload(**overrides):
    base = {
        "name": "Showroom Centro",
        "type": "showroom",
        "address": "Av. Corrientes 1234",
        "city": "Buenos Aires",
        "latitude": -34.6,
        "longitude": -58.4,
        "hours_json": {},
    }
    return {**base, **overrides}


def _visit(moment: datetime, location_id):
    return SimpleNamespace(
        entry_time=moment,
        location_id=location_id,
        visit_type=VisitType.WALK_IN,
        dwell_minutes=None,
    )


def test_timezone_defaults_to_utc_when_omitted():
    assert LocationCreate(**_payload()).timezone == "UTC"


def test_accepts_an_iana_name():
    assert LocationCreate(**_payload(timezone=BUENOS_AIRES)).timezone == BUENOS_AIRES


@pytest.mark.parametrize("bad", ["Mars/Olympus_Mons", "America", "../../etc/passwd", ""])
def test_rejects_names_the_iana_database_does_not_know(bad):
    with pytest.raises(ValidationError):
        LocationCreate(**_payload(timezone=bad))


def test_update_rejects_an_explicit_null_zone():
    # An explicit null would reach the NOT NULL column through model_dump(exclude_unset=True).
    with pytest.raises(ValidationError):
        LocationUpdate(timezone=None)


def test_update_without_a_zone_leaves_it_untouched():
    assert "timezone" not in LocationUpdate(name="Nuevo nombre").model_dump(exclude_unset=True)


def test_unknown_or_missing_zone_falls_back_to_utc():
    assert _zone(BUENOS_AIRES).key == BUENOS_AIRES
    assert _zone(None) == timezone.utc
    assert _zone("") == timezone.utc
    assert _zone("Mars/Olympus_Mons") == timezone.utc


def test_hours_and_weekdays_follow_the_location_zone():
    showroom = uuid.uuid4()
    # 01:30 UTC on Thursday 1 Oct 2026 is 22:30 on Wednesday 30 Sep in Buenos Aires.
    visits = [_visit(datetime(2026, 10, 1, 1, 30, tzinfo=timezone.utc), showroom)]

    profile = traffic_profile(visits, {showroom: _zone(BUENOS_AIRES)})

    assert profile["hourly_breakdown"] == {"22": 1}
    assert profile["peak_hour"] == "22:00-23:00"
    assert profile["peak_day"] == "Wednesday"


def test_without_a_known_zone_the_figures_stay_utc():
    showroom = uuid.uuid4()
    visits = [_visit(datetime(2026, 10, 1, 1, 30, tzinfo=timezone.utc), showroom)]

    profile = traffic_profile(visits, {})

    assert profile["hourly_breakdown"] == {"01": 1}
    assert profile["peak_day"] == "Thursday"


def test_business_hours_bucket_each_visit_in_its_own_location_zone():
    buenos_aires, utc_site = uuid.uuid4(), uuid.uuid4()
    moment = datetime(2026, 10, 1, 1, 15, tzinfo=timezone.utc)
    visits = [_visit(moment, buenos_aires), _visit(moment, utc_site), _visit(moment, None)]

    profile = traffic_profile(visits, {buenos_aires: _zone(BUENOS_AIRES)})

    # Buenos Aires visit at 22:15 local; the UTC site and the location-less visit stay at 01:15.
    assert profile["hourly_breakdown"] == {"01": 2, "22": 1}


def test_daily_trend_counts_each_visit_on_its_local_day():
    showroom = uuid.uuid4()
    start = datetime(2026, 9, 28, 12, 0, tzinfo=timezone.utc)  # 09:00 local on 28 Sep
    # 01:30 UTC on 1 Oct is 22:30 on 30 Sep locally: it belongs to the 30th, not the 1st.
    visits = [_visit(datetime(2026, 10, 1, 1, 30, tzinfo=timezone.utc), showroom)]

    trend = daily_trend(visits, start, 4, _zone(BUENOS_AIRES))

    assert trend == [
        {"date": "2026-09-28", "visits": 0},
        {"date": "2026-09-29", "visits": 0},
        {"date": "2026-09-30", "visits": 1},
        {"date": "2026-10-01", "visits": 0},
    ]
