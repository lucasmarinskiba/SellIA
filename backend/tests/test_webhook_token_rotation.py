"""Webhook token rotation: it looks at the LAST rotation, and the business owner decides.

``rotate_webhook_tokens`` selected active channels with ``created_at`` older than 90 days, so
once a channel was that old every run rotated its token again. Each rotation invalidates the
webhook URL configured on the external platform, so the task now only *proposes* the rotation
(a pending recommendation plus an alert) and the owner accepts or rejects it.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, update

from app.domains.channels.models import ChannelConnection

NOW = datetime.now(timezone.utc)


@pytest.fixture
async def make_channel(db_session, test_user):
    from app.domains.alerts.models import Alert, Recommendation
    from app.domains.businesses.models import Business
    from app.domains.channels.models import ChannelPlatform
    from app.domains.security.models import SecretRotationLog

    business = Business(user_id=test_user.id, name=f"Rotation {uuid.uuid4().hex[:6]}")
    db_session.add(business)
    await db_session.commit()
    business_id = business.id

    async def _make(age_days: int, *, active: bool = True) -> ChannelConnection:
        ch = ChannelConnection(
            business_id=business_id, platform=ChannelPlatform.EMAIL, name=f"ch-{uuid.uuid4().hex[:6]}", is_active=active
        )
        db_session.add(ch)
        await db_session.commit()
        await db_session.execute(
            update(ChannelConnection).where(ChannelConnection.id == ch.id).values(created_at=NOW - timedelta(days=age_days))
        )
        await db_session.commit()
        return ch

    yield _make
    for table, column in (
        (Alert, Alert.business_id),
        (Recommendation, Recommendation.business_id),
        (SecretRotationLog, SecretRotationLog.business_id),
        (ChannelConnection, ChannelConnection.business_id),
    ):
        await db_session.execute(table.__table__.delete().where(column == business_id))
    await db_session.execute(Business.__table__.delete().where(Business.id == business_id))
    await db_session.commit()


async def _due(db) -> set[uuid.UUID]:
    from app.tasks.security_tasks import _channels_due_for_rotation

    return {c.id for c in await _channels_due_for_rotation(db, datetime.now(timezone.utc))}


async def _log_rotation(db, ch, *, days_ago: int, status: str = "success") -> None:
    from app.domains.security.models import SecretRotationLog

    db.add(
        SecretRotationLog(
            business_id=ch.business_id, secret_type="webhook_token", target_id=str(ch.id), status=status,
            created_at=NOW - timedelta(days=days_ago),
        )
    )
    await db.commit()


# ── which channels are due ───────────────────────────────────────────────────

async def test_old_never_rotated_channel_is_due_and_a_young_one_is_not(db_session, make_channel) -> None:
    old, young = await make_channel(120), await make_channel(10)
    due = await _due(db_session)
    assert old.id in due and young.id not in due


async def test_a_channel_rotated_recently_is_not_due(db_session, make_channel) -> None:
    ch = await make_channel(200)
    assert ch.id in await _due(db_session)
    await _log_rotation(db_session, ch, days_ago=1)
    assert ch.id not in await _due(db_session)


async def test_only_the_latest_successful_rotation_counts(db_session, make_channel) -> None:
    ch = await make_channel(400)
    await _log_rotation(db_session, ch, days_ago=95)
    assert ch.id in await _due(db_session)  # last rotation 95 days ago -> due again
    await _log_rotation(db_session, ch, days_ago=60)
    assert ch.id not in await _due(db_session)  # a newer one wins over the older log


async def test_a_failed_rotation_does_not_count(db_session, make_channel) -> None:
    ch = await make_channel(200)
    await _log_rotation(db_session, ch, days_ago=1, status="error")
    assert ch.id in await _due(db_session)


async def test_inactive_channels_are_never_due(db_session, make_channel) -> None:
    ch = await make_channel(300, active=False)
    assert ch.id not in await _due(db_session)


# ── the task proposes; the owner decides ─────────────────────────────────────

class _Session:
    def __init__(self, db) -> None:
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, *exc):
        return False


@pytest.fixture
def run_task(db_session, monkeypatch):
    from app.tasks import security_tasks

    monkeypatch.setattr(security_tasks, "AsyncSessionLocal", lambda: _Session(db_session))
    monkeypatch.setattr(security_tasks, "run_async", lambda coro: coro)  # the test already has a loop

    async def _run():
        return await security_tasks.rotate_webhook_tokens.run()

    return _run


async def _recommendations(db, business_id):
    from app.domains.alerts.models import Recommendation

    return (await db.execute(select(Recommendation).where(Recommendation.business_id == business_id))).scalars().all()


async def test_the_task_only_proposes_it_never_rotates_by_itself(db_session, make_channel, run_task) -> None:
    from app.domains.alerts.models import Alert, RecommendationStatus

    ch = await make_channel(200)
    before, business_id, channel_id = ch.webhook_token, ch.business_id, ch.id

    first = await run_task()
    await db_session.refresh(ch)

    assert first["proposed"] >= 1
    assert ch.webhook_token == before  # nothing rotated without the owner's answer
    recs = await _recommendations(db_session, business_id)
    assert len(recs) == 1 and recs[0].status == RecommendationStatus.PENDING
    assert recs[0].context_data["channel_id"] == str(channel_id)
    assert "Aceptar" in recs[0].description and "Rechazar" in recs[0].description
    alerts = (await db_session.execute(select(Alert).where(Alert.business_id == business_id))).scalars().all()
    assert len(alerts) == 1 and alerts[0].alert_metadata["kind"] == "webhook_token_rotation_proposed"


async def test_running_the_task_again_does_not_duplicate_the_proposal(db_session, make_channel, run_task) -> None:
    ch = await make_channel(200)
    business_id = ch.business_id
    await run_task()
    second = await run_task()
    third = await run_task()

    assert second["proposed"] == 0 and third["proposed"] == 0
    assert len(await _recommendations(db_session, business_id)) == 1


async def test_accepting_rotates_once_and_stops_the_channel_being_due(
    db_session, make_channel, run_task, test_user
) -> None:
    from app.domains.alerts.models import RecommendationStatus
    from app.domains.alerts.service import AlertService
    from app.domains.security.models import SecretRotationLog

    ch = await make_channel(200)
    before, business_id, channel_id, user_id = ch.webhook_token, ch.business_id, ch.id, test_user.id
    await run_task()
    rec_id = (await _recommendations(db_session, business_id))[0].id

    applied = await AlertService(db_session).apply_recommendation(rec_id, user_id)
    await db_session.refresh(ch)
    after = ch.webhook_token
    assert applied.status == RecommendationStatus.APPLIED and after != before

    again = await AlertService(db_session).apply_recommendation(rec_id, user_id)  # a second click
    await db_session.refresh(ch)
    assert again.status == RecommendationStatus.APPLIED and ch.webhook_token == after

    logs = (
        await db_session.execute(select(SecretRotationLog).where(SecretRotationLog.target_id == str(channel_id)))
    ).scalars().all()
    assert len(logs) == 1 and logs[0].rotated_by == user_id and logs[0].status == "success"
    assert channel_id not in await _due(db_session)
    assert (await run_task())["proposed"] == 0


async def test_rejecting_keeps_the_token_and_does_not_ask_again_for_90_days(db_session, make_channel, run_task) -> None:
    from app.domains.alerts.models import RecommendationStatus
    from app.domains.alerts.service import AlertService

    ch = await make_channel(200)
    before, business_id = ch.webhook_token, ch.business_id
    await run_task()
    rec_id = (await _recommendations(db_session, business_id))[0].id

    dismissed = await AlertService(db_session).dismiss_recommendation(rec_id)
    await db_session.refresh(ch)
    assert dismissed.status == RecommendationStatus.DISMISSED and ch.webhook_token == before

    assert (await run_task())["proposed"] == 0  # still due, but the owner said no
    assert len(await _recommendations(db_session, business_id)) == 1


async def test_it_asks_again_once_90_days_have_passed_since_the_last_proposal(
    db_session, make_channel, run_task
) -> None:
    from app.domains.alerts.models import Recommendation, RecommendationStatus

    ch = await make_channel(400)
    business_id = ch.business_id
    await run_task()
    await db_session.execute(
        update(Recommendation).where(Recommendation.business_id == business_id)
        .values(status=RecommendationStatus.DISMISSED, created_at=NOW - timedelta(days=91))
    )
    await db_session.commit()

    assert (await run_task())["proposed"] >= 1
    assert len(await _recommendations(db_session, business_id)) == 2


async def test_accepting_for_a_channel_that_was_deactivated_is_refused(
    db_session, make_channel, run_task, test_user
) -> None:
    from app.domains.alerts.service import AlertService
    from app.domains.channels.token_rotation import RotationNotPossible

    ch = await make_channel(200)
    business_id, channel_id, user_id = ch.business_id, ch.id, test_user.id
    await run_task()
    rec_id = (await _recommendations(db_session, business_id))[0].id
    await db_session.execute(update(ChannelConnection).where(ChannelConnection.id == channel_id).values(is_active=False))
    await db_session.commit()

    with pytest.raises(RotationNotPossible):
        await AlertService(db_session).apply_recommendation(rec_id, user_id)


# ── API: only the owner of the business can answer ───────────────────────────

async def test_the_api_lets_the_owner_accept_and_hides_it_from_other_users(
    db_session, make_channel, run_task, auth_client, test_user
) -> None:
    from app.core.deps import get_current_active_user
    from app.domains.users.models import User
    from app.main import app

    ch = await make_channel(200)
    before, business_id, owner_id = ch.webhook_token, ch.business_id, test_user.id
    await run_task()
    rec_id = (await _recommendations(db_session, business_id))[0].id

    stranger = User(
        id=uuid.uuid4(), email=f"stranger-{uuid.uuid4()}@example.com", hashed_password="x",
        full_name="Stranger", is_active=True,
    )
    db_session.add(stranger)
    await db_session.commit()
    stranger_id = stranger.id
    base = "/api/v1/alerts/recommendations"
    try:
        app.dependency_overrides[get_current_active_user] = lambda: stranger
        assert (await auth_client.get(base, params={"business_id": str(business_id)})).status_code == 404
        assert (await auth_client.post(f"{base}/{rec_id}/apply", json={})).status_code == 404
        assert (await auth_client.post(f"{base}/{rec_id}/dismiss")).status_code == 404
        await db_session.refresh(ch)
        assert ch.webhook_token == before  # the stranger changed nothing

        app.dependency_overrides[get_current_active_user] = lambda: test_user
        listed = await auth_client.get(base, params={"business_id": str(business_id)})
        assert listed.status_code == 200 and [r["id"] for r in listed.json()] == [str(rec_id)]
        accepted = await auth_client.post(f"{base}/{rec_id}/apply", json={"user_id": str(stranger_id)})
        assert accepted.status_code == 200 and accepted.json()["status"] == "applied"
        assert accepted.json()["applied_by_user_id"] == str(owner_id)  # not the id sent in the body
        await db_session.refresh(ch)
        assert ch.webhook_token != before
    finally:
        await db_session.execute(User.__table__.delete().where(User.id == stranger_id))
        await db_session.commit()
