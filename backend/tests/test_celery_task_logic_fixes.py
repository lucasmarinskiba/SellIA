"""Three Celery task bugs seen in the production worker logs, each a code path that
referred to something that does not exist:

* ``handoff_alert_sender``: ``Conversation.awaiting_human`` (no such column; the flag is a
  key of ``extra_data``). The autopilot escalations set it as a plain attribute, which
  is never persisted.
* ``schedule_content_posts_task``: ``ContentCalendar.approval_status`` (it belongs to
  ``GeneratedContent``).
* AOC health report: ``AlertSeverity.LOW`` / ``.HIGH`` (the enum has INFO/WARNING/CRITICAL)
  and ``Alert(message=..., is_read=...)`` (the fields are ``description`` / ``status``).
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

NOW = datetime.now(timezone.utc)


@pytest.fixture
async def business(db_session, test_user):
    from app.domains.businesses.models import Business

    b = Business(user_id=test_user.id, name=f"Logic Fix Co {uuid.uuid4().hex[:6]}")
    db_session.add(b)
    await db_session.commit()
    yield b
    await db_session.delete(b)
    await db_session.commit()


# ── handoff ──────────────────────────────────────────────────────────────────

async def test_mark_awaiting_human_persists_even_when_extra_data_is_not_empty(db_session, business) -> None:
    """An in-place edit of a non-empty JSONB dict is not detected; the helper reassigns."""
    from app.domains.channels.handoff import mark_awaiting_human
    from app.domains.channels.models import Conversation

    conv = Conversation(business_id=business.id, extra_data={"source": "whatsapp"})
    db_session.add(conv)
    await db_session.commit()

    conv_id = conv.id  # read before expire_all(): an expired instance would trigger IO here
    mark_awaiting_human(conv, "Escalado por el autopilot")
    await db_session.commit()
    db_session.expire_all()

    fresh = (await db_session.execute(select(Conversation).where(Conversation.id == conv_id))).scalar_one()
    assert fresh.extra_data == {
        "source": "whatsapp",
        "awaiting_human": True,
        "handoff_reason": "Escalado por el autopilot",
    }


async def test_handoff_query_finds_only_flagged_and_recent_conversations(db_session, business) -> None:
    from app.domains.channels.handoff import mark_awaiting_human
    from app.domains.channels.models import Conversation
    from app.tasks.autonomous_tasks import _conversations_awaiting_human

    flagged_recent = Conversation(business_id=business.id)
    flagged_old = Conversation(business_id=business.id)
    not_flagged = Conversation(business_id=business.id, extra_data={"awaiting_human": False})
    mark_awaiting_human(flagged_recent)
    mark_awaiting_human(flagged_old)
    db_session.add_all([flagged_recent, flagged_old, not_flagged])
    await db_session.commit()
    flagged_old.updated_at = NOW - timedelta(hours=2)
    await db_session.commit()

    found = await _conversations_awaiting_human(db_session, NOW - timedelta(minutes=5))

    assert {c.id for c in found} == {flagged_recent.id}


# ── content calendar ─────────────────────────────────────────────────────────

async def test_due_calendar_posts_filter_uses_real_columns_and_requires_opt_in(db_session, business) -> None:
    from app.domains.automations.models import ContentCalendar
    from app.tasks.content_tasks import _due_calendar_posts_stmt

    def entry(**kw) -> ContentCalendar:
        base = {
            "business_id": business.id, "scheduled_at": NOW - timedelta(minutes=1), "platform": "instagram",
            "content_format": "feed_post", "status": "scheduled", "auto_publish": True, "requires_approval": True,
        }
        return ContentCalendar(**{**base, **kw})

    due_no_approval_needed = entry(requires_approval=False)
    due_and_approved = entry(approved_at=NOW)
    awaiting_approval = entry()                                   # requires approval, none given
    opted_out = entry(auto_publish=False, requires_approval=False)  # not allowed to go out alone
    in_the_future = entry(requires_approval=False, scheduled_at=NOW + timedelta(hours=1))
    already_published = entry(requires_approval=False, status="published")
    db_session.add_all([due_no_approval_needed, due_and_approved, awaiting_approval, opted_out,
                        in_the_future, already_published])
    await db_session.commit()

    found = (await db_session.execute(_due_calendar_posts_stmt(business.id, NOW))).scalars().all()

    assert {e.id for e in found} == {due_no_approval_needed.id, due_and_approved.id}


# ── AOC health alert ─────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("score", "expected"),
    [(100, "INFO"), (70, "INFO"), (69, "WARNING"), (50, "WARNING"), (49, "CRITICAL"), (0, "CRITICAL")],
)
def test_health_alert_uses_severities_that_exist_and_valid_fields(score: int, expected: str) -> None:
    from app.domains.agents.autonomous.operations_center import (
        AutonomousOperationsCenter,
        SystemHealthSnapshot,
    )
    from app.domains.alerts.models import Alert, AlertSeverity

    center = AutonomousOperationsCenter(db=None)
    snapshot = SystemHealthSnapshot(overall_health_score=score)

    alert = center._build_health_alert(uuid.uuid4(), snapshot, "🟢", "cuerpo del reporte")

    assert isinstance(alert, Alert)
    assert alert.severity == AlertSeverity[expected]
    assert alert.description == "cuerpo del reporte"
    assert f"{score}/100" in alert.title
    assert alert.created_at == snapshot.timestamp
