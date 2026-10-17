"""Regression tests for the cold-lead follow-up scan (app.domains.channels.followup_service).

Production log, right after startup:

    ERROR | app.core.followup_scheduler | Follow-up loop iteration failed:
    greenlet_spawn has not been called; can't call await_only() here.

Cause: scan_and_send_followups() loaded every cold Conversation up front, and its
per-conversation error handler did `await db.rollback()` and then read
`conversation.id` for the log line. rollback() expires *every* instance loaded in
the session, so that attribute read tried a lazy refresh outside an `await` ->
MissingGreenlet. It escaped the handler, aborted the whole scan and hid the real
error. The same expiry also broke every conversation still waiting in the batch.

These tests drive the scan with a session built like the production one
(app.core.database.AsyncSessionLocal) against real Postgres.
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import pytest
import pytest_asyncio
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domains.businesses.models import Business
from app.domains.channels.followup_service import (
    COLD_THRESHOLD_HOURS,
    MAX_FOLLOWUPS_PER_CONVERSATION,
    scan_and_send_followups,
)
from app.domains.channels.models import (
    ChannelConnection,
    ChannelPlatform,
    ChannelStatus,
    Conversation,
    Message,
    MessageDirection,
)
from app.domains.users.models import User


class _FakeConnector:
    """Stands in for the platform connector; fails for chosen recipients."""

    def __init__(self, fail_for: set[str] | None = None) -> None:
        self.fail_for = fail_for or set()
        self.sent: list[tuple[str, str]] = []

    async def send_message(self, recipient: str, content: str, content_type: str = "text") -> dict[str, Any]:
        if recipient in self.fail_for:
            raise RuntimeError(f"platform rejected message for {recipient}")
        self.sent.append((recipient, content))
        return {"id": f"fake-{len(self.sent)}"}


@pytest.fixture
def connector(monkeypatch: pytest.MonkeyPatch) -> _FakeConnector:
    fake = _FakeConnector()
    monkeypatch.setattr(
        "app.domains.channels.services.get_connector",
        lambda *_args, **_kwargs: fake,
    )
    return fake


@pytest_asyncio.fixture
async def channel(db_session: AsyncSession) -> ChannelConnection:
    # The scan is global, so start every test from an empty conversations table.
    await db_session.execute(delete(Conversation))
    user = User(
        id=uuid.uuid4(),
        email=f"followup-{uuid.uuid4()}@example.com",
        hashed_password="hashed",
        full_name="Follow-up Test",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    business = Business(id=uuid.uuid4(), user_id=user.id, name="Follow-up Test Biz")
    db_session.add(business)
    await db_session.flush()
    conn = ChannelConnection(
        id=uuid.uuid4(),
        business_id=business.id,
        platform=ChannelPlatform.WHATSAPP,
        name="wa",
        status=ChannelStatus.CONNECTED,
    )
    db_session.add(conn)
    await db_session.commit()
    return conn


async def _seed_cold_conversation(
    db: AsyncSession,
    channel: ChannelConnection,
    external_id: str,
    *,
    outbound_last: bool = True,
) -> uuid.UUID:
    silent_since = datetime.now(timezone.utc) - timedelta(hours=COLD_THRESHOLD_HOURS + 24)
    conversation = Conversation(
        id=uuid.uuid4(),
        business_id=channel.business_id,
        channel_connection_id=channel.id,
        external_id=external_id,
        last_message_at=silent_since,
    )
    db.add(conversation)
    await db.flush()
    db.add(
        Message(
            conversation_id=conversation.id,
            direction=MessageDirection.OUTBOUND if outbound_last else MessageDirection.INBOUND,
            content="hola",
            created_at=silent_since,
        )
    )
    await db.commit()
    return conversation.id


async def _reload(conversation_id: uuid.UUID) -> Conversation:
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Conversation).where(Conversation.id == conversation_id))
        return result.scalar_one()


async def _outbound_count(conversation_id: uuid.UUID) -> int:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Message).where(
                Message.conversation_id == conversation_id,
                Message.direction == MessageDirection.OUTBOUND,
            )
        )
        return len(result.scalars().all())


async def test_sends_nudge_and_records_it(
    db_session: AsyncSession, channel: ChannelConnection, connector: _FakeConnector
) -> None:
    conv_id = await _seed_cold_conversation(db_session, channel, "5491100000001")

    async with AsyncSessionLocal() as db:
        stats = await scan_and_send_followups(db)

    assert stats == {"scanned": 1, "sent": 1, "skipped_replied": 0, "errors": 0}
    assert [recipient for recipient, _ in connector.sent] == ["5491100000001"]
    conv = await _reload(conv_id)
    assert conv.followup_count == 1
    assert conv.last_followup_sent_at is not None
    assert await _outbound_count(conv_id) == 2  # seeded + the nudge

    # The nudge bumps last_message_at, so the very next scan must not repeat it.
    async with AsyncSessionLocal() as db:
        again = await scan_and_send_followups(db)
    assert again["scanned"] == 0
    assert len(connector.sent) == 1


async def test_failed_send_does_not_abort_scan_or_raise_missing_greenlet(
    db_session: AsyncSession, channel: ChannelConnection, connector: _FakeConnector
) -> None:
    """The bug: the error handler's rollback() expired every loaded Conversation,
    then the handler (and each remaining loop iteration) read `.id` on an expired
    instance -> MissingGreenlet, aborting the scan. One bad conversation must not
    stop the others, whichever order the database returns them in."""
    bad = await _seed_cold_conversation(db_session, channel, "bad-recipient")
    good_a = await _seed_cold_conversation(db_session, channel, "good-a")
    good_b = await _seed_cold_conversation(db_session, channel, "good-b")
    connector.fail_for = {"bad-recipient"}

    async with AsyncSessionLocal() as db:
        stats = await scan_and_send_followups(db)  # must not raise

    assert stats == {"scanned": 3, "sent": 2, "skipped_replied": 0, "errors": 1}
    assert sorted(recipient for recipient, _ in connector.sent) == ["good-a", "good-b"]
    assert (await _reload(bad)).followup_count == 0
    assert (await _reload(bad)).last_followup_sent_at is None
    assert (await _reload(good_a)).followup_count == 1
    assert (await _reload(good_b)).followup_count == 1


async def test_conversation_without_channel_is_counted_as_error_not_raised(
    db_session: AsyncSession, channel: ChannelConnection, connector: _FakeConnector
) -> None:
    """ON DELETE SET NULL leaves ACTIVE conversations with no channel; sending
    raises ValueError("Conversación sin canal asociado") for them."""
    orphan = await _seed_cold_conversation(db_session, channel, "orphan")
    await db_session.execute(
        Conversation.__table__.update()
        .where(Conversation.id == orphan)
        .values(channel_connection_id=None)
    )
    await db_session.commit()

    async with AsyncSessionLocal() as db:
        stats = await scan_and_send_followups(db)

    assert stats["errors"] == 1
    assert stats["sent"] == 0
    assert connector.sent == []


async def test_skips_when_customer_wrote_last(
    db_session: AsyncSession, channel: ChannelConnection, connector: _FakeConnector
) -> None:
    await _seed_cold_conversation(db_session, channel, "replied", outbound_last=False)

    async with AsyncSessionLocal() as db:
        stats = await scan_and_send_followups(db)

    assert stats == {"scanned": 1, "sent": 0, "skipped_replied": 1, "errors": 0}
    assert connector.sent == []


async def test_followup_cap_is_enforced(
    db_session: AsyncSession, channel: ChannelConnection, connector: _FakeConnector
) -> None:
    conv_id = await _seed_cold_conversation(db_session, channel, "capped")
    await db_session.execute(
        Conversation.__table__.update()
        .where(Conversation.id == conv_id)
        .values(followup_count=MAX_FOLLOWUPS_PER_CONVERSATION)
    )
    await db_session.commit()

    async with AsyncSessionLocal() as db:
        stats = await scan_and_send_followups(db)

    assert stats["scanned"] == 0
    assert connector.sent == []
