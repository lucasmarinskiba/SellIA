"""Phase 29 voice sales: call lifecycle, playbook extraction and recommendation, on the real database.

Rewritten from the synchronous version that was quarantined in known_failures.txt: the voice domain is
async since the voice port, and the old tests used a `db` fixture that no longer exists. These tests
assert what the code stores and returns, and that nothing is invented when there is no AI key or no data.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select

from app.domains.enterprise.voice_sales import (
    PlaybookExtractor,
    PlaybookRecommender,
    VoiceCallManager,
)

NIL_UUID = "00000000-0000-0000-0000-000000000000"


@pytest.fixture
async def business(db_session, test_user):
    from app.domains.businesses.models import Business, BusinessType

    row = Business(user_id=test_user.id, name=f"Voice29 {uuid.uuid4().hex[:6]}", type=BusinessType.SERVICES)
    db_session.add(row)
    await db_session.commit()
    business_id = row.id
    yield row
    from app.models.voice_sales import SalesPlaybook

    await db_session.execute(SalesPlaybook.__table__.delete().where(SalesPlaybook.name.like("test29-%")))
    await db_session.execute(Business.__table__.delete().where(Business.id == business_id))
    await db_session.commit()


@pytest.fixture
async def deal(db_session, business):
    from app.domains.crm.models import Deal
    from app.models.voice_sales import VoiceCall

    row = Deal(business_id=business.id, title="Deal voz 29")
    db_session.add(row)
    await db_session.commit()
    deal_id = row.id  # plain uuid: _count() expires ORM objects, and reading them later would lazy-load
    yield deal_id
    await db_session.execute(VoiceCall.__table__.delete().where(VoiceCall.deal_id == str(deal_id)))
    await db_session.execute(Deal.__table__.delete().where(Deal.id == deal_id))
    await db_session.commit()


@pytest.fixture
async def manager(db_session):
    return VoiceCallManager(db_session)


async def _count(db, model, **where) -> int:
    db.expire_all()
    query = select(func.count()).select_from(model)
    for column, value in where.items():
        query = query.where(getattr(model, column) == value)
    return (await db.execute(query)).scalar_one()


# ── Call lifecycle ─────────────────────────────────────────────────────────


async def test_initiate_call_stores_the_call(db_session, manager, deal) -> None:
    from app.models.voice_sales import VoiceCall

    result = await manager.initiate_call("prospect-29", str(deal))

    assert result.status == "initiated"
    assert result.prospect_id == "prospect-29"
    assert result.deal_id == str(deal)
    assert await _count(db_session, VoiceCall, id=uuid.UUID(result.call_id)) == 1


async def test_each_turn_is_stored_as_a_transcript_line(db_session, manager, deal) -> None:
    from app.models.voice_sales import CallTranscript

    result = await manager.initiate_call("prospect-29", str(deal))
    reply = await manager.handle_call_input(result.call_id, "Cuéntame más sobre el producto")

    assert isinstance(reply, str) and reply.strip()
    db_session.expire_all()
    speakers = (
        await db_session.execute(select(CallTranscript.speaker).where(CallTranscript.call_id == uuid.UUID(result.call_id)))
    ).scalars().all()
    assert sorted(speakers) == ["ai", "prospect"]


async def test_input_for_an_unknown_call_says_so(manager) -> None:
    reply = await manager.handle_call_input(str(uuid.uuid4()), "hola")

    assert reply == "Call not found"


async def test_end_call_completes_the_call_and_stores_its_metrics(db_session, manager, deal) -> None:
    from app.models.voice_sales import VoiceCall, VoiceCallMetrics

    result = await manager.initiate_call("prospect-29", str(deal))
    await manager.handle_call_input(result.call_id, "Sí, me interesa, agendemos")
    ended = await manager.end_call(result.call_id, "meeting_booked")

    assert ended["call_id"] == result.call_id
    assert ended["outcome"] == "meeting_booked"
    assert isinstance(ended["meeting_booked"], bool)
    db_session.expire_all()
    call = (await db_session.execute(select(VoiceCall).where(VoiceCall.id == uuid.UUID(result.call_id)))).scalar_one()
    assert call.status == "completed" and call.outcome == "meeting_booked"
    assert await _count(db_session, VoiceCallMetrics, call_id=uuid.UUID(result.call_id)) == 1


async def test_a_call_runs_start_to_metrics_in_one_flow(db_session, manager, deal) -> None:
    from app.models.voice_sales import VoiceCallMetrics

    before = await _count(db_session, VoiceCallMetrics)
    result = await manager.initiate_call("prospect-29", str(deal))
    assert await manager.handle_call_input(result.call_id, "Hola, me interesa")
    assert await manager.handle_call_input(result.call_id, "¿Podemos agendar una reunión?")
    await manager.end_call(result.call_id, "meeting_booked")

    assert await _count(db_session, VoiceCallMetrics) == before + 1


# ── Playbook extraction ────────────────────────────────────────────────────


async def test_without_an_ai_key_no_playbook_is_invented(db_session, manager, deal) -> None:
    """Extraction reads the AI model. Without a key it must return nothing, not guess a playbook."""
    for _ in range(2):
        result = await manager.initiate_call("prospect-29", str(deal))
        await manager.handle_call_input(result.call_id, "Me interesa mucho")
        await manager.end_call(result.call_id, "meeting_booked")

    assert await PlaybookExtractor(db_session).extract_playbooks(["rep-1"]) == []


async def test_consolidation_names_the_cluster_and_invents_no_win_rate(db_session) -> None:
    cluster = [
        {"opening": "Hola, soy de SellIA", "win_rate": 0.75},
        {"opening": "Hola, soy de SellIA", "win_rate": 0.78},
    ]

    playbook = PlaybookExtractor(db_session)._consolidate_cluster(cluster)

    assert playbook.name == "Playbook extraído: Hola, soy de SellIA"
    assert playbook.win_rate is None  # the old placeholder was a made-up 0.75
    assert playbook.extracted_from_calls == 2


async def test_clusters_group_playbooks_by_opening(db_session) -> None:
    playbooks = [{"opening": "A"}, {"opening": "A"}, {"opening": "B"}]

    clusters = PlaybookExtractor(db_session)._cluster_playbooks(playbooks)

    assert sorted(len(c) for c in clusters) == [1, 2]


# ── Playbook recommendation ────────────────────────────────────────────────


async def test_no_deal_no_recommendation(db_session) -> None:
    assert await PlaybookRecommender(db_session).recommend_playbook(NIL_UUID) is None


async def test_recommends_the_playbook_for_the_business_type_and_stage(db_session, deal) -> None:
    from app.domains.crm.models import Deal
    from app.models.voice_sales import SalesPlaybook

    stage = (await db_session.execute(select(Deal.stage).where(Deal.id == deal))).scalar_one()
    playbook = SalesPlaybook(
        name=f"test29-{uuid.uuid4().hex[:6]}", industry="services", deal_stage=stage.value,
        win_rate=0.42, steps=[{"step": 1, "name": "Apertura"}],
    )
    db_session.add(playbook)
    await db_session.commit()

    recommendation = await PlaybookRecommender(db_session).recommend_playbook(str(deal))

    assert recommendation is not None
    assert recommendation.playbook_id == str(playbook.id)
    assert recommendation.next_step == "Apertura"


async def test_a_playbook_without_a_measured_win_rate_loses_to_a_measured_one(db_session, deal) -> None:
    """Postgres sorts NULL first on DESC. A playbook with no measured win rate must not win by default."""
    from app.domains.crm.models import Deal
    from app.models.voice_sales import SalesPlaybook

    stage = (await db_session.execute(select(Deal.stage).where(Deal.id == deal))).scalar_one()
    unmeasured = SalesPlaybook(name=f"test29-a-{uuid.uuid4().hex[:6]}", industry="services", deal_stage=stage.value, win_rate=None, steps=[])
    measured = SalesPlaybook(name=f"test29-b-{uuid.uuid4().hex[:6]}", industry="services", deal_stage=stage.value, win_rate=0.3, steps=[])
    db_session.add_all([unmeasured, measured])
    await db_session.commit()

    recommendation = await PlaybookRecommender(db_session).recommend_playbook(str(deal))

    assert recommendation is not None
    assert recommendation.playbook_id == str(measured.id)
