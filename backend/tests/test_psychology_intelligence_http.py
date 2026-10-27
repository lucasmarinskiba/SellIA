"""The buyer intelligence and next-move endpoints, through HTTP and the real database.

What the prospect says is stored by record-response, read back by the intelligence endpoint, and turned
into moves. A move the business cannot back comes back blocked with the missing facts, never invented.
"""

from __future__ import annotations

import uuid

import pytest

NIL_DEAL = "00000000-0000-0000-0000-000000000000"

ANSWERS = (
    "Perdemos $2000 por mes con los errores y estoy frustrado",
    "Soy el dueño, lo decido yo. ¿Cuánto cuesta y cómo empiezo?",
    "Lo necesitamos esta semana",
)


@pytest.fixture
async def deal(db_session, test_user):
    from app.domains.businesses.models import Business
    from app.domains.crm.models import Deal

    business = Business(user_id=test_user.id, name=f"Intel {uuid.uuid4().hex[:6]}")
    db_session.add(business)
    await db_session.flush()
    row = Deal(business_id=business.id, title="Deal inteligencia")
    db_session.add(row)
    await db_session.commit()
    deal_id, business_id = row.id, business.id
    yield deal_id
    from app.models.psychology_sales import DiscoveryResponse, ObjectionHandling

    for model in (DiscoveryResponse, ObjectionHandling):
        await db_session.execute(model.__table__.delete().where(model.deal_id == str(deal_id)))
    await db_session.execute(Deal.__table__.delete().where(Deal.id == deal_id))
    await db_session.execute(Business.__table__.delete().where(Business.id == business_id))
    await db_session.commit()


async def _record(async_client, deal_id, answers) -> None:
    for answer in answers:
        response = await async_client.post(
            "/api/v1/psychology/record-response",
            json={"deal_id": str(deal_id), "question": "¿Qué pasa hoy?", "response": answer},
        )
        assert response.status_code == 200, response.text


async def test_intelligence_of_a_deal_without_answers(async_client, deal) -> None:
    response = await async_client.get(f"/api/v1/psychology/deals/{deal}/intelligence")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["readiness"] == 0
    assert body["driver"] == "discovery"
    assert body["signals"]["answers"] == 0


async def test_intelligence_reads_what_was_recorded(async_client, deal) -> None:
    await _record(async_client, deal, ANSWERS)

    body = (await async_client.get(f"/api/v1/psychology/deals/{deal}/intelligence")).json()

    assert body["signals"]["answers"] == 3
    assert body["signals"]["decision_maker"] is True
    assert "Perdemos $2000 por mes" in body["signals"]["quotes"]["cost"]
    assert body["readiness"] >= 60
    assert body["driver"] == "buying"


async def test_next_moves_without_facts_are_blocked_not_invented(async_client, deal) -> None:
    await _record(async_client, deal, ANSWERS)

    response = await async_client.post(f"/api/v1/psychology/deals/{deal}/next-moves", json={})

    assert response.status_code == 200, response.text
    body = response.json()
    ready = {m["id"]: m for m in body["ready"]}
    blocked = {m["id"]: m for m in body["blocked"]}
    assert "real_scarcity" not in ready
    assert blocked["real_scarcity"]["missing"] == ["capacity_slots", "capacity_reason"]
    assert blocked["real_scarcity"]["line"] is None
    assert "Perdemos $2000 por mes" in ready["cost_of_inaction"]["line"]


async def test_next_moves_offer_scarcity_once_the_business_backs_it(async_client, deal) -> None:
    await _record(async_client, deal, ANSWERS)

    response = await async_client.post(
        f"/api/v1/psychology/deals/{deal}/next-moves",
        json={"evidence": {"capacity_slots": 3, "capacity_reason": "El equipo de implementación tiene 3 lugares este trimestre"}},
    )

    assert response.status_code == 200, response.text
    ready = {m["id"]: m for m in response.json()["ready"]}
    assert "3 lugares" in ready["real_scarcity"]["line"]


async def test_urgency_triggers_without_evidence_are_empty(async_client) -> None:
    """The old endpoint answered with invented deadlines and customer counts. Now it answers with nothing."""
    response = await async_client.post(
        "/api/v1/psychology/urgency-triggers",
        json={"deal_id": NIL_DEAL, "stage": "negotiation", "industry": "retail"},
    )

    assert response.status_code == 200, response.text
    assert response.json()["triggers"] == []


async def test_unknown_deal_is_404_for_the_new_endpoints(async_client) -> None:
    intelligence = await async_client.get(f"/api/v1/psychology/deals/{NIL_DEAL}/intelligence")
    moves = await async_client.post(f"/api/v1/psychology/deals/{NIL_DEAL}/next-moves", json={})

    assert intelligence.status_code == 404, intelligence.text
    assert moves.status_code == 404, moves.text


async def test_malformed_deal_id_is_422(async_client) -> None:
    response = await async_client.get("/api/v1/psychology/deals/no-es-un-uuid/intelligence")

    assert response.status_code == 422, response.text


async def test_automation_answers_a_silent_prospect_with_his_own_words(async_client, deal) -> None:
    await _record(async_client, deal, ANSWERS)

    response = await async_client.post(
        f"/api/v1/psychology/deals/{deal}/automation", json={"event": "silent_3_days"}
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["drafts_need_approval"] is True
    ready = {d["id"]: d for d in body["ready"]}
    assert 'Me dijiste: "Perdemos $2000 por mes' in ready["remind_their_pain"]["text"]


async def test_automation_refuses_an_unknown_event(async_client, deal) -> None:
    response = await async_client.post(
        f"/api/v1/psychology/deals/{deal}/automation", json={"event": "se_enamoro"}
    )

    assert response.status_code == 422, response.text


async def test_automation_catalog_lists_the_four_goals(async_client) -> None:
    response = await async_client.get("/api/v1/psychology/automation/catalog")

    assert response.status_code == 200, response.text
    assert set(response.json()["goals"]) == {"attract", "trust", "close", "retain"}


async def test_evidence_values_are_validated(async_client, deal) -> None:
    """A capacity of zero is not a capacity: the request is refused rather than offering scarcity."""
    response = await async_client.post(
        f"/api/v1/psychology/deals/{deal}/next-moves",
        json={"evidence": {"capacity_slots": 0}},
    )

    assert response.status_code == 422, response.text
