"""The analytics monitoring endpoints answer 501 instead of fixed numbers.

They used to return the same invented figures (2847 visits, a 10 000-visitor funnel, a
made-up A/B test) to everyone. Until a real source is connected they must say so: a 501
with a message, never a 200 with data. Each route stays mounted so callers get that answer
rather than a 404.
"""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1 import analytics

GET_ROUTES = [
    "/api/v1/analytics/funnel/conversion",
    "/api/v1/analytics/ab-test/active",
    "/api/v1/analytics/anomalies/seo",
    "/api/v1/analytics/performance/core-web-vitals",
    "/api/v1/analytics/personalization/user-segment?user_id=abc",
    "/api/v1/analytics/dashboard/seo-metrics",
    "/api/v1/analytics/dashboard/marketing-metrics",
]
POST_ROUTES = [
    ("/api/v1/analytics/track-event?event_name=page_view", None),
    ("/api/v1/analytics/ab-test/create?test_name=t&control_url=a&variant_url=b", None),
]


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(analytics.router, prefix="/api/v1/analytics")  # as in app/main.py
    return TestClient(app)


@pytest.mark.parametrize("path", GET_ROUTES)
def test_get_answers_501_not_invented_data(client: TestClient, path: str) -> None:
    response = client.get(path)

    assert response.status_code == 501
    assert "todavía no hay una fuente de datos conectada" in response.json()["detail"]


@pytest.mark.parametrize("path,body", POST_ROUTES)
def test_post_does_not_report_success(client: TestClient, path: str, body) -> None:
    response = client.post(path, json=body)

    assert response.status_code == 501
    assert "status" not in response.json()  # no "tracked" / "created" for something that was not stored


def test_no_fixed_figures_in_module() -> None:
    source = open(analytics.__file__, encoding="utf-8").read()

    for invented in ("2847", "10000", "89234", "test_id"):
        assert invented not in source
