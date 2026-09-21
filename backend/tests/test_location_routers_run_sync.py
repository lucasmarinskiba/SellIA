"""Location routers must hand the *sync* Session to the sync services.

get_db yields an AsyncSession (no ``.query``), but LocationInventoryService,
FulfillmentRoutingService, GeofenceTriggerService and UnifiedDashboardService
are sync. The routers bridge with ``await db.run_sync(...)``. These tests use an
``AsyncMock(spec=AsyncSession)`` -- any direct ``db.query`` / ``db.commit()`` on
it raises -- plus a separate sync-session stand-in, and check that:

* the services receive the sync session, never the async one;
* a 404 raised inside the ``try`` is not swallowed into a 400.

No database needed.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import location_inventory as li
from app.api.v1 import mobile_geofence as mg
from app.api.v1 import unified_dashboard as ud
from app.domains.analytics.unified_dashboard_service import UnifiedDashboardService
from app.domains.inventory.inventory_service import (
    FulfillmentRoutingService,
    LocationInventoryService,
)
from app.domains.locations.geofence_service import GeofenceTriggerService

BA = (-34.6037, -58.3816)


class _User:
    id = uuid4()


@pytest.fixture
def dbs() -> tuple[AsyncMock, MagicMock]:
    sync_db = MagicMock(name="sync_session")
    async_db = AsyncMock(spec=AsyncSession)
    async_db.run_sync.side_effect = lambda fn, *a, **k: fn(sync_db, *a, **k)
    return async_db, sync_db


def _record(monkeypatch: pytest.MonkeyPatch, cls: type, name: str, ret: object) -> list:
    seen: list = []

    def fake(*args: object, **kwargs: object) -> object:
        seen.append([*args, *kwargs.values()])
        return ret

    monkeypatch.setattr(cls, name, staticmethod(fake))
    return seen


def _stock_row() -> SimpleNamespace:
    return SimpleNamespace(
        product_name="p",
        quantity_on_hand=1,
        quantity_available=1,
        quantity_reserved=0,
        reorder_point=1,
        status=SimpleNamespace(value="in_stock"),
        is_demo_unit=False,
        unit_price=1,
        fulfillment_method=SimpleNamespace(value="ship_from_location"),
    )


def _loc(lat: float = BA[0], lng: float = BA[1]) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(), name="Shop", latitude=lat, longitude=lng, address="x", hours_json={}
    )


SERVICE_BACKED = [
    (LocationInventoryService, "get_location_inventory", [],
     lambda db: li.get_location_inventory(location_id=uuid4(), db=db)),
    (LocationInventoryService, "get_product_at_location", _stock_row(),
     lambda db: li.get_product_stock(location_id=uuid4(), product_id="p", db=db)),
    (LocationInventoryService, "update_stock", {"ok": True},
     lambda db: li.update_stock(
         request=li.StockUpdateRequest(
             location_id=uuid4(), product_id="p", quantity_change=1, movement_type="stock_in"
         ),
         current_user=_User(), db=db)),
    (LocationInventoryService, "check_stock_for_demo", {"ok": True},
     lambda db: li.check_demo_stock(
         location_id=uuid4(),
         request=li.DemoCheckRequest(location_id=uuid4(), product_id="p", checkin_id=uuid4()),
         db=db)),
    (LocationInventoryService, "get_stock_movement_history", [],
     lambda db: li.get_stock_history(location_id=uuid4(), product_id=None, days=30, db=db)),
    (LocationInventoryService, "acknowledge_low_stock_alert", {"ok": True},
     lambda db: li.acknowledge_alert(alert_id=uuid4(), current_user=_User(), db=db)),
    (FulfillmentRoutingService, "find_best_fulfillment_location", {"ok": True},
     lambda db: li.find_fulfillment_location(
         request=li.FulfillmentRequest(
             business_id=uuid4(), product_id="p", customer_lat=BA[0], customer_lng=BA[1]
         ),
         db=db)),
    (FulfillmentRoutingService, "reserve_inventory_for_order", {"ok": True},
     lambda db: li.reserve_inventory(
         request=li.OrderReservationRequest(
             location_id=uuid4(), product_id="p", quantity=1, order_id="o"
         ),
         current_user=_User(), db=db)),
    (FulfillmentRoutingService, "mark_order_shipped", {"ok": True},
     lambda db: li.mark_order_shipped(
         order_id="o", location_id=uuid4(), product_id="p", current_user=_User(), db=db)),
    (UnifiedDashboardService, "aggregate_location_day", {"ok": True},
     lambda db: ud.aggregate_location_metrics(location_id=uuid4(), date="2026-01-01", db=db)),
    (UnifiedDashboardService, "generate_business_summary", {"ok": True},
     lambda db: ud.generate_business_summary(business_id=uuid4(), date=None, db=db)),
    (UnifiedDashboardService, "compare_locations", {"ok": True},
     lambda db: ud.compare_locations(business_id=uuid4(), date="2026-01-01", db=db)),
]


@pytest.mark.parametrize(
    ("cls", "method", "ret", "call"),
    SERVICE_BACKED,
    ids=[f"{c.__name__}.{m}" for c, m, _, _ in SERVICE_BACKED],
)
async def test_service_gets_sync_session(dbs, monkeypatch, cls, method, ret, call) -> None:
    async_db, sync_db = dbs
    sync_db.query.return_value.filter.return_value.all.return_value = [_loc()]
    seen = _record(monkeypatch, cls, method, ret)

    await call(async_db)

    assert len(seen) == 1
    assert any(arg is sync_db for arg in seen[0]), "service did not receive the sync session"
    assert not any(arg is async_db for arg in seen[0]), "service received the AsyncSession"


async def test_low_stock_alerts_query_runs_on_sync_session(dbs) -> None:
    async_db, sync_db = dbs
    sync_db.query.return_value.filter.return_value.filter.return_value.all.return_value = []

    result = await li.get_low_stock_alerts(location_id=uuid4(), acknowledged=False, db=async_db)

    assert result["total_alerts"] == 0
    sync_db.query.assert_called_once()


async def test_check_geofence_runs_queries_and_service_on_sync_session(dbs, monkeypatch) -> None:
    async_db, sync_db = dbs
    loc = _loc()
    query = sync_db.query.return_value.filter.return_value
    query.first.return_value = SimpleNamespace(id=uuid4())  # the Business
    query.all.return_value = [loc]
    seen = _record(
        monkeypatch, GeofenceTriggerService, "check_geofence_triggers",
        {"triggered": True, "location_id": str(loc.id), "location_name": "Shop"},
    )

    result = await mg.check_geofence(
        request=mg.GeofenceCheckRequest(latitude=BA[0], longitude=BA[1], business_id=uuid4()),
        current_user=_User(), db=async_db,
    )

    assert result["triggered"] is True
    assert any(arg is sync_db for arg in seen[0])
    assert [loc] in seen[0]  # locations loaded on the sync session were passed along


async def test_check_geofence_unknown_business_is_404_not_400(dbs) -> None:
    async_db, sync_db = dbs
    sync_db.query.return_value.filter.return_value.first.return_value = None

    with pytest.raises(HTTPException) as exc:
        await mg.check_geofence(
            request=mg.GeofenceCheckRequest(latitude=BA[0], longitude=BA[1], business_id=uuid4()),
            current_user=_User(), db=async_db,
        )

    assert exc.value.status_code == 404


async def test_nearby_and_subscribe_load_locations_via_run_sync(dbs) -> None:
    async_db, sync_db = dbs
    loc = _loc()
    sync_db.query.return_value.filter.return_value.all.return_value = [loc]
    bid = uuid4()

    nearby = await mg.get_nearby_locations(
        request=mg.GeofenceCheckRequest(latitude=BA[0], longitude=BA[1], business_id=bid),
        current_user=_User(), db=async_db,
    )
    subscribed = await mg.subscribe_to_geofence(
        business_id=bid, radius_km=0.5, current_user=_User(), db=async_db
    )

    assert nearby["count"] == 1
    assert nearby["nearby_locations"][0]["location_id"] == str(loc.id)
    assert [g["id"] for g in subscribed["geofences"]] == [str(loc.id)]


async def test_unknown_product_at_location_is_404_not_400(dbs, monkeypatch) -> None:
    async_db, _ = dbs
    _record(monkeypatch, LocationInventoryService, "get_product_at_location", None)

    with pytest.raises(HTTPException) as exc:
        await li.get_product_stock(location_id=uuid4(), product_id="nope", db=async_db)

    assert exc.value.status_code == 404


async def test_unified_dashboard_reads_run_on_sync_session(dbs) -> None:
    async_db, sync_db = dbs
    sync_db.query.return_value.filter.return_value.first.return_value = None
    sync_db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []

    dashboard = await ud.get_business_dashboard(business_id=uuid4(), db=async_db)
    metrics = await ud.get_location_unified_metrics(location_id=uuid4(), days=7, db=async_db)

    assert dashboard == {"dashboard_available": False}
    assert metrics["data_points"] == []
