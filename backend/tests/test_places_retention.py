"""Retención de datos de Google Places: solo se conserva el place_id, pasados 30 días.

Sin red ni base de datos: la sesión async se reemplaza por mocks.
"""

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domains.lead_generation import places_retention
from app.domains.lead_generation.places_retention import (
    RETENTION_DAYS,
    purge_expired_place_contacts,
    redact_place_contact,
)

NOW = datetime(2026, 10, 21, tzinfo=timezone.utc)
PLACE_CONTACT = {
    "name": "Clínica Norte",
    "phone": "+54 11 5555-0000",
    "website": "https://example.com",
    "address": "Av. Siempreviva 742",
    "maps_url": "https://maps.google.com/?cid=1",
    "place_id": "ChIJ-place-1",
    "rating": 4.6,
    "review_count": 120,
}


def _lead(contact_info, days_old=RETENTION_DAYS + 1):
    return SimpleNamespace(
        id=uuid.uuid4(),
        contact_info=dict(contact_info),
        source_detail="google_places: clinicas en Rosario",
        first_touch_at=NOW - timedelta(days=days_old),
    )


def _db(*batches):
    """Sesión mock: cada execute() devuelve el siguiente lote de leads."""
    db = AsyncMock()
    results = []
    for rows in batches:
        result = MagicMock()
        result.scalars.return_value.all.return_value = rows
        results.append(result)
    db.execute = AsyncMock(side_effect=results)
    return db


def test_redact_keeps_only_place_id():
    assert redact_place_contact(PLACE_CONTACT) == {"place_id": "ChIJ-place-1"}


def test_redact_without_place_id_returns_empty():
    assert redact_place_contact({"name": "Sin id", "phone": "+54 11 1111"}) == {}
    assert redact_place_contact(None) == {}


@pytest.mark.asyncio
async def test_purge_redacts_expired_places_leads_and_commits():
    expired = _lead(PLACE_CONTACT)
    already_redacted = _lead({"place_id": "ChIJ-place-2"})
    db = _db([expired, already_redacted])

    purged = await purge_expired_place_contacts(db, now=NOW)

    assert purged == 1
    assert expired.contact_info == {"place_id": "ChIJ-place-1"}
    assert already_redacted.contact_info == {"place_id": "ChIJ-place-2"}
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_purge_without_changes_does_not_commit():
    db = _db([_lead({"place_id": "ChIJ-place-3"})])

    purged = await purge_expired_place_contacts(db, now=NOW)

    assert purged == 0
    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_purge_query_filters_by_source_and_cutoff():
    db = _db([])

    await purge_expired_place_contacts(db, now=NOW)

    sql = str(
        db.execute.call_args.args[0].compile(compile_kwargs={"literal_binds": False})
    )
    assert "source_detail LIKE" in sql
    assert "first_touch_at <" in sql


@pytest.mark.asyncio
async def test_purge_paginates_by_id_and_commits_per_batch(monkeypatch):
    monkeypatch.setattr(places_retention, "PURGE_BATCH_SIZE", 1)
    first, second = _lead(PLACE_CONTACT), _lead(PLACE_CONTACT)
    db = _db([first], [second], [])

    purged = await purge_expired_place_contacts(db, now=NOW)

    assert purged == 2
    assert db.execute.await_count == 3
    assert db.commit.await_count == 2
    assert first.contact_info == {"place_id": "ChIJ-place-1"}
    assert second.contact_info == {"place_id": "ChIJ-place-1"}


def test_purge_task_is_registered_and_scheduled():
    from app.tasks.celery_app import celery_app

    assert (
        "app.tasks.places_retention_tasks.purge_expired_place_contacts_task"
        in celery_app.tasks
    )
    entry = celery_app.conf.beat_schedule["purge-expired-place-contacts"]
    assert (
        entry["task"]
        == "app.tasks.places_retention_tasks.purge_expired_place_contacts_task"
    )
