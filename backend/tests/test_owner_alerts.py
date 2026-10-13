"""Owner alerts: they must be creatable, and must not repeat on every run.

Four paths built ``Alert`` rows with ``AlertSeverity.HIGH/MEDIUM/LOW`` (the enum is
INFO/WARNING/CRITICAL) and ``message=`` / ``is_read=`` (the columns are ``description`` /
``status``), so none ever created an alert. The AOC health report was fixed first and then
flooded production with ~900 identical alerts an hour, because its "once every 6 hours"
state lived in an object Celery rebuilds on every run. These tests cover the other three
(weekly report, self-repair, pipeline) and the shared factory.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update

NOW = datetime.now(timezone.utc)


# ── fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
async def make_business(db_session, test_user):
    from app.domains.alerts.models import Alert
    from app.domains.businesses.models import Business

    created = []

    async def _make(name: str | None = None) -> Business:
        b = Business(user_id=test_user.id, name=name or f"Owner Alerts {uuid.uuid4().hex[:6]}")
        db_session.add(b)
        await db_session.commit()
        created.append(b.id)
        return b

    yield _make
    for biz_id in created:
        await db_session.execute(Alert.__table__.delete().where(Alert.business_id == biz_id))
        await db_session.execute(Business.__table__.delete().where(Business.id == biz_id))
    await db_session.commit()


async def _alerts(db, business_id):
    from app.domains.alerts.models import Alert

    return (await db.execute(select(Alert).where(Alert.business_id == business_id))).scalars().all()


async def _age(db, business_id, by: timedelta) -> None:
    from app.domains.alerts.models import Alert

    await db.execute(
        update(Alert).where(Alert.business_id == business_id).values(created_at=datetime.now(timezone.utc) - by)
    )
    await db.commit()


# ── factory ──────────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("level", "expected"),
    [("critical", "CRITICAL"), ("high", "WARNING"), ("medium", "WARNING"), ("warning", "WARNING"),
     ("low", "INFO"), ("info", "INFO"), ("HIGH", "WARNING"), (None, "INFO"), ("nonsense", "INFO")],
)
def test_severity_maps_every_caller_vocabulary_onto_a_real_member(level, expected) -> None:
    from app.domains.alerts.factory import severity_for
    from app.domains.alerts.models import AlertSeverity

    assert severity_for(level) is AlertSeverity[expected]


def test_build_alert_uses_the_real_columns_and_tags_the_kind() -> None:
    from app.domains.alerts.factory import build_alert
    from app.domains.alerts.models import Alert, AlertSeverity

    biz = uuid.uuid4()
    alert = build_alert(biz, "titulo", "cuerpo", kind="k", level="high", dedupe_key="d", created_at=NOW)

    assert isinstance(alert, Alert)
    assert (alert.business_id, alert.title, alert.description) == (biz, "titulo", "cuerpo")
    assert alert.severity is AlertSeverity.WARNING
    assert alert.alert_metadata == {"kind": "k", "dedupe_key": "d"}
    assert alert.created_at == NOW


async def test_alert_sent_recently_respects_kind_key_window_and_business(db_session, make_business) -> None:
    from app.domains.alerts.factory import alert_sent_recently, build_alert

    a, b = await make_business(), await make_business()
    window = timedelta(hours=6)
    assert not await alert_sent_recently(db_session, a.id, "k", window)

    db_session.add(build_alert(a.id, "t", "d", kind="k", dedupe_key="x"))
    await db_session.commit()

    assert await alert_sent_recently(db_session, a.id, "k", window)
    assert await alert_sent_recently(db_session, a.id, "k", window, dedupe_key="x")
    assert not await alert_sent_recently(db_session, a.id, "k", window, dedupe_key="y")  # other key
    assert not await alert_sent_recently(db_session, a.id, "other", window)               # other kind
    assert not await alert_sent_recently(db_session, b.id, "k", window)                   # other business

    await _age(db_session, a.id, timedelta(hours=7))
    assert not await alert_sent_recently(db_session, a.id, "k", window)                   # window passed


async def test_a_str_enum_dedupe_key_is_stored_and_matched_by_its_value(db_session, make_business) -> None:
    from app.domains.agents.autonomous.self_repair import FaultType
    from app.domains.alerts.factory import alert_sent_recently, build_alert

    biz = await make_business()
    db_session.add(build_alert(biz.id, "t", "d", kind="k", dedupe_key=FaultType.WORKFLOW_STUCK))
    await db_session.commit()

    assert (await _alerts(db_session, biz.id))[0].alert_metadata["dedupe_key"] == FaultType.WORKFLOW_STUCK.value
    assert await alert_sent_recently(db_session, biz.id, "k", timedelta(hours=1), dedupe_key=FaultType.WORKFLOW_STUCK)


# ── weekly executive report ──────────────────────────────────────────────────

class _Center:
    async def run_quick_health_check(self, business_id):
        return {"health_score": 100, "load_state": "normal"}


async def test_weekly_report_creates_one_alert_per_business_and_does_not_repeat_on_restarts(
    db_session, make_business, monkeypatch
) -> None:
    """Beat starts from a committed, stale schedule file, so the 'weekly' task fires on each
    deploy. Every run after the first must neither create an alert nor call the LLM."""
    from app.domains.agents import ai_reply
    from app.tasks.autonomous_tasks import _weekly_report_for

    llm_calls: list[uuid.UUID] = []

    async def fake_llm(**kwargs):
        llm_calls.append(kwargs["business_id"])
        return "briefing de la IA"

    monkeypatch.setattr(ai_reply, "generate_raw_ai_response", fake_llm)

    biz = await make_business()
    results = [await _weekly_report_for(db_session, _Center(), biz.id, "Mi Negocio", NOW) for _ in range(5)]

    assert results == [True, False, False, False, False]
    assert llm_calls == [biz.id]                         # the expensive call ran once
    alerts = await _alerts(db_session, biz.id)
    assert len(alerts) == 1
    assert alerts[0].alert_metadata["kind"] == "weekly_executive_report"
    assert alerts[0].title.startswith("📊 Reporte Ejecutivo Semanal")


async def test_weekly_report_runs_again_after_the_week_has_passed(db_session, make_business, monkeypatch) -> None:
    from app.domains.agents import ai_reply
    from app.tasks.autonomous_tasks import _weekly_report_for

    async def fake_llm(**kwargs):
        return "briefing"

    monkeypatch.setattr(ai_reply, "generate_raw_ai_response", fake_llm)
    biz = await make_business()

    assert await _weekly_report_for(db_session, _Center(), biz.id, "N", NOW)
    await _age(db_session, biz.id, timedelta(days=5, hours=23))
    assert not await _weekly_report_for(db_session, _Center(), biz.id, "N", NOW)
    await _age(db_session, biz.id, timedelta(days=6, hours=1))
    assert await _weekly_report_for(db_session, _Center(), biz.id, "N", NOW)
    assert len(await _alerts(db_session, biz.id)) == 2


async def test_weekly_report_counts_only_the_businesses_own_messages(
    db_session, make_business, monkeypatch
) -> None:
    """Message has no business_id; the count used to be platform-wide, so every owner's
    report showed every tenant's traffic."""
    from app.domains.agents import ai_reply
    from app.domains.channels.models import Conversation, Message, MessageDirection
    from app.tasks.autonomous_tasks import _weekly_report_for

    async def fake_llm(**kwargs):
        return kwargs["user_prompt"]  # echo the context so the test can read the count

    monkeypatch.setattr(ai_reply, "generate_raw_ai_response", fake_llm)
    mine, other = await make_business(), await make_business()

    async def add_messages(biz, n: int) -> None:
        conv = Conversation(business_id=biz.id)
        db_session.add(conv)
        await db_session.flush()
        for i in range(n):
            db_session.add(Message(conversation_id=conv.id, direction=MessageDirection.INBOUND, content=f"m{i}"))
        await db_session.commit()

    await add_messages(mine, 2)
    await add_messages(other, 5)

    await _weekly_report_for(db_session, _Center(), mine.id, "Mine", NOW)

    body = (await _alerts(db_session, mine.id))[0].description
    assert "Mensajes procesados esta semana: 2" in body
    assert "7" not in body.split("Mensajes procesados esta semana:")[1].split("\n")[0]

    # clean the conversations/messages this test created (cascade on conversation delete)
    for biz in (mine, other):
        await db_session.execute(Conversation.__table__.delete().where(Conversation.business_id == biz.id))
    await db_session.commit()


async def test_weekly_report_is_skipped_without_consuming_the_week_when_the_llm_is_down(
    db_session, make_business, monkeypatch
) -> None:
    from app.domains.agents import ai_reply
    from app.tasks.autonomous_tasks import _weekly_report_for

    answers = iter([None, None, "informe real de la IA"])

    async def flaky_llm(**kwargs):
        return next(answers)

    monkeypatch.setattr(ai_reply, "generate_raw_ai_response", flaky_llm)
    biz = await make_business()

    assert [await _weekly_report_for(db_session, _Center(), biz.id, "N", NOW) for _ in range(3)] == [False, False, True]
    alerts = await _alerts(db_session, biz.id)
    assert [a.description for a in alerts] == ["informe real de la IA"]  # never the bare context lines


# ── self-repair ──────────────────────────────────────────────────────────────

async def test_self_repair_notification_is_created_and_not_repeated_every_cycle(db_session, make_business) -> None:
    from app.domains.agents.autonomous.self_repair import (
        FaultReport,
        FaultType,
        SelfRepairEngine,
    )
    from app.domains.alerts.models import AlertSeverity

    biz = await make_business()
    engine = SelfRepairEngine(db_session)
    kind_a, kind_b = list(FaultType)[:2]
    fault = FaultReport(fault_type=kind_a, severity="high", description="el flujo no avanza", repair_attempts=3)
    other = FaultReport(fault_type=kind_b, severity="critical", description="otra falla", repair_attempts=3)

    for _ in range(6):  # a persistent fault is detected again on every cycle
        await engine._notify_owner_of_fault(fault, biz.id)

    alerts = await _alerts(db_session, biz.id)
    assert len(alerts) == 1
    assert alerts[0].severity is AlertSeverity.WARNING          # "high" -> WARNING
    assert "el flujo no avanza" in alerts[0].description
    assert alerts[0].alert_metadata["kind"] == "self_repair_fault"
    assert alerts[0].alert_metadata["dedupe_key"] == kind_a.value

    # a different type of fault is a different alert, with its own severity
    await engine._notify_owner_of_fault(other, biz.id)
    assert len(await _alerts(db_session, biz.id)) == 2

    # the same fault is reported again once the repeat window has passed
    await _age(db_session, biz.id, timedelta(hours=6, minutes=1))
    await engine._notify_owner_of_fault(fault, biz.id)
    assert len(await _alerts(db_session, biz.id)) == 3


# ── pipeline ─────────────────────────────────────────────────────────────────

async def test_pipeline_owner_alert_is_created_then_suppressed_for_the_same_message(
    db_session, make_business
) -> None:
    from app.domains.agents.pipeline_automations import PipelineAutomationEngine
    from app.domains.alerts.models import AlertSeverity

    biz = await make_business()
    engine = PipelineAutomationEngine(db_session)
    action = {"message": "Deal estancado hace 14 dias", "priority": "critical"}

    first = await engine._send_owner_alert(action, str(biz.id))
    repeats = [await engine._send_owner_alert(action, str(biz.id)) for _ in range(5)]
    different = await engine._send_owner_alert({"message": "Otro aviso", "priority": "low"}, str(biz.id))

    assert first == {"status": "alert_created"}
    assert all(r["status"] == "alert_suppressed" for r in repeats)
    assert different == {"status": "alert_created"}
    alerts = {a.title: a for a in await _alerts(db_session, biz.id)}
    assert len(alerts) == 2
    assert alerts["[SellIA Auto] Deal estancado hace 14 dias"].severity is AlertSeverity.WARNING  # "critical" priority -> high
    assert alerts["[SellIA Auto] Otro aviso"].severity is AlertSeverity.WARNING                   # medium
