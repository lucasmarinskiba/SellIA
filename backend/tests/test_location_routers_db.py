"""Location routers over HTTP against a real database (SQLite via aiosqlite).

The mock-based tests prove which *session* the services receive; these prove the
whole path -- auth dependency, ownership check, ``run_sync`` bridge, sync services,
SQL -- on real tables, so dead code that never ran (wrong column names, missing
attributes) fails here instead of in production.

Covered for ``location_inventory``, ``mobile_geofence`` and ``unified_dashboard``:

* no login            -> 401/403
* someone else's id   -> 403, and nothing was written
* unknown id          -> 404
* the owner           -> works, and the rows end up in the database

No Postgres needed. JSONB / UUID are rendered as JSON / CHAR(32) for SQLite.
"""

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from types import SimpleNamespace

import httpx
import pytest
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import func, select
from sqlalchemy import types as sqltypes
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.api.v1 import location_inventory, mobile_geofence, unified_dashboard
from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.db.schema_bootstrap import ensure_unique_index_names
from app.domains.analytics.unified_dashboard_models import (
    BusinessDashboardSummary,
    LocationComparison,
    UnifiedLocationMetric,
)
from app.domains.businesses.location_models import Location
from app.domains.businesses.models import Business
from app.domains.inventory.inventory_models import (
    LocationInventory,
    LowStockAlert,
    StockMovement,
)
from app.domains.locations.checkin_models import LocationCheckin, LocationFeedback
from app.domains.pricing.pricing_models import PricingTransaction
from app.domains.staff.task_models import StaffTask


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"


@compiles(sqltypes.UUID, "sqlite")
def _uuid_as_char(type_, compiler, **kw):
    return "CHAR(32)"


MODELS = [
    Business, Location, LocationInventory, StockMovement, LowStockAlert, LocationCheckin,
    LocationFeedback, StaffTask, PricingTransaction, UnifiedLocationMetric,
    BusinessDashboardSummary, LocationComparison,
]

BA = (-34.6037, -58.3816)
CORDOBA = (-31.4201, -64.1888)  # ~650 km away
TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")

OWNER = SimpleNamespace(id=uuid.uuid4())
STRANGER = SimpleNamespace(id=uuid.uuid4())


@pytest_asyncio.fixture
async def factory():
    ensure_unique_index_names(Base.metadata)  # same in-memory fix the prod bootstrap applies
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=[m.__table__ for m in MODELS]))
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    await engine.dispose()


def _build_app(factory, who: dict | None) -> FastAPI:
    app = FastAPI()
    app.include_router(location_inventory.router, prefix="/api/v1")  # as in app/main.py
    app.include_router(mobile_geofence.router)
    app.include_router(unified_dashboard.router)

    async def _db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    if who is not None:  # None -> keep the real get_current_user (no token => rejected)
        app.dependency_overrides[get_current_user] = lambda: who["user"]
    return app


@pytest_asyncio.fixture
async def world(factory):
    async with factory() as s:
        biz = Business(user_id=OWNER.id, name="Shop")
        s.add(biz)
        await s.flush()
        loc = Location(business_id=biz.id, name="Sucursal", address="Av 1", city="BA",
                       latitude=BA[0], longitude=BA[1])
        s.add(loc)
        await s.flush()
        inv = LocationInventory(location_id=loc.id, business_id=biz.id, product_id="sku-1",
                                product_name="Remera", quantity_on_hand=10, quantity_available=10,
                                quantity_reserved=0, reorder_point=3, unit_price=Decimal("19.99"))
        s.add(inv)
        await s.flush()
        alert = LowStockAlert(location_id=loc.id, business_id=biz.id, inventory_id=inv.id,
                              product_id="sku-1", product_name="Remera",
                              quantity_available=2, reorder_point=3)
        s.add(alert)
        await s.commit()
        ids = SimpleNamespace(biz=biz.id, loc=loc.id, inv=inv.id, alert=alert.id)

    who = {"user": OWNER}
    app = _build_app(factory, who)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield SimpleNamespace(client=client, who=who, factory=factory, **vars(ids))


def _routes(loc, biz, alert) -> list[tuple[str, str, dict | None]]:
    geo = {"latitude": BA[0], "longitude": BA[1], "business_id": str(biz)}
    return [
        ("GET", f"/api/v1/locations/{loc}/inventory", None),
        ("GET", f"/api/v1/locations/{loc}/inventory/sku-1", None),
        ("POST", "/api/v1/inventory/update-stock",
         {"location_id": str(loc), "product_id": "sku-1", "quantity_change": 5, "movement_type": "stock_in"}),
        ("POST", f"/api/v1/locations/{loc}/check-demo-availability",
         {"location_id": str(loc), "product_id": "sku-1", "checkin_id": str(uuid.uuid4())}),
        ("GET", f"/api/v1/locations/{loc}/stock-movements", None),
        ("GET", f"/api/v1/locations/{loc}/low-stock-alerts", None),
        ("POST", f"/api/v1/inventory/acknowledge-alert?alert_id={alert}", None),
        ("POST", "/api/v1/fulfillment/find-location",
         {"business_id": str(biz), "product_id": "sku-1", "customer_lat": BA[0], "customer_lng": BA[1]}),
        ("POST", "/api/v1/orders/reserve-inventory",
         {"location_id": str(loc), "product_id": "sku-1", "quantity": 1, "order_id": "o-1"}),
        ("POST", f"/api/v1/orders/o-1/shipped?location_id={loc}&product_id=sku-1", None),
        ("POST", "/api/v1/mobile/geofence/check", geo),
        ("POST", "/api/v1/mobile/locations/nearby", geo),
        ("POST", f"/api/v1/mobile/geofence/subscribe?business_id={biz}", None),
        ("POST", f"/api/v1/locations/{loc}/metrics/aggregate?date={TODAY}", None),
        ("POST", f"/api/v1/businesses/{biz}/summary", None),
        ("POST", f"/api/v1/businesses/{biz}/location-comparison?date={TODAY}", None),
        ("GET", f"/api/v1/locations/{loc}/unified-metrics", None),
        ("GET", f"/api/v1/businesses/{biz}/unified-dashboard", None),
    ]


def _ids(routes: list) -> list[str]:
    return [f"{m} {u.split('?')[0].replace('/api/v1', '')[:48]}" for m, u, _ in routes]


_SHAPE = _routes("L", "B", "A")


async def _call(client: httpx.AsyncClient, method: str, url: str, body: dict | None) -> httpx.Response:
    return await client.request(method, url, json=body)


async def _count(factory, model) -> int:
    async with factory() as s:
        return (await s.execute(select(func.count()).select_from(model))).scalar_one()


# --------------------------------------------------------------------------- access


@pytest.mark.parametrize("idx", range(len(_SHAPE)), ids=_ids(_SHAPE))
async def test_someone_elses_id_is_403_and_writes_nothing(world, idx) -> None:
    world.who["user"] = STRANGER
    method, url, body = _routes(world.loc, world.biz, world.alert)[idx]

    r = await _call(world.client, method, url, body)

    assert r.status_code == 403, r.text
    for model in (StockMovement, LocationCheckin, UnifiedLocationMetric, BusinessDashboardSummary,
                  LocationComparison):
        assert await _count(world.factory, model) == 0, f"{model.__name__} written by a stranger"
    async with world.factory() as s:
        inv = await s.get(LocationInventory, world.inv)
        alert = await s.get(LowStockAlert, world.alert)
    assert (inv.quantity_on_hand, inv.quantity_reserved) == (10, 0)
    assert alert.acknowledged in (False, None)


@pytest.mark.parametrize("idx", range(len(_SHAPE)), ids=_ids(_SHAPE))
async def test_unknown_id_is_404(world, idx) -> None:
    method, url, body = _routes(uuid.uuid4(), uuid.uuid4(), uuid.uuid4())[idx]

    r = await _call(world.client, method, url, body)

    assert r.status_code == 404, r.text


@pytest.mark.parametrize("idx", range(len(_SHAPE)), ids=_ids(_SHAPE))
async def test_no_login_is_rejected(factory, world, idx) -> None:
    app = _build_app(factory, None)
    method, url, body = _routes(world.loc, world.biz, world.alert)[idx]
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as anon:
        r = await _call(anon, method, url, body)

    assert r.status_code in (401, 403), r.text


# --------------------------------------------------------------------------- inventory


async def test_owner_reads_inventory_and_alerts(world) -> None:
    inv = await world.client.get(f"/api/v1/locations/{world.loc}/inventory")
    one = await world.client.get(f"/api/v1/locations/{world.loc}/inventory/sku-1")
    alerts = await world.client.get(f"/api/v1/locations/{world.loc}/low-stock-alerts")

    assert inv.status_code == one.status_code == alerts.status_code == 200, (inv.text, one.text, alerts.text)
    assert [i["product_id"] for i in inv.json()["inventory"]] == ["sku-1"]
    assert one.json()["quantity_on_hand"] == 10
    assert [a["alert_id"] for a in alerts.json()["alerts"]] == [str(world.alert)]


async def test_unknown_product_is_404_not_400(world) -> None:
    r = await world.client.get(f"/api/v1/locations/{world.loc}/inventory/nope")

    assert r.status_code == 404, r.text


async def test_owner_update_stock_changes_row_and_logs_movement(world) -> None:
    r = await world.client.post("/api/v1/inventory/update-stock", json={
        "location_id": str(world.loc), "product_id": "sku-1", "quantity_change": 5, "movement_type": "stock_in"})

    assert r.status_code == 200, r.text
    async with world.factory() as s:
        assert (await s.get(LocationInventory, world.inv)).quantity_on_hand == 15
    assert await _count(world.factory, StockMovement) == 1
    history = await world.client.get(f"/api/v1/locations/{world.loc}/stock-movements")
    assert [m["quantity_after"] for m in history.json()["movements"]] == [15]


async def test_owner_acknowledges_alert(world) -> None:
    r = await world.client.post(f"/api/v1/inventory/acknowledge-alert?alert_id={world.alert}")

    assert r.status_code == 200, r.text
    async with world.factory() as s:
        alert = await s.get(LowStockAlert, world.alert)
    assert alert.acknowledged is True
    assert alert.acknowledged_by == OWNER.id


async def test_find_fulfillment_location_picks_the_owners_store(world) -> None:
    r = await world.client.post("/api/v1/fulfillment/find-location", json={
        "business_id": str(world.biz), "product_id": "sku-1", "customer_lat": BA[0], "customer_lng": BA[1]})

    assert r.status_code == 200, r.text
    assert r.json()["location_id"] == str(world.loc)
    assert r.json()["inventory_available"] == 10


async def test_reserve_then_ship(world) -> None:
    reserved = await world.client.post("/api/v1/orders/reserve-inventory", json={
        "location_id": str(world.loc), "product_id": "sku-1", "quantity": 2, "order_id": "o-1"})
    shipped = await world.client.post(f"/api/v1/orders/o-1/shipped?location_id={world.loc}&product_id=sku-1")

    assert reserved.status_code == 200, reserved.text
    assert shipped.status_code == 200, shipped.text


async def test_demo_check_rejects_path_body_mismatch(world) -> None:
    r = await world.client.post(f"/api/v1/locations/{world.loc}/check-demo-availability", json={
        "location_id": str(uuid.uuid4()), "product_id": "sku-1", "checkin_id": str(uuid.uuid4())})

    assert r.status_code == 400, r.text


# --------------------------------------------------------------------------- geofence


async def test_geofence_check_in_once_then_deduplicates(world) -> None:
    body = {"latitude": BA[0], "longitude": BA[1], "business_id": str(world.biz)}

    first = await world.client.post("/api/v1/mobile/geofence/check", json=body)
    second = await world.client.post("/api/v1/mobile/geofence/check", json=body)

    assert first.status_code == 200, first.text
    assert first.json()["triggered"] is True, first.text
    assert first.json()["location_id"] == str(world.loc)
    assert second.json()["triggered"] is False
    assert await _count(world.factory, LocationCheckin) == 1
    async with world.factory() as s:
        assert (await s.execute(select(LocationCheckin.user_id))).scalar_one() == OWNER.id


async def test_geofence_check_far_away_does_not_check_in(world) -> None:
    r = await world.client.post("/api/v1/mobile/geofence/check", json={
        "latitude": CORDOBA[0], "longitude": CORDOBA[1], "business_id": str(world.biz)})

    assert r.status_code == 200, r.text
    assert r.json()["triggered"] is False
    assert await _count(world.factory, LocationCheckin) == 0


async def test_nearby_and_subscribe_list_the_owners_locations(world) -> None:
    near = await world.client.post("/api/v1/mobile/locations/nearby", json={
        "latitude": BA[0], "longitude": BA[1], "business_id": str(world.biz)})
    sub = await world.client.post(f"/api/v1/mobile/geofence/subscribe?business_id={world.biz}")

    assert near.status_code == sub.status_code == 200, (near.text, sub.text)
    assert near.json()["count"] == 1
    assert [g["id"] for g in sub.json()["geofences"]] == [str(world.loc)]


# --------------------------------------------------------------------------- dashboard


async def test_dashboard_flow_uses_the_locations_real_business_id(world) -> None:
    agg = await world.client.post(f"/api/v1/locations/{world.loc}/metrics/aggregate?date={TODAY}")
    assert agg.status_code == 200, agg.text

    async with world.factory() as s:
        metric = (await s.execute(select(UnifiedLocationMetric))).scalar_one()
    assert metric.business_id == world.biz  # used to be the all-zero UUID
    assert metric.location_id == world.loc

    series = await world.client.get(f"/api/v1/locations/{world.loc}/unified-metrics")
    assert [p["date"] for p in series.json()["data_points"]] == [TODAY], series.text

    summary = await world.client.post(f"/api/v1/businesses/{world.biz}/summary")
    assert summary.status_code == 200, summary.text
    dash = await world.client.get(f"/api/v1/businesses/{world.biz}/unified-dashboard")
    assert dash.status_code == 200, dash.text
    assert dash.json()["dashboard_available"] is True
    assert dash.json()["total_locations"] == 1

    cmp_ = await world.client.post(f"/api/v1/businesses/{world.biz}/location-comparison?date={TODAY}")
    assert cmp_.status_code == 200, cmp_.text
    assert cmp_.json()["comparison_generated"] is True
    assert await _count(world.factory, LocationComparison) == 1
