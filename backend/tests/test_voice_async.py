"""The voice sales endpoints must work end to end and store what they say they stored.

The routes and the call manager used the synchronous ``db.query`` API on the async session, so every
call returned 400 ("'AsyncSession' object has no attribute 'query'"), and the playbook recommender read
``deal.industry`` (not a column) inside a try that answered None: it could never recommend anything.
These tests go through the HTTP routes and count rows in the database.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select

NIL_DEAL = "00000000-0000-0000-0000-000000000000"


@pytest.fixture
async def deal(db_session, test_user):
    from app.domains.businesses.models import Business, BusinessType
    from app.domains.crm.models import Deal

    business = Business(user_id=test_user.id, name=f"Voz {uuid.uuid4().hex[:6]}", type=BusinessType.SERVICES)
    db_session.add(business)
    await db_session.flush()
    row = Deal(business_id=business.id, title="Deal voz")
    db_session.add(row)
    await db_session.commit()
    deal_id, business_id = row.id, business.id
    yield deal_id
    from app.models.voice_sales import SalesPlaybook, VoiceCall

    await db_session.execute(VoiceCall.__table__.delete().where(VoiceCall.deal_id == str(deal_id)))
    await db_session.execute(SalesPlaybook.__table__.delete().where(SalesPlaybook.name.like("test-playbook-%")))
    await db_session.execute(Deal.__table__.delete().where(Deal.id == deal_id))
    await db_session.execute(Business.__table__.delete().where(Business.id == business_id))
    await db_session.commit()


async def _calls(db, deal_id) -> int:
    db.expire_all()
    from app.models.voice_sales import VoiceCall

    return (await db.execute(select(func.count()).select_from(VoiceCall).where(VoiceCall.deal_id == str(deal_id)))).scalar_one()


async def _start_call(async_client, deal_id) -> str:
    response = await async_client.post(
        "/api/v1/voice/initiate-call", json={"prospect_id": "prospect-1", "deal_id": str(deal_id)}
    )
    assert response.status_code == 200, response.text
    return response.json()["call_id"]


async def test_initiate_call_stores_the_call(db_session, async_client, deal) -> None:
    call_id = await _start_call(async_client, deal)

    assert await _calls(db_session, deal) == 1
    assert uuid.UUID(call_id)


async def test_initiate_call_for_an_unknown_deal_is_refused_and_stores_nothing(db_session, async_client) -> None:
    response = await async_client.post(
        "/api/v1/voice/initiate-call", json={"prospect_id": "prospect-1", "deal_id": NIL_DEAL}
    )

    assert response.status_code == 400, response.text
    assert "not found" in response.text
    assert await _calls(db_session, NIL_DEAL) == 0


async def test_call_input_stores_both_turns(db_session, async_client, deal) -> None:
    from app.models.voice_sales import CallTranscript

    call_id = await _start_call(async_client, deal)
    response = await async_client.post("/api/v1/voice/call/input", json={"call_id": call_id, "input_text": "Cuéntame más"})

    assert response.status_code == 200, response.text
    assert response.json()["response"]
    db_session.expire_all()
    turns = (
        await db_session.execute(select(CallTranscript.speaker).where(CallTranscript.call_id == uuid.UUID(call_id)))
    ).scalars().all()
    assert sorted(turns) == ["ai", "prospect"]


async def test_call_input_for_an_unknown_call_says_so(async_client) -> None:
    response = await async_client.post("/api/v1/voice/call/input", json={"call_id": str(uuid.uuid4()), "input_text": "hola"})

    assert response.status_code == 200, response.text
    assert response.json()["response"] == "Call not found"


async def test_ending_a_call_completes_it_and_stores_its_metrics(db_session, async_client, deal) -> None:
    from app.models.voice_sales import VoiceCall, VoiceCallMetrics

    call_id = await _start_call(async_client, deal)
    await async_client.post("/api/v1/voice/call/input", json={"call_id": call_id, "input_text": "Sí, me interesa"})
    response = await async_client.post("/api/v1/voice/call/end", json={"call_id": call_id, "outcome": "qualified"})

    assert response.status_code == 200, response.text
    assert response.json()["outcome"] == "qualified"
    db_session.expire_all()
    call = (await db_session.execute(select(VoiceCall).where(VoiceCall.id == uuid.UUID(call_id)))).scalar_one()
    assert call.status == "completed" and call.outcome == "qualified" and call.transcript
    metrics = (
        await db_session.execute(select(func.count()).select_from(VoiceCallMetrics).where(VoiceCallMetrics.call_id == uuid.UUID(call_id)))
    ).scalar_one()
    assert metrics == 1


async def test_metrics_count_the_calls(db_session, async_client, deal) -> None:
    before = (await async_client.get("/api/v1/voice/metrics")).json()["total_calls"]
    await _start_call(async_client, deal)

    after = (await async_client.get("/api/v1/voice/metrics"))
    assert after.status_code == 200, after.text
    assert after.json()["total_calls"] == before + 1


async def test_playbook_recommendation_matches_the_business_type_and_the_stage(db_session, async_client, deal) -> None:
    from app.domains.crm.models import Deal
    from app.models.voice_sales import SalesPlaybook

    stage = (await db_session.execute(select(Deal.stage).where(Deal.id == deal))).scalar_one()
    playbook = SalesPlaybook(
        name=f"test-playbook-{uuid.uuid4().hex[:6]}", industry="services", deal_stage=stage.value,
        win_rate=0.42, steps=[{"step": 1, "name": "Opening"}],
    )
    db_session.add(playbook)
    await db_session.commit()

    response = await async_client.get(f"/api/v1/voice/playbooks/recommend/{deal}")

    assert response.status_code == 200, response.text
    assert response.json()["playbook_id"] == str(playbook.id)
    assert response.json()["next_step"] == "Opening"


async def test_playbook_recommendation_is_null_without_a_match(async_client, deal) -> None:
    response = await async_client.get(f"/api/v1/voice/playbooks/recommend/{deal}")

    assert response.status_code == 200, response.text
    assert response.json() is None
