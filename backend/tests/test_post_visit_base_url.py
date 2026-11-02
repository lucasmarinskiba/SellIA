"""The post-visit beat task builds its unsubscribe links from POST_VISIT_BASE_URL, and never from TRACKING_BASE_URL.

TRACKING_BASE_URL also feeds the MercadoPago notification URL, so the post-visit path must not depend on it. The
session, the event loop and the sending are stubbed: nothing here touches a database, Redis or the mail provider.
"""

import asyncio
from types import SimpleNamespace

import pytest

from app.tasks import offline_sequence_tasks


class _Session:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, *exc):
        return False


def _settings(**overrides) -> SimpleNamespace:
    base = {
        "OFFLINE_SEQUENCE_SEND_ENABLED": True,
        "POST_VISIT_BASE_URL": "https://post-visit.example",
        "TRACKING_BASE_URL": "https://tracking.example",
        "SECRET_KEY": "test-secret-key",
        "ALLOW_GLOBAL_SENDER_FOR_TESTING": False,
        "GLOBAL_SENDER_EMAIL": None,
    }
    base.update(overrides)
    return SimpleNamespace(**base)


@pytest.fixture
def captured(monkeypatch) -> dict:
    seen: dict = {}

    async def fake_send_due_jobs(db, **kwargs):
        seen.update(kwargs)
        return {"sent": 0, "failed": 0, "skipped": 0, "retry": 0, "blocked": 0}

    monkeypatch.setattr("app.tasks.offline_sequence_tasks.AsyncSessionLocal", lambda: _Session())
    monkeypatch.setattr("app.tasks.offline_sequence_tasks.run_async", lambda coro: asyncio.run(coro))
    monkeypatch.setattr("app.domains.sequences.offline_sequence_jobs.send_due_jobs", fake_send_due_jobs)
    return seen


def test_the_base_url_comes_from_the_post_visit_setting(captured, monkeypatch) -> None:
    monkeypatch.setattr("app.core.config.get_settings", lambda: _settings())
    offline_sequence_tasks.process_offline_sequence_jobs()
    assert captured["base_url"] == "https://post-visit.example"


def test_without_a_post_visit_url_it_stays_none_and_never_uses_the_tracking_url(captured, monkeypatch) -> None:
    monkeypatch.setattr("app.core.config.get_settings", lambda: _settings(POST_VISIT_BASE_URL=None))
    offline_sequence_tasks.process_offline_sequence_jobs()
    assert captured["base_url"] is None
