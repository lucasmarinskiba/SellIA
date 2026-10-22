"""Regression: two ``OfflineConversion`` models must never share a table.

``app.domains.analytics.offline_models`` owns ``offline_conversions`` (live visit tracking and BI). The legacy
model in ``app.domains.locations.models`` used the same name on the same ``Base``, so importing both raised
``Table 'offline_conversions' is already defined``. ``init_db()`` swallowed that error as a warning.

Importing both at module level makes a reappearance fail at collection, before any assertion runs.
"""

from app.core.database import Base
from app.domains.analytics.offline_models import (
    OfflineConversion as LiveOfflineConversion,
)
from app.domains.locations.models import OfflineConversion as LegacyOfflineConversion


def test_live_model_keeps_the_offline_conversions_table() -> None:
    assert LiveOfflineConversion.__tablename__ == "offline_conversions"


def test_legacy_model_has_its_own_table() -> None:
    assert LegacyOfflineConversion.__tablename__ == "location_offline_conversions"


def test_both_tables_are_registered_on_the_shared_base() -> None:
    assert {"offline_conversions", "location_offline_conversions"} <= set(Base.metadata.tables)
    assert Base.metadata.tables["offline_conversions"] is LiveOfflineConversion.__table__
    assert Base.metadata.tables["location_offline_conversions"] is LegacyOfflineConversion.__table__
