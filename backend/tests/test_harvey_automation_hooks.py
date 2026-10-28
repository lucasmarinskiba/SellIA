"""Harvey events reach the business's own workflows, and only the workflows that asked for them."""

# The db fixture comes from test_harvey, so every test argument "redefines" it.
# ruff: noqa: F811

import pytest
import pytest_asyncio
from test_harvey import _fake_model, _setup, db  # noqa: F401 - db is a pytest fixture

from app.domains.alerts.models import Alert
from app.domains.automations.engine import WorkflowEngine
from app.domains.channels.models import BookingEvent
from app.domains.crm.models import Deal
from app.domains.harvey import automation_hooks, crm_sync


@pytest_asyncio.fixture
async def crm(db, monkeypatch):
    async with db.bind.begin() as conn:
        for m in (Deal, Alert, BookingEvent):
            await conn.run_sync(lambda c, m=m: m.__table__.create(bind=c, checkfirst=True))
    fired: list[tuple[str, dict]] = []

    async def capture(_db, trigger, business_id, data):
        fired.append((trigger, data))

    monkeypatch.setattr(automation_hooks, "fire", capture)
    return db, fired


# ── what Harvey fires ─────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_a_first_reply_fires_new_lead_and_a_later_one_fires_stage_changed(crm, monkeypatch):
    db, fired = crm
    svc, biz, profile, prospect = await _setup(db)
    _fake_model(monkeypatch, {"classification": "question", "answer": "x"})
    await svc.record_reply(biz, profile, prospect, "¿Envían a Rosario?")
    assert [t for t, _ in fired] == ["new_lead"]
    data = fired[0][1]
    assert data["email"] == "ana@cliente.com" and data["channel"] == "email" and "Rosario" in data["content"]

    _fake_model(monkeypatch, {"classification": "interested", "answer": "ok"})
    await svc.record_reply(biz, profile, prospect, "Dale, me interesa")
    assert [t for t, _ in fired] == ["new_lead", "stage_changed"]
    assert fired[1][1]["from"] == "contacted" and fired[1][1]["to"] == "qualified"


@pytest.mark.asyncio
async def test_a_repeat_with_no_stage_change_fires_nothing_more(crm, monkeypatch):
    db, fired = crm
    svc, biz, profile, prospect = await _setup(db)
    _fake_model(monkeypatch, {"classification": "interested", "answer": "ok"})
    await svc.record_reply(biz, profile, prospect, "Me interesa")
    await svc.record_reply(biz, profile, prospect, "Sí, en serio, me interesa")
    assert [t for t, _ in fired] == ["new_lead"]


@pytest.mark.asyncio
async def test_a_booking_and_a_payment_fire_their_triggers(crm, monkeypatch):
    db, fired = crm
    svc, biz, profile, prospect = await _setup(db)
    _fake_model(monkeypatch, {"classification": "interested", "answer": "ok"})
    await svc.record_reply(biz, profile, prospect, "Me interesa")
    fired.clear()

    await crm_sync.on_booking(db, biz.id, "ana@cliente.com", None)
    await crm_sync.attribute_payment(db, biz.id, "ana@cliente.com", "2500", "ARS")
    assert [t for t, _ in fired] == ["appointment_scheduled", "revenue_event"]
    assert fired[1][1]["value"] == 2500.0 and fired[1][1]["currency"] == "ARS"


@pytest.mark.asyncio
async def test_nothing_fires_when_the_sync_does_nothing(crm):
    db, fired = crm
    svc, biz, profile, prospect = await _setup(db)
    assert not await crm_sync.on_booking(db, biz.id, "alguien@otro.com", None)
    assert not await crm_sync.attribute_payment(db, biz.id, "alguien@otro.com", 10)
    assert fired == []


# ── the hook itself ───────────────────────────────────────────────────────
@pytest.mark.asyncio
async def test_an_engine_failure_never_propagates(db, monkeypatch):
    async def boom(self, **kw):
        raise RuntimeError("engine down")

    svc0, biz0, profile0, prospect0 = await _setup(db)
    before = prospect0.email

    monkeypatch.setattr(WorkflowEngine, "process_trigger", boom)
    svc, biz, profile, prospect = await _setup(db)
    await automation_hooks.fire(db, "new_lead", biz.id, {"email": "a@b.com"})  # must not raise
    assert prospect.email == before == prospect0.email  # the caller's objects are untouched, not expired


@pytest.mark.asyncio
async def test_the_hook_tags_the_source_and_ignores_unknown_triggers(db, monkeypatch):
    seen = {}

    async def capture(self, **kw):
        seen.update(kw)

    monkeypatch.setattr(WorkflowEngine, "process_trigger", capture)
    svc, biz, profile, prospect = await _setup(db)
    await automation_hooks.fire(db, "order_created", biz.id, {})
    assert seen == {}
    await automation_hooks.fire(db, "new_lead", biz.id, {"email": "a@b.com"})
    assert seen["trigger_data"]["source"] == "harvey" and seen["conversation_id"] is None
    assert seen["trigger_type"].value == "new_lead"


# ── the engine's source rule ──────────────────────────────────────────────
def _match(config, data):
    return WorkflowEngine(None)._check_trigger_config(config, data)


def test_a_harvey_event_runs_only_workflows_that_ask_for_harvey():
    event = {"source": "harvey", "content": "me interesa el precio", "channel": "email"}
    assert not _match({}, event)  # an existing chat automation is left alone
    assert not _match({"keywords": ["precio"]}, event)
    assert _match({"sources": ["harvey"]}, event)
    assert _match({"sources": ["harvey"], "keywords": ["precio"]}, event)
    assert not _match({"sources": ["harvey"], "keywords": ["garantía"]}, event)
    assert _match({"sources": ["harvey", "chat"]}, event)


def test_chat_events_keep_working_exactly_as_before():
    chat = {"content": "hola, precio?", "channel": "whatsapp"}
    assert _match({}, chat) and _match(None, chat)
    assert _match({"keywords": ["precio"]}, chat)
    assert not _match({"keywords": ["envío"]}, chat)
    assert _match({"channels": ["whatsapp"]}, chat) and not _match({"channels": ["email"]}, chat)
    assert _match({"sources": ["chat"]}, chat)
    assert not _match({"sources": ["harvey"]}, chat)  # a Harvey-only workflow ignores chat leads
