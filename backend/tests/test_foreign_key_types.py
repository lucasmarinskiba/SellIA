"""A ForeignKey column must have the same type family as the column it points at.

Eight columns named ``deal_id`` were ``VARCHAR(255)`` while ``deals.id`` is a UUID, so PostgreSQL
refused to create the constraint (DatatypeMismatchError) and the tables, plus the three that depend on
``voice_calls``, were skipped on every boot: voice_calls, ai_call_scripts, meeting_bookings,
close_attempts, discovery_responses, need_narratives, objection_handling, sales_conversations,
call_transcripts, playbook_executions, voice_call_metrics. (``email_verification_tokens.user_id`` and
``account_approvals.user_id`` had the same mismatch against ``users.id``.) The columns are now ``UUID(as_uuid=False)``:
the Python side keeps handling ``str`` ids, the database stores a real uuid.
"""

from __future__ import annotations

import pytest
from sqlalchemy import String, Text, text
from sqlalchemy.dialects.postgresql import UUID

TABLES_WITH_DEAL_ID = [
    "voice_calls",
    "ai_call_scripts",
    "meeting_bookings",
    "close_attempts",
    "discovery_responses",
    "need_narratives",
    "objection_handling",
    "sales_conversations",
]
TABLES_THAT_DEPEND_ON_THEM = ["call_transcripts", "playbook_executions", "voice_call_metrics"]

#: Known mismatches that are not created through the ORM metadata. ``computer_use_audit_logs`` keeps
#: ``String(36)`` ids and production creates it with raw DDL (see sellbot), so its column types must
#: not be changed under an existing table.
KNOWN_EXCEPTIONS = {"computer_use_audit_logs"}


def _family(column_type) -> str:
    if isinstance(column_type, UUID):
        return "uuid"
    if isinstance(column_type, (String, Text)):
        return "text"
    return type(column_type).__name__.lower()


def _target(fk):
    from sqlalchemy.exc import NoReferencedTableError

    try:
        return fk.column
    except NoReferencedTableError:
        return None


def _registered_metadata():
    import app.main  # noqa: F401  -- load every router and model, like the web process
    from app.core.database import Base
    from app.db.schema_bootstrap import _import_all_models

    _import_all_models()
    return Base.metadata


def test_foreign_key_columns_have_the_type_of_the_column_they_reference() -> None:
    metadata = _registered_metadata()
    mismatches = []
    for table in metadata.tables.values():
        if table.name in KNOWN_EXCEPTIONS:
            continue
        for fk in table.foreign_keys:
            target = _target(fk)
            if target is None:  # an unresolved target is covered by test_foreign_keys_resolve
                continue
            if _family(fk.parent.type) != _family(target.type):
                mismatches.append(f"{table.name}.{fk.parent.name} ({fk.parent.type}) -> {fk._colspec} ({target.type})")
    assert not mismatches, mismatches


def test_deal_id_is_a_uuid_that_python_still_sees_as_a_string() -> None:
    from app.models.psychology_sales import CloseAttempt
    from app.models.voice_sales import VoiceCall

    for model in (VoiceCall, CloseAttempt):
        column_type = model.__table__.c.deal_id.type
        assert isinstance(column_type, UUID) and column_type.as_uuid is False


@pytest.mark.parametrize("table", TABLES_WITH_DEAL_ID + TABLES_THAT_DEPEND_ON_THEM)
async def test_the_table_is_created_by_the_bootstrap(db_session, table: str) -> None:
    """The test database is built with ensure_all_tables (see conftest)."""
    exists = (await db_session.execute(text("SELECT to_regclass(:name)"), {"name": table})).scalar_one()
    assert exists is not None


async def test_a_deal_id_round_trips_as_a_string(db_session, test_user) -> None:
    """Code that passes ``str(deal.id)`` keeps working: it is accepted on insert and on filters."""
    import uuid

    from sqlalchemy import select

    from app.domains.businesses.models import Business
    from app.domains.crm.models import Deal
    from app.models.psychology_sales import DiscoveryResponse

    business = Business(user_id=test_user.id, name=f"Deal {uuid.uuid4().hex[:6]}")
    db_session.add(business)
    await db_session.commit()
    business_id = business.id
    deal = Deal(business_id=business_id, title="d")
    db_session.add(deal)
    await db_session.commit()
    deal_id = str(deal.id)

    required = [c.name for c in DiscoveryResponse.__table__.columns if not c.nullable and c.default is None and c.server_default is None]
    values = {"deal_id": deal_id}
    for name in required:
        if name not in values and name != "id":
            values[name] = "x"
    db_session.add(DiscoveryResponse(**values))
    await db_session.commit()
    try:
        stored = (await db_session.execute(select(DiscoveryResponse.deal_id).where(DiscoveryResponse.deal_id == deal_id))).scalar_one()
        assert str(stored) == deal_id  # written with a str id, found again by filtering on a str id
    finally:
        await db_session.execute(DiscoveryResponse.__table__.delete().where(DiscoveryResponse.deal_id == deal_id))
        await db_session.execute(Deal.__table__.delete().where(Deal.id == deal.id))
        await db_session.execute(Business.__table__.delete().where(Business.id == business_id))
        await db_session.commit()
