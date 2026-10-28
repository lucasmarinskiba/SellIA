"""Harvey weekly summary: counts from the business's own rows, a fixed 7-day window, rules for next steps."""

# The db fixture comes from test_harvey, so every test argument "redefines" it.
# ruff: noqa: F811

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from test_harvey import _Biz, _setup, db  # noqa: F401 - db is a pytest fixture

from app.domains.alerts.models import Alert
from app.domains.crm.models import Deal, LeadStage
from app.domains.harvey import weekly
from app.domains.harvey.models import HarveyOutboxItem, HarveyReply

NOW = datetime(2026, 10, 28, 12, 0, tzinfo=timezone.utc)


def _item(biz, prospect, status, sent_at=None, reply_id=None, step=1):
    return HarveyOutboxItem(
        business_id=biz.id, prospect_id=prospect.id, step=step, to_email=prospect.email, subject="hola", body="x",
        status=status, sent_at=sent_at, reply_id=reply_id,
    )


def _reply(biz, prospect, classification, when, needs_human=False):
    return HarveyReply(
        business_id=biz.id, prospect_id=prospect.id, body="x", classification=classification,
        needs_human=needs_human, created_at=when,
    )


@pytest_asyncio.fixture
async def crm(db):
    async with db.bind.begin() as conn:
        for m in (Deal, Alert):
            await conn.run_sync(lambda c, m=m: m.__table__.create(bind=c, checkfirst=True))
    return db


@pytest.mark.asyncio
async def test_only_the_last_seven_days_count(db):
    svc, biz, profile, prospect = await _setup(db)
    old, recent = NOW - timedelta(days=9), NOW - timedelta(days=2)
    db.add_all([
        _item(biz, prospect, "sent", recent), _item(biz, prospect, "sent", old, step=2),
        _item(biz, prospect, "pending_review", step=3),
        _reply(biz, prospect, "interested", recent), _reply(biz, prospect, "question", recent),
        _reply(biz, prospect, "objection", old),
    ])
    await db.commit()
    s = await weekly.weekly_summary(db, biz.id, NOW)
    assert s["sent"] == 1 and s["pending_review"] == 1
    assert s["replies"]["total"] == 2 and s["replies"]["interested"] == 1
    assert s["prospects_total"] == 1


@pytest.mark.asyncio
async def test_a_reply_that_already_has_an_answer_does_not_need_you(db):
    svc, biz, profile, prospect = await _setup(db)
    waiting = _reply(biz, prospect, "handoff", NOW - timedelta(days=1), needs_human=True)
    answered = _reply(biz, prospect, "handoff", NOW - timedelta(days=1), needs_human=True)
    db.add_all([waiting, answered])
    await db.commit()
    db.add(_item(biz, prospect, "pending_review", reply_id=answered.id))
    await db.commit()
    assert (await weekly.weekly_summary(db, biz.id, NOW))["needs_you"] == 1


@pytest.mark.asyncio
async def test_another_business_sees_none_of_it(db):
    svc, biz, profile, prospect = await _setup(db)
    db.add(_item(biz, prospect, "sent", NOW - timedelta(days=1)))
    await db.commit()
    s = await weekly.weekly_summary(db, _Biz().id, NOW)
    assert s["sent"] == 0 and s["prospects_total"] == 0 and s["replies"]["total"] == 0


@pytest.mark.asyncio
async def test_without_a_crm_the_summary_still_works(db):
    svc, biz, profile, prospect = await _setup(db)
    assert (await weekly.weekly_summary(db, biz.id, NOW))["deals"] == {"created": 0, "won": 0, "won_value": 0.0}


@pytest.mark.asyncio
async def test_deals_brought_by_harvey_are_counted_and_valued(crm):
    svc, biz, profile, prospect = await _setup(crm)
    crm.add_all([
        Deal(business_id=biz.id, title="a", source_channel="harvey", created_at=NOW - timedelta(days=1)),
        Deal(business_id=biz.id, title="b", source_channel="harvey", stage=LeadStage.CLOSED_WON, value=1500,
             created_at=NOW - timedelta(days=3), actual_close_date=NOW - timedelta(days=1)),
        Deal(business_id=biz.id, title="otro canal", source_channel="whatsapp", created_at=NOW - timedelta(days=1)),
    ])
    await crm.commit()
    d = (await weekly.weekly_summary(crm, biz.id, NOW))["deals"]
    assert d["created"] == 2 and d["won"] == 1 and d["won_value"] == 1500.0


def _s(**kw):
    base = {
        "sent": 0, "prospects_total": 5, "prospects_new": 0, "prospects_added": 0, "pending_review": 0, "needs_you": 0,
        "replies": {"total": 0, "interested": 0}, "deals": {"created": 0, "won": 0, "won_value": 0.0},
    }
    base.update(kw)
    return base


def test_next_steps_follow_the_numbers():
    assert weekly.next_steps(_s()) == []
    assert any("aprobación" in t for t in weekly.next_steps(_s(pending_review=3)))
    assert any("atiendas vos" in t for t in weekly.next_steps(_s(needs_you=1)))
    assert any("sin contactar" in t for t in weekly.next_steps(_s(prospects_new=4)))
    assert any("Todavía no hay prospectos" in t for t in weekly.next_steps(_s(prospects_total=0)))
    assert any("ninguna respuesta" in t for t in weekly.next_steps(_s(sent=25)))
    assert not any("ninguna respuesta" in t for t in weekly.next_steps(_s(sent=25, replies={"total": 1, "interested": 0})))
    assert any("reseña" in t for t in weekly.next_steps(_s(deals={"created": 1, "won": 1, "won_value": 10.0})))


def test_alert_text_reports_the_week_and_the_first_two_steps():
    s = _s(sent=12, pending_review=2, needs_you=1, replies={"total": 3, "interested": 1},
           deals={"created": 1, "won": 0, "won_value": 0.0})
    s["next_steps"] = weekly.next_steps(s)
    title, body = weekly.alert_text(s)
    assert title == "Tu semana con Harvey" and "12 email(s) enviados" in body and "1 interesadas" in body
    assert "1 oportunidad(es) en el CRM" in body and "aprobación" in body
