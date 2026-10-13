"""The "this conversation needs a human" flag, in one place.

The flag lives inside ``Conversation.extra_data`` (JSONB) under ``awaiting_human``;
there is no ``awaiting_human`` column. ``channels.services`` already writes and reads
it that way, and its guard on the auto-reply path is what stops the AI from answering
a conversation a human has to take over.

Two things went wrong elsewhere, both from treating it as a column:

* the autopilot escalations did ``conv.awaiting_human = True``, which sets a plain
  Python attribute on the ORM object: nothing is persisted, so the conversation was
  never flagged, the AI kept answering and no human was alerted;
* ``handoff_alert_sender`` filtered on ``Conversation.awaiting_human``, which does not
  exist, so the task raised ``AttributeError`` on every run.

Reassigning the whole dict (rather than ``extra_data["x"] = ...``) matters:
``extra_data`` is a plain JSONB column, not a ``MutableDict``, so an in-place edit of
a non-empty dict is not detected and the UPDATE silently omits it.
"""

from __future__ import annotations

from typing import Any

from app.domains.channels.models import Conversation


def mark_awaiting_human(conversation: Conversation, reason: str | None = None) -> None:
    """Flag ``conversation`` as waiting for a human. The caller commits."""
    extra: dict[str, Any] = dict(conversation.extra_data or {})
    extra["awaiting_human"] = True
    if reason:
        extra["handoff_reason"] = reason
    conversation.extra_data = extra


def awaiting_human_clause():
    """SQL condition matching conversations flagged by :func:`mark_awaiting_human`."""
    return Conversation.extra_data["awaiting_human"].astext == "true"
