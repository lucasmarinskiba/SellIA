"""Authority snapshots and actions.

A single authority number is useless: the user needs to see whether it is going
up or down, and know which part moved. So each computation is stored as a row
with its six pillar scores AND the raw signals behind them -- that way the chart
is real history, and the analyst can say *why* it moved by diffing two snapshots
instead of guessing.

Actions are the concrete work that raises a pillar. They are stored (not
regenerated on every page load) so "hecho" survives a reload and the next
snapshot can show whether doing the work actually moved the number.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.core.database import Base


class ActionStatus(str, enum.Enum):
    SUGGESTED = "suggested"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    DISMISSED = "dismissed"


class ActionMode(str, enum.Enum):
    #: SellIA can carry it out itself (it has the data and an endpoint for it).
    AUTOMATIC = "automatic"
    #: SellIA prepares everything (text, list, link) but a human has to act.
    ASSISTED = "assisted"
    #: Only the user can do it; SellIA can only explain and check it later.
    MANUAL = "manual"


class AuthoritySnapshot(Base):
    __tablename__ = "authority_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    captured_at = Column(
        DateTime(timezone=True), nullable=False, index=True,
        default=lambda: datetime.now(timezone.utc),
    )

    total_score = Column(Float, nullable=False, default=0.0)
    #: {pillar_key: {"score": float, "inputs": {...}, "missing": [...]}}
    pillars = Column(JSONB, nullable=False, default=dict)
    #: Flat, comparable measurements (review_count, profiles_linked, …) used by
    #: the analyst to explain a move between two snapshots.
    signals = Column(JSONB, nullable=False, default=dict)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class AuthorityAction(Base):
    __tablename__ = "authority_actions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    business_id = Column(UUID(as_uuid=True), nullable=True)

    #: Stable identifier of the recommendation, so re-running the analysis
    #: updates the existing row instead of stacking duplicates.
    action_key = Column(String(80), nullable=False, index=True)
    pillar = Column(String(40), nullable=False)
    #: Which psychology agent raised it (see psychology.py).
    agent = Column(String(60), nullable=True)
    principle = Column(String(80), nullable=True)

    title = Column(String(300), nullable=False)
    rationale = Column(Text, nullable=True)
    #: Ready-to-use copy when the action is "say this to your customers".
    script = Column(Text, nullable=True)
    channel = Column(String(40), nullable=True)

    mode = Column(Enum(ActionMode), nullable=False, default=ActionMode.MANUAL)
    status = Column(Enum(ActionStatus), nullable=False, default=ActionStatus.SUGGESTED)
    impact_points = Column(Integer, nullable=True)  # estimated pillar points, from the gap itself

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)


AUTHORITY_TABLES = [AuthoritySnapshot.__table__, AuthorityAction.__table__]
