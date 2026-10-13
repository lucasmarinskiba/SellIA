"""The AOC health report must not be created on every 5-minute cycle.

``CYCLE_INTERVALS["health_report"]`` asks for one report every 6 hours, but the cadence was
kept in ``_last_cycle_times``, a per-instance dict, and Celery builds a new
``AutonomousOperationsCenter`` for every run, so the report was always "due". Once the
alert-building code worked (see test_celery_task_logic_fixes), production got ~900 identical
INFO alerts an hour: 462 in the first 20 minutes, one per business per cycle.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update


@pytest.fixture
async def business(db_session, test_user):
    from app.domains.businesses.models import Business

    b = Business(user_id=test_user.id, name=f"AOC Co {uuid.uuid4().hex[:6]}")
    db_session.add(b)
    await db_session.commit()
    yield b
    from app.domains.alerts.models import Alert

    await db_session.execute(Alert.__table__.delete().where(Alert.business_id == b.id))
    await db_session.delete(b)
    await db_session.commit()


async def _health_alerts(db, business_id):
    from app.domains.alerts.models import Alert

    result = await db.execute(select(Alert).where(Alert.business_id == business_id))
    return result.scalars().all()


async def _send(db, business_id, score: int) -> None:
    """One Celery run: a brand-new center each time, exactly like the task does."""
    from app.domains.agents.autonomous.operations_center import (
        AutonomousOperationsCenter,
        SystemHealthSnapshot,
    )

    center = AutonomousOperationsCenter(db)
    await center._send_health_report(SystemHealthSnapshot(overall_health_score=score), business_id)


async def _age_alerts(db, business_id, by: timedelta) -> None:
    from app.domains.alerts.models import Alert

    await db.execute(
        update(Alert).where(Alert.business_id == business_id)
        .values(created_at=datetime.now(timezone.utc) - by)
    )
    await db.commit()


async def test_repeated_runs_with_a_fresh_center_each_time_create_one_alert(db_session, business) -> None:
    """The production scenario: the 5-minute cycle, many times over."""
    for _ in range(12):  # one hour of 5-minute cycles
        await _send(db_session, business.id, score=100)

    alerts = await _health_alerts(db_session, business.id)
    assert len(alerts) == 1
    assert "Reporte de Salud SellIA" in alerts[0].title


async def test_a_new_report_is_created_once_the_regular_interval_has_passed(db_session, business) -> None:
    await _send(db_session, business.id, score=100)
    await _age_alerts(db_session, business.id, timedelta(hours=5, minutes=59))
    await _send(db_session, business.id, score=100)
    assert len(await _health_alerts(db_session, business.id)) == 1  # 6 h not reached yet

    await _age_alerts(db_session, business.id, timedelta(hours=6, minutes=1))
    await _send(db_session, business.id, score=100)
    assert len(await _health_alerts(db_session, business.id)) == 2


async def test_a_degraded_score_reports_sooner_but_not_on_every_cycle(db_session, business) -> None:
    await _send(db_session, business.id, score=40)
    for _ in range(11):
        await _send(db_session, business.id, score=40)
    assert len(await _health_alerts(db_session, business.id)) == 1

    await _age_alerts(db_session, business.id, timedelta(minutes=61))
    await _send(db_session, business.id, score=40)  # an hour later, still degraded
    assert len(await _health_alerts(db_session, business.id)) == 2


async def test_reports_of_different_businesses_do_not_suppress_each_other(db_session, business, test_user) -> None:
    from app.domains.businesses.models import Business

    other = Business(user_id=test_user.id, name=f"AOC Other {uuid.uuid4().hex[:6]}")
    db_session.add(other)
    await db_session.commit()
    try:
        await _send(db_session, business.id, score=100)
        await _send(db_session, other.id, score=100)
        assert len(await _health_alerts(db_session, business.id)) == 1
        assert len(await _health_alerts(db_session, other.id)) == 1
    finally:
        from app.domains.alerts.models import Alert

        await db_session.execute(Alert.__table__.delete().where(Alert.business_id == other.id))
        await db_session.delete(other)
        await db_session.commit()
