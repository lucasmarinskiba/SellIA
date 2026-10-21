"""Regression: ``Location`` lives in ``businesses.location_models``, not ``locations.models``.

``Location`` (table ``locations``) is defined in
``app.domains.businesses.location_models``. ``app.domains.locations.models`` only
defines LocationProfile & co. (table ``location_profiles``). Several modules
imported ``Location`` from the latter, so they either failed at import time or
raised ImportError at request time inside a broad ``except`` that turned it into
a 400. They also reached for a ``locations.proximity_engine`` / ``GeoPoint`` API
that never existed (the engine lives in ``app.domains.proximity``).

These tests need no database.
"""

import ast
import importlib
import pathlib
from types import SimpleNamespace
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

APP_DIR = pathlib.Path(__file__).resolve().parents[1] / "app"

MODULES = [
    "app.api.v1.mobile_geofence",
    "app.api.v1.location_inventory",
    "app.api.v1.unified_dashboard",
    "app.domains.analytics.unified_dashboard_service",
    "app.domains.locations.geofence_service",
    "app.domains.inventory.inventory_service",
]

BA = (-34.6037, -58.3816)  # Obelisco, Buenos Aires
CORDOBA = (-31.4201, -64.1888)  # ~650 km from BA


@pytest.mark.parametrize("module_name", MODULES)
def test_module_imports(module_name: str) -> None:
    importlib.import_module(module_name)


def test_location_is_the_locations_table() -> None:
    from app.domains.businesses.location_models import Location

    assert Location.__tablename__ == "locations"


def _module_file(dotted: str) -> pathlib.Path | None:
    base = APP_DIR.parent / pathlib.Path(*dotted.split("."))
    for candidate in (base.with_suffix(".py"), base / "__init__.py"):
        if candidate.is_file():
            return candidate
    return None


def _top_level_names(path: pathlib.Path) -> set[str]:
    names: set[str] = set()
    for node in ast.parse(path.read_text(encoding="utf-8")).body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            names.update((a.asname or a.name).split(".")[0] for a in node.names)
    return names


def test_names_imported_from_locations_package_exist() -> None:
    """Every ``from app.domains.locations[.x] import Y`` in app/ must resolve.

    Purely static (parses source, imports nothing), so it also covers
    function-level imports that only run when an endpoint is hit, and does not
    depend on import order.
    """
    prefix = "app.domains.locations"
    problems: list[str] = []

    for path in APP_DIR.rglob("*.py"):
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if prefix not in source:
            continue
        for node in ast.walk(ast.parse(source)):
            if not (
                isinstance(node, ast.ImportFrom)
                and node.level == 0
                and node.module
                and (node.module == prefix or node.module.startswith(prefix + "."))
            ):
                continue
            where = f"{path.relative_to(APP_DIR)}:{node.lineno}"
            target = _module_file(node.module)
            if target is None:
                problems.append(f"{where}: module {node.module} does not exist")
                continue
            defined = _top_level_names(target)
            for alias in node.names:
                if alias.name == "*" or alias.name in defined:
                    continue
                if _module_file(f"{node.module}.{alias.name}") is not None:
                    continue  # `from pkg import submodule`
                problems.append(f"{where}: {node.module} has no {alias.name!r}")

    assert not problems, "\n".join(problems)


def _loc(name: str, lat: float, lng: float) -> SimpleNamespace:
    return SimpleNamespace(
        id=uuid4(), name=name, latitude=lat, longitude=lng, address=f"{name} 123", hours_json={}
    )


def test_get_nearby_locations_filters_and_sorts_by_km() -> None:
    from app.domains.locations.geofence_service import GeofenceTriggerService

    here = _loc("here", *BA)
    close = _loc("close", BA[0] + 0.0027, BA[1])  # ~300 m
    edge = _loc("edge", BA[0] + 0.0063, BA[1])  # ~700 m, outside 500 m
    cordoba = _loc("cordoba", *CORDOBA)

    nearby = GeofenceTriggerService.get_nearby_locations(
        BA[0], BA[1], uuid4(), [cordoba, edge, close, here], radius_km=0.5
    )

    assert [n["name"] for n in nearby] == ["here", "close"]
    assert nearby[0]["distance_km"] == 0.0
    assert nearby[1]["distance_km"] == pytest.approx(0.3, abs=0.02)


def test_check_geofence_triggers_out_of_range() -> None:
    from app.domains.locations.geofence_service import GeofenceTriggerService

    result = GeofenceTriggerService.check_geofence_triggers(
        uuid4(), BA[0], BA[1], uuid4(), [_loc("cordoba", *CORDOBA)], db=MagicMock()
    )

    assert result == {"triggered": False, "reason": "No locations in range"}


def test_find_best_fulfillment_location_picks_nearest_with_stock() -> None:
    from app.domains.inventory.inventory_models import FulfillmentMethod
    from app.domains.inventory.inventory_service import FulfillmentRoutingService

    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = SimpleNamespace(
        quantity_available=5,
        shipping_lead_days=2,
        fulfillment_method=FulfillmentMethod.SHIP_FROM_LOCATION,
    )
    near = _loc("near", BA[0] + 0.01, BA[1])
    far = _loc("far", *CORDOBA)

    result = FulfillmentRoutingService.find_best_fulfillment_location(
        uuid4(), "sku-1", BA[0], BA[1], [far, near], db=db
    )

    assert result["location_name"] == "near"
    assert result["distance_km"] == pytest.approx(1.11, abs=0.02)


def test_location_routers_are_mounted_in_main_without_collisions() -> None:
    """mobile_geofence / unified_dashboard were never mounted; `_try_include` hides import errors."""
    import collections

    from app.main import app

    mine = {
        "app.api.v1.mobile_geofence",
        "app.api.v1.unified_dashboard",
        "app.api.v1.location_inventory",
        "app.api.v1.dynamic_pricing",
        "app.api.v1.feedback_alerts",
        "app.api.v1.staff_tasks",
    }
    owners: dict[tuple[str, str], list[str]] = collections.defaultdict(list)
    for route in app.routes:
        for method in getattr(route, "methods", None) or ():
            owners[(method, route.path)].append(getattr(route.endpoint, "__module__", ""))

    for expected in (
        ("POST", "/api/v1/mobile/geofence/check"),
        ("POST", "/api/v1/mobile/locations/nearby"),
        ("POST", "/api/v1/mobile/geofence/subscribe"),
        ("POST", "/api/v1/locations/{location_id}/metrics/aggregate"),
        ("GET", "/api/v1/locations/{location_id}/unified-metrics"),
        ("GET", "/api/v1/businesses/{business_id}/unified-dashboard"),
        ("GET", "/api/v1/locations/{location_id}/inventory"),
        ("POST", "/api/v1/tasks/assign"),
        ("GET", "/api/v1/staff/{staff_id}/task-performance"),
        ("POST", "/api/v1/alerts/{alert_id}/escalate"),
        ("POST", "/api/v1/pricing/calculate"),
    ):
        assert expected in owners, f"{expected} is not mounted"

    clashes = {key: mods for key, mods in owners.items() if len(mods) > 1 and mine & set(mods)}
    assert not clashes, f"routes registered twice: {clashes}"


def test_bootstrap_registers_tables_the_dashboard_endpoints_query() -> None:
    """aggregate_location_day reads staff_tasks and pricing_transactions, but nothing imports
    those model modules at boot -- unless the schema bootstrap lists them, the tables are
    never created in production. Runs in a fresh interpreter: in this process app.main has
    already imported everything, which would make the check vacuous."""
    import subprocess
    import sys

    code = (
        "from app.db.schema_bootstrap import _import_all_models\n"
        "from app.core.database import Base\n"
        "_import_all_models()\n"
        "need = {'staff_tasks', 'pricing_transactions', 'unified_location_metrics', 'locations', "
        "'nps_alerts', 'business_members', 'location_pricing_tiers'}\n"
        "print(sorted(need - set(Base.metadata.tables)))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=APP_DIR.parent, capture_output=True, text=True, timeout=120, check=False,
    )

    assert result.returncode == 0, result.stderr[-800:]
    assert result.stdout.strip().splitlines()[-1] == "[]", f"tables not registered: {result.stdout[-300:]}"
