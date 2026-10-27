"""The psychology sales endpoints must work and must persist what they say they saved.

Before this change the routes used the synchronous ``db.query`` API on the async session (every
discovery-questions call returned 400), and the engines called ``commit()`` without awaiting it, so
``record-response`` answered ``{"recorded": true}`` and wrote nothing. These tests go through the HTTP
routes and count the rows in the database, which is the part that was silently lost.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select

NIL_DEAL = "00000000-0000-0000-0000-000000000000"


@pytest.fixture
async def deal(db_session, test_user):
    from app.domains.businesses.models import Business
    from app.domains.crm.models import Deal

    business = Business(user_id=test_user.id, name=f"Psy {uuid.uuid4().hex[:6]}")
    db_session.add(business)
    await db_session.flush()
    row = Deal(business_id=business.id, title="Deal psicología")
    db_session.add(row)
    await db_session.commit()
    deal_id, business_id = row.id, business.id
    yield deal_id
    from app.models.psychology_sales import (
        CloseAttempt,
        DiscoveryResponse,
        NeedNarrative,
        ObjectionHandling,
        SalesConversation,
    )

    for model in (DiscoveryResponse, NeedNarrative, ObjectionHandling, CloseAttempt, SalesConversation):
        await db_session.execute(model.__table__.delete().where(model.deal_id == str(deal_id)))
    await db_session.execute(Deal.__table__.delete().where(Deal.id == deal_id))
    await db_session.execute(Business.__table__.delete().where(Business.id == business_id))
    await db_session.commit()


async def _count(db, model, deal_id) -> int:
    db.expire_all()
    return (await db.execute(select(func.count()).select_from(model.__table__).where(model.deal_id == str(deal_id)))).scalar_one()


async def test_record_response_is_saved_not_just_acknowledged(db_session, async_client, deal) -> None:
    from app.models.psychology_sales import DiscoveryResponse

    response = await async_client.post(
        "/api/v1/psychology/record-response",
        json={"deal_id": str(deal), "question": "¿Cuál es su mayor dolor?", "response": "Pierde 20 horas por semana, está frustrado"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["recorded"] is True
    assert await _count(db_session, DiscoveryResponse, deal) == 1  # the row is really there
    assert response.json()["pain_points"]                           # "frustrado"/"pierde" -> a pain point


async def test_create_need_narrative_is_saved(db_session, async_client, deal) -> None:
    from app.models.psychology_sales import NeedNarrative

    response = await async_client.post(
        "/api/v1/psychology/create-need-narrative",
        json={"deal_id": str(deal), "discovery_responses": ["Perdemos ventas por no responder a tiempo"]},
    )

    assert response.status_code == 200, response.text
    assert response.json()["narrative"]
    assert await _count(db_session, NeedNarrative, deal) == 1


async def test_discovery_questions_work_for_an_existing_deal(async_client, deal) -> None:
    """This route used ``db.query`` on the async session: it failed for every deal."""
    response = await async_client.post(
        "/api/v1/psychology/discovery-questions",
        json={"deal_id": str(deal), "prospect_id": "p-1", "stage": "rapport"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["questions"]


async def test_unknown_deal_is_a_404_and_writes_nothing(db_session, async_client) -> None:
    from app.models.psychology_sales import DiscoveryResponse

    response = await async_client.post(
        "/api/v1/psychology/record-response",
        json={"deal_id": NIL_DEAL, "question": "q", "response": "r"},
    )

    assert response.status_code == 404, response.text   # previously a 400 whose text read "404: Deal not found"
    assert await _count(db_session, DiscoveryResponse, NIL_DEAL) == 0


async def test_malformed_deal_id_is_a_422(async_client) -> None:
    response = await async_client.post(
        "/api/v1/psychology/discovery-questions",
        json={"deal_id": "no-es-un-uuid", "prospect_id": "p-1", "stage": "rapport"},
    )

    assert response.status_code == 422, response.text


@pytest.mark.parametrize(
    ("path", "body"),
    [
        ("/api/v1/psychology/handle-objection", {"deal_id": NIL_DEAL, "objection": "Es muy caro", "prospect_role": "decision_maker"}),
        ("/api/v1/psychology/urgency-triggers", {"deal_id": NIL_DEAL, "stage": "negotiation", "industry": "retail"}),
        ("/api/v1/psychology/close", {"deal_id": NIL_DEAL, "current_step": 1, "prospect_response": "yes, let's do it"}),
    ],
)
async def test_the_engines_that_do_not_store_still_answer(async_client, path: str, body: dict) -> None:
    response = await async_client.post(path, json=body)

    assert response.status_code == 200, response.text
