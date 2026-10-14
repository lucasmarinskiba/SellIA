"""Two silent-failure bugs found in the production Celery logs.

* ``data_retention_cleanup``: one failing DELETE aborted the PostgreSQL transaction and every
  later table failed with ``InFailedSQLTransactionError`` (it cascaded into sales_invoices).
  Each table now runs in its own SAVEPOINT.
* ``Conversation.extra_data`` was a plain JSONB column: ``extra_data["x"] = ...`` on a non-empty
  dict was not detected, the UPDATE omitted it and the change was lost (chatbot-rule handoff,
  most workflow actions). It is now a ``MutableDict``.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select, text

NOW = datetime.now(timezone.utc)


@pytest.fixture
async def business(db_session, test_user):
    from app.domains.businesses.models import Business

    b = Business(user_id=test_user.id, name=f"Retention {uuid.uuid4().hex[:6]}")
    db_session.add(b)
    await db_session.commit()
    business_id = b.id  # tests expire the session, so read it once here
    yield b
    from app.domains.channels.models import Conversation

    await db_session.execute(Conversation.__table__.delete().where(Conversation.business_id == business_id))
    await db_session.execute(Business.__table__.delete().where(Business.id == business_id))
    await db_session.commit()


# ── retention cleanup ────────────────────────────────────────────────────────

class _Session:
    def __init__(self, db) -> None:
        self.db = db

    async def __aenter__(self):
        return self.db

    async def __aexit__(self, *exc):
        return False


async def test_a_failing_table_does_not_stop_the_tables_after_it(db_session, monkeypatch) -> None:
    from app.domains.security.models import DataRetentionLog, SecretRotationLog
    from app.tasks import security_tasks

    old = SecretRotationLog(
        secret_type=f"retention-test-{uuid.uuid4().hex[:8]}", status="success", created_at=NOW - timedelta(days=30)
    )
    db_session.add(old)
    await db_session.commit()
    marker = old.secret_type

    # the failing table first, then one that must still be cleaned
    monkeypatch.setattr(security_tasks, "DEFAULT_HARD_RETENTION", {"zz_table_that_does_not_exist": 1, "secret_rotation_logs": 1})
    monkeypatch.setattr(security_tasks, "AsyncSessionLocal", lambda: _Session(db_session))
    monkeypatch.setattr(security_tasks, "run_async", lambda coro: coro)  # the test already has a loop

    before = (await db_session.execute(select(DataRetentionLog.id))).scalars().all()
    deleted = await security_tasks.data_retention_cleanup.run()

    assert deleted.get("secret_rotation_logs", 0) >= 1
    remaining = (await db_session.execute(select(SecretRotationLog).where(SecretRotationLog.secret_type == marker))).scalars().all()
    assert remaining == []

    new_logs = (
        await db_session.execute(select(DataRetentionLog).where(DataRetentionLog.id.notin_(before)))
    ).scalars().all()
    by_table = {entry.table_name: entry for entry in new_logs}
    assert by_table["zz_table_that_does_not_exist"].status == "error"
    assert by_table["secret_rotation_logs"].status == "success"  # not InFailedSQLTransactionError
    assert by_table["secret_rotation_logs"].records_deleted >= 1

    for entry in new_logs:
        await db_session.delete(entry)
    await db_session.commit()
    assert (await db_session.execute(text("select 1"))).scalar_one() == 1


# ── Conversation.extra_data ──────────────────────────────────────────────────

async def test_in_place_edit_of_conversation_extra_data_is_persisted(db_session, business) -> None:
    from app.domains.channels.models import Conversation

    conv = Conversation(business_id=business.id, extra_data={"stage": "new"})
    db_session.add(conv)
    await db_session.commit()
    conv_id = conv.id

    await db_session.refresh(conv)  # commit expired it; the app edits an already loaded object
    conv.extra_data["awaiting_human"] = True  # the pattern used by the chatbot-rule handoff
    conv.extra_data["handoff_reason"] = "regla"
    await db_session.commit()

    db_session.expire_all()
    fresh = (await db_session.execute(select(Conversation).where(Conversation.id == conv_id))).scalar_one()
    assert fresh.extra_data == {"stage": "new", "awaiting_human": True, "handoff_reason": "regla"}


async def test_handoff_helper_still_works_with_the_mutable_column(db_session, business) -> None:
    from app.domains.channels.handoff import awaiting_human_clause, mark_awaiting_human
    from app.domains.channels.models import Conversation

    conv = Conversation(business_id=business.id)
    db_session.add(conv)
    await db_session.commit()

    mark_awaiting_human(conv, "pidió un humano")
    await db_session.commit()

    flagged = (await db_session.execute(select(Conversation.id).where(awaiting_human_clause()))).scalars().all()
    assert conv.id in flagged
