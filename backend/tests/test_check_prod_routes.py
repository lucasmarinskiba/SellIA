"""The post-deploy route check: groups, the failure rules, and the snapshot against itself."""

import importlib.util
import json
from collections import Counter
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "check_prod_routes.py"
spec = importlib.util.spec_from_file_location("check_prod_routes", SCRIPT)
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


def test_a_group_is_the_first_four_static_segments():
    assert check.group_of("/api/v1/businesses/{business_id}/harvey/profile") == "api/v1/businesses/harvey"
    assert check.group_of("/api/v1/auth/login") == "api/v1/auth/login"
    assert check.group_of("/api/health") == "api/health"
    assert check.group_of("/api/v1/businesses/{business_id}/conversations/{conversation_id}/messages") == (
        "api/v1/businesses/conversations"
    )


def test_a_complete_deployment_passes_and_new_routes_never_fail():
    snapshot = {"api/v1/businesses/harvey": 27, "api/v1/auth/login": 1}
    assert check.compare(snapshot, Counter({"api/v1/businesses/harvey": 27, "api/v1/auth/login": 1})) == []
    assert check.compare(snapshot, Counter({"api/v1/businesses/harvey": 40, "api/v1/auth/login": 1, "api/v1/new/x": 3})) == []


def test_a_skipped_router_is_reported_by_name():
    snapshot = {"api/v1/businesses/harvey": 27, "api/v1/auth/login": 1}
    problems = check.compare(snapshot, Counter({"api/v1/auth/login": 1}))
    assert any("/api/v1/businesses/harvey" in p and "27" in p for p in problems)


def test_a_broad_loss_of_routes_fails_even_if_every_group_survives():
    snapshot = {"a/b/c/d": 100, "e/f/g/h": 100}
    assert check.compare(snapshot, Counter({"a/b/c/d": 50, "e/f/g/h": 100})) != []
    assert check.compare(snapshot, Counter({"a/b/c/d": 97, "e/f/g/h": 100})) == []  # 98.5%: within tolerance


def test_the_committed_snapshot_has_the_routes_that_went_missing_on_2026_10_28():
    snapshot = json.loads((SCRIPT.parent.parent / "routes_snapshot.json").read_text(encoding="utf-8"))
    assert snapshot["api/v1/businesses/harvey"] >= 27 and sum(snapshot.values()) > 1000
    assert check.compare(snapshot, Counter(snapshot)) == []
