"""Post-visit messages: queued by the trigger, sent by the beat task, over a real database (SQLite).

Pinned here:
* nothing is queued while OFFLINE_SEQUENCE_SEND_ENABLED is off, and the response says so;
* a visit is queued once per template, only with a contact email the business recorded, and never after a purchase;
* the worker sends due messages, retries with a cap, skips visits bought in the meantime, and sends nothing with the
  flag off.

No Postgres needed: JSONB / UUID are rendered as JSON / CHAR(32) for SQLite.
"""

import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import httpx
import pytest_asyncio
from fastapi import FastAPI
from sqlalchemy import event, func, select
from sqlalchemy import types as sqltypes
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.pool import StaticPool

from app.api.v1 import offline_sequences
from app.core.database import Base, get_db
from app.core.deps import get_current_user
from app.db.schema_bootstrap import ensure_unique_index_names
from app.domains.analytics.offline_models import OfflineConversion, VisitType
from app.domains.businesses.location_models import Location
from app.domains.businesses.models import Business
from app.domains.businesses.team_models import BusinessMember
from app.domains.channels.models import Conversation
from app.domains.orders.models import Order
from app.domains.sequences.offline_sequence_jobs import (
    MAX_ATTEMPTS,
    RETRY_AFTER,
    send_due_jobs,
)
from app.domains.sequences.offline_sequence_models import OfflineSequenceJob


@compiles(JSONB, "sqlite")
def _jsonb_as_json(type_, compiler, **kw):
    return "JSON"


@compiles(sqltypes.UUID, "sqlite")
def _uuid_as_char(type_, compiler, **kw):
    return "CHAR(32)"


def _make_aware(target, *_args) -> None:
    """timestamptz comes back timezone-aware from Postgres; SQLite hands back naive datetimes."""
    for key, value in list(target.__dict__.items()):
        if isinstance(value, datetime) and value.tzinfo is None:
            target.__dict__[key] = value.replace(tzinfo=timezone.utc)


event.listen(Base, "load", _make_aware, propagate=True)
event.listen(Base, "refresh", _make_aware, propagate=True)

MODELS = [Business, Location, BusinessMember, Conversation, Order, OfflineConversion, OfflineSequenceJob]
NOW = datetime(2026, 10, 22, 12, 0, tzinfo=timezone.utc)


@pytest_asyncio.fixture
async def factory():
    ensure_unique_index_names(Base.metadata)
    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=[m.__table__ for m in MODELS]))
    yield async_sessionmaker(engine, expire_on_commit=False, autoflush=False)
    await engine.dispose()


@pytest_asyncio.fixture
async def world(factory):
    owner = uuid.uuid4()
    async with factory() as s:
        biz = Business(user_id=owner, name="A")
        s.add(biz)
        await s.flush()
        loc = Location(business_id=biz.id, name="A1", address="x", city="BA", latitude=-34.6, longitude=-58.4)
        s.add(loc)
        await s.flush()

        def visit(**kw):
            return OfflineConversion(
                business_id=biz.id, location_id=loc.id, visit_type=VisitType.WALK_IN,
                entry_time=NOW - timedelta(minutes=20), **kw,
            )

        reachable = visit(visitor_email="ana@example.com", contact_collected=True)
        no_email = visit(visitor_email=None, contact_collected=True)
        no_consent = visit(visitor_email="luis@example.com", contact_collected=False)
        bought = visit(visitor_email="eva@example.com", contact_collected=True, purchased=True)
        s.add_all([reachable, no_email, no_consent, bought])
        await s.commit()
        ids = SimpleNamespace(
            biz=biz.id, loc=loc.id, reachable=reachable.id, no_email=no_email.id,
            no_consent=no_consent.id, bought=bought.id,
        )

    app = FastAPI()
    app.include_router(offline_sequences.router, prefix="/api/v1")

    async def _db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = _db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=owner)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        yield SimpleNamespace(client=client, factory=factory, **vars(ids))


def _trigger(w, conversion_id):
    return w.client.post(
        "/api/v1/offline-sequences/trigger",
        json={"business_id": str(w.biz), "location_id": str(w.loc), "conversion_id": str(conversion_id),
              "visit_type": "walk_in"},
    )


async def _job_count(factory) -> int:
    async with factory() as s:
        return (await s.execute(select(func.count()).select_from(OfflineSequenceJob))).scalar_one()


def _enable(monkeypatch, enabled: bool) -> None:
    monkeypatch.setattr(
        "app.api.v1.offline_sequences.get_settings",
        lambda: SimpleNamespace(OFFLINE_SEQUENCE_SEND_ENABLED=enabled),
    )


# ------------------------------------------------------------------ trigger


async def test_nothing_is_queued_while_sending_is_off(world, monkeypatch) -> None:
    _enable(monkeypatch, False)
    r = await _trigger(world, world.reachable)
    assert r.json()["success"] is False
    assert "desactivado" in r.json()["message"]
    assert await _job_count(world.factory) == 0


async def test_a_visit_with_contact_is_queued_once(world, monkeypatch) -> None:
    _enable(monkeypatch, True)
    first = await _trigger(world, world.reachable)
    second = await _trigger(world, world.reachable)

    assert first.json()["success"] is True
    assert second.json()["success"] is True
    assert "Ya estaba encolado" in second.json()["message"]
    assert await _job_count(world.factory) == 1


async def test_the_queued_job_carries_the_template_and_delay(world, monkeypatch) -> None:
    _enable(monkeypatch, True)
    await _trigger(world, world.reachable)
    async with world.factory() as s:
        job = (await s.execute(select(OfflineSequenceJob))).scalar_one()
    assert job.template_name == "post_visit_thank_you"
    assert job.recipient_email == "ana@example.com"
    assert job.status == "pending"
    assert job.due_at - job.created_at == timedelta(hours=1)


async def test_visits_without_reachable_contact_or_after_a_purchase_are_not_queued(world, monkeypatch) -> None:
    _enable(monkeypatch, True)
    for conversion_id in (world.no_email, world.no_consent, world.bought):
        r = await _trigger(world, conversion_id)
        assert r.json()["success"] is False, conversion_id
    assert await _job_count(world.factory) == 0


# ------------------------------------------------------------------ worker


async def _queue_job(factory, conversion_id, *, due_at=NOW - timedelta(minutes=5), attempts=0) -> uuid.UUID:
    async with factory() as s:
        conv = await s.get(OfflineConversion, conversion_id)
        job = OfflineSequenceJob(
            business_id=conv.business_id, conversion_id=conv.id, template_name="post_visit_thank_you",
            recipient_email="ana@example.com", subject="Gracias", body_text="<b>hola</b> & chau",
            status="pending", due_at=due_at, attempts=attempts, created_at=NOW,
        )
        s.add(job)
        await s.commit()
        return job.id


async def _job(factory, job_id) -> OfflineSequenceJob:
    async with factory() as s:
        return await s.get(OfflineSequenceJob, job_id)


def _sender(result=True, raises: Exception | None = None):
    calls: list[tuple[str, str, str]] = []

    async def send(to: str, subject: str, html: str) -> bool:
        calls.append((to, subject, html))
        if raises is not None:
            raise raises
        return result

    return send, calls


async def test_a_due_job_is_sent_with_escaped_html(world) -> None:
    job_id = await _queue_job(world.factory, world.reachable)
    send, calls = _sender(True)
    async with world.factory() as s:
        counts = await send_due_jobs(s, now=NOW, enabled=True, sender=send)

    assert counts["sent"] == 1
    assert calls == [("ana@example.com", "Gracias", "<p>&lt;b&gt;hola&lt;/b&gt; &amp; chau</p>")]
    job = await _job(world.factory, job_id)
    assert job.status == "sent"
    assert job.sent_at == NOW
    assert job.attempts == 1


async def test_a_job_not_yet_due_is_left_alone(world) -> None:
    job_id = await _queue_job(world.factory, world.reachable, due_at=NOW + timedelta(minutes=5))
    send, calls = _sender(True)
    async with world.factory() as s:
        await send_due_jobs(s, now=NOW, enabled=True, sender=send)
    assert calls == []
    assert (await _job(world.factory, job_id)).status == "pending"


async def test_a_rejected_send_is_retried_then_failed_at_the_cap(world) -> None:
    job_id = await _queue_job(world.factory, world.reachable)
    send, _ = _sender(False)
    for attempt in range(1, MAX_ATTEMPTS + 1):
        async with world.factory() as s:
            await send_due_jobs(s, now=NOW, enabled=True, sender=send)
        job = await _job(world.factory, job_id)
        assert job.attempts == attempt
        if attempt < MAX_ATTEMPTS:
            assert job.status == "pending"
            assert job.due_at == NOW + RETRY_AFTER
            job.due_at = NOW  # make it due again for the next round
            async with world.factory() as s:
                s.add(job)
                await s.commit()
        else:
            assert job.status == "failed"
            assert job.last_error == "el proveedor rechazó el envío"


async def test_an_exception_from_the_sender_is_recorded_and_does_not_stop_the_batch(world) -> None:
    failing = await _queue_job(world.factory, world.reachable, due_at=NOW - timedelta(minutes=10))
    ok = await _queue_job(world.factory, world.no_consent, due_at=NOW - timedelta(minutes=5))
    calls: list[str] = []

    async def send(to: str, subject: str, html: str) -> bool:
        calls.append(to)
        if len(calls) == 1:
            raise RuntimeError("provider timeout")
        return True

    async with world.factory() as s:
        counts = await send_due_jobs(s, now=NOW, enabled=True, sender=send)

    assert counts == {"sent": 1, "failed": 0, "skipped": 0, "retry": 1}
    assert (await _job(world.factory, failing)).last_error == "provider timeout"
    assert (await _job(world.factory, ok)).status == "sent"


async def test_nothing_is_sent_with_the_flag_off(world) -> None:
    job_id = await _queue_job(world.factory, world.reachable)
    send, calls = _sender(True)
    async with world.factory() as s:
        counts = await send_due_jobs(s, now=NOW, enabled=False, sender=send)
    assert counts == {"sent": 0, "failed": 0, "skipped": 0, "retry": 0}
    assert calls == []
    assert (await _job(world.factory, job_id)).status == "pending"


async def test_a_visit_bought_after_queueing_is_skipped(world) -> None:
    job_id = await _queue_job(world.factory, world.reachable)
    async with world.factory() as s:
        conv = await s.get(OfflineConversion, world.reachable)
        conv.purchased = True
        await s.commit()
    send, calls = _sender(True)
    async with world.factory() as s:
        counts = await send_due_jobs(s, now=NOW, enabled=True, sender=send)
    assert counts["skipped"] == 1
    assert calls == []
    assert (await _job(world.factory, job_id)).status == "skipped"
