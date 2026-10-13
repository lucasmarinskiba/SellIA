"""Webhook token rotation must look at the LAST rotation, not at the channel's age.

``rotate_webhook_tokens`` selected active channels with ``created_at`` older than 90 days, so
once a channel was that old every run rotated its token again. Each rotation invalidates the
webhook URL configured on the external platform.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import update

NOW = datetime.now(timezone.utc)


@pytest.fixture
async def make_channel(db_session, test_user):
    from app.domains.businesses.models import Business
    from app.domains.channels.models import ChannelConnection, ChannelPlatform
    from app.domains.security.models import SecretRotationLog

    business = Business(user_id=test_user.id, name=f"Rotation {uuid.uuid4().hex[:6]}")
    db_session.add(business)
    await db_session.commit()
    created: list[uuid.UUID] = []

    async def _make(age_days: int, *, active: bool = True) -> ChannelConnection:
        ch = ChannelConnection(
            business_id=business.id, platform=ChannelPlatform.EMAIL, name=f"ch-{uuid.uuid4().hex[:6]}", is_active=active
        )
        db_session.add(ch)
        await db_session.commit()
        await db_session.execute(
            update(ChannelConnection).where(ChannelConnection.id == ch.id).values(created_at=NOW - timedelta(days=age_days))
        )
        await db_session.commit()
        created.append(ch.id)
        return ch

    yield _make
    await db_session.execute(SecretRotationLog.__table__.delete().where(SecretRotationLog.business_id == business.id))
    await db_session.execute(ChannelConnection.__table__.delete().where(ChannelConnection.business_id == business.id))
    await db_session.execute(Business.__table__.delete().where(Business.id == business.id))
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


async def test_old_never_rotated_channel_is_due_and_a_young_one_is_not(db_session, make_channel) -> None:
    old, young = await make_channel(120), await make_channel(10)
    due = await _due(db_session)
    assert old.id in due and young.id not in due


async def test_a_channel_rotated_recently_is_not_rotated_again(db_session, make_channel) -> None:
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


async def test_inactive_channels_are_never_rotated(db_session, make_channel) -> None:
    ch = await make_channel(300, active=False)
    assert ch.id not in await _due(db_session)


async def test_rotating_twice_in_a_row_changes_each_token_only_once(db_session, make_channel, monkeypatch) -> None:
    """The task itself: the second run, right after the first, must be a no-op."""
    from app.tasks import security_tasks

    ch = await make_channel(200)
    before = ch.webhook_token

    class _Session:
        async def __aenter__(self):
            return db_session

        async def __aexit__(self, *exc):
            return False

    monkeypatch.setattr(security_tasks, "AsyncSessionLocal", lambda: _Session())
    monkeypatch.setattr(security_tasks, "run_async", lambda coro: coro)  # the test already has a loop

    first = await security_tasks.rotate_webhook_tokens.run()
    await db_session.refresh(ch)
    after_first = ch.webhook_token
    second = await security_tasks.rotate_webhook_tokens.run()
    await db_session.refresh(ch)

    assert first["rotated"] >= 1 and second["rotated"] == 0
    assert after_first != before and ch.webhook_token == after_first
