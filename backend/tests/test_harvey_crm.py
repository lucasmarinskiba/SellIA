"""Harvey ↔ CRM/alerts/payments: a reply becomes a deal and an alert, a payment closes it. Isolated SQLite."""

# The db fixture comes from test_harvey, so every test argument "redefines" it.
# ruff: noqa: F811

import pytest
import pytest_asyncio
from sqlalchemy import select
from test_harvey import _Biz, _fake_model, _setup, db  # noqa: F401 - db is a pytest fixture

from app.domains.alerts.models import Alert
from app.domains.crm.models import Deal, LeadStage
from app.domains.harvey import crm_sync


@pytest_asyncio.fixture
async def crm(db):
    async with db.bind.begin() as conn:
        for m in (Deal, Alert):
            await conn.run_sync(lambda c, m=m: m.__table__.create(bind=c, checkfirst=True))
    return db


async def _deals(db, biz):
    return list((await db.execute(select(Deal).where(Deal.business_id == biz.id))).scalars())


async def _alerts(db, biz):
    return list((await db.execute(select(Alert).where(Alert.business_id == biz.id))).scalars())


@pytest.mark.asyncio
async def test_an_interested_reply_creates_a_qualified_deal_and_a_critical_alert(crm, monkeypatch):
    svc, biz, profile, prospect = await _setup(crm)
    _fake_model(monkeypatch, {"classification": "interested", "answer": "¡Genial!"})
    await svc.record_reply(biz, profile, prospect, "Me interesa, contame más")

    (deal,) = await _deals(crm, biz)
    assert deal.stage is LeadStage.QUALIFIED and deal.source_channel == "harvey"
    assert deal.contact_email == "ana@cliente.com" and deal.extra_data["harvey_prospect_id"] == str(prospect.id)
    (alert,) = await _alerts(crm, biz)
    assert alert.severity.value == "critical" and alert.deal_id == deal.id
    assert "Me interesa" in alert.description and "Respuestas" in alert.recommended_action


@pytest.mark.asyncio
async def test_a_second_reply_updates_the_same_deal_instead_of_duplicating(crm, monkeypatch):
    svc, biz, profile, prospect = await _setup(crm)
    _fake_model(monkeypatch, {"classification": "question", "answer": "Sí, enviamos."})
    await svc.record_reply(biz, profile, prospect, "¿Envían a Rosario?")
    _fake_model(monkeypatch, {"classification": "interested", "answer": "Perfecto"})
    await svc.record_reply(biz, profile, prospect, "Dale, me interesa")

    (deal,) = await _deals(crm, biz)
    assert deal.stage is LeadStage.QUALIFIED and deal.extra_data["last_reply_class"] == "interested"
    assert len(await _alerts(crm, biz)) == 2


@pytest.mark.asyncio
async def test_a_refusal_closes_an_existing_deal_but_creates_none(crm, monkeypatch):
    svc, biz, profile, prospect = await _setup(crm)
    _fake_model(monkeypatch, {"classification": "not_interested", "answer": ""})
    await svc.record_reply(biz, profile, prospect, "No, gracias")
    assert await _deals(crm, biz) == []  # nothing to close, nothing worth a CRM row

    svc2, biz2, profile2, prospect2 = await _setup(crm, _Biz())
    _fake_model(monkeypatch, {"classification": "question", "answer": "x"})
    await svc2.record_reply(biz2, profile2, prospect2, "¿Precio?")
    prospect2.status = "new"
    _fake_model(monkeypatch, {"classification": "opt_out", "answer": ""})
    await svc2.record_reply(biz2, profile2, prospect2, "No me escriban más")
    (deal,) = await _deals(crm, biz2)
    assert deal.stage is LeadStage.CLOSED_LOST and "no lo contacten" in deal.close_reason


@pytest.mark.asyncio
async def test_a_reply_is_saved_even_if_the_crm_is_broken(db, monkeypatch):
    svc, biz, profile, prospect = await _setup(db)  # no deals/alerts tables here: the sync must fail quietly
    _fake_model(monkeypatch, {"classification": "interested", "answer": "ok"})
    reply = await svc.record_reply(biz, profile, prospect, "Me interesa")
    assert reply.classification == "interested" and (await svc.list_replies(biz.id))[0].id == reply.id


@pytest.mark.asyncio
async def test_deals_and_alerts_stay_within_their_business(crm, monkeypatch):
    svc, biz, profile, prospect = await _setup(crm)
    _fake_model(monkeypatch, {"classification": "interested", "answer": "ok"})
    await svc.record_reply(biz, profile, prospect, "Me interesa")
    other = _Biz()
    assert await _deals(crm, other) == [] and await _alerts(crm, other) == []
    assert await crm_sync.find_deal(crm, other.id, "ana@cliente.com") is None


@pytest.mark.asyncio
async def test_a_payment_from_a_prospect_closes_the_deal_as_won(crm, monkeypatch):
    svc, biz, profile, prospect = await _setup(crm)
    _fake_model(monkeypatch, {"classification": "interested", "answer": "ok"})
    await svc.record_reply(biz, profile, prospect, "Me interesa")

    assert await crm_sync.attribute_payment(crm, biz.id, "ANA@Cliente.com", "15000.50", "ARS")
    (deal,) = await _deals(crm, biz)
    assert deal.stage is LeadStage.CLOSED_WON and float(deal.value) == 15000.50 and deal.probability == 100
    assert not await crm_sync.attribute_payment(crm, biz.id, "ana@cliente.com", 1)  # already won: not credited twice
    assert not await crm_sync.attribute_payment(crm, biz.id, "alguien@otro.com", 10)
    assert not await crm_sync.attribute_payment(crm, biz.id, "", 10)


@pytest.mark.asyncio
async def test_a_later_reply_never_reopens_a_won_deal(crm, monkeypatch):
    svc, biz, profile, prospect = await _setup(crm)
    _fake_model(monkeypatch, {"classification": "interested", "answer": "ok"})
    await svc.record_reply(biz, profile, prospect, "Me interesa")
    await crm_sync.attribute_payment(crm, biz.id, "ana@cliente.com", 100)
    prospect.status = "new"
    _fake_model(monkeypatch, {"classification": "objection", "answer": "x"})
    await svc.record_reply(biz, profile, prospect, "Che, ¿y la garantía?")
    (deal,) = await _deals(crm, biz)
    assert deal.stage is LeadStage.CLOSED_WON
