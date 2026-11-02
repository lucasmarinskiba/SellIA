"""Phase 31 psychology sales: the five engines on the real database.

Rewritten from the version quarantined in known_failures.txt. That one defined its own `db` fixture
against a wrong import path and called drop_all on the engine of the suite, and it asserted urgency
triggers with invented facts ("Pricing increases March 1st"). These tests cover each engine's behaviour
as it is now, and check that no number or claim is made up when the data is not there.

The HTTP routes are covered in test_psychology_persistence.py and test_psychology_intelligence_http.py.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import func, select

from app.domains.enterprise.psychology_sales import (
    AssumptiveCloseEngine,
    DiscoveryQuestionsEngine,
    NeedCreationEngine,
    PsychologyObjectionHandler,
    UrgencyTriggerEngine,
)

NIL_UUID = "00000000-0000-0000-0000-000000000000"


@pytest.fixture
async def deal(db_session, test_user):
    from app.domains.businesses.models import Business
    from app.domains.crm.models import Deal
    from app.models.psychology_sales import DiscoveryResponse, NeedNarrative

    business = Business(user_id=test_user.id, name=f"Psy31 {uuid.uuid4().hex[:6]}")
    db_session.add(business)
    await db_session.flush()
    row = Deal(business_id=business.id, title="Deal psicología 31")
    db_session.add(row)
    await db_session.commit()
    deal_id, business_id = row.id, business.id
    yield deal_id
    for model in (DiscoveryResponse, NeedNarrative):
        await db_session.execute(model.__table__.delete().where(model.deal_id == str(deal_id)))
    await db_session.execute(Deal.__table__.delete().where(Deal.id == deal_id))
    await db_session.execute(Business.__table__.delete().where(Business.id == business_id))
    await db_session.commit()


async def _count(db, model, deal_id) -> int:
    db.expire_all()
    return (await db.execute(select(func.count()).select_from(model).where(model.deal_id == str(deal_id)))).scalar_one()


# ── DiscoveryQuestionsEngine ───────────────────────────────────────────────


def test_discovery_questions_follow_the_stage() -> None:
    engine = DiscoveryQuestionsEngine(db=None)

    questions = engine.generate_questions({"company_name": "TechCorp"}, "discovery")

    assert questions and all(q.category == "problem" for q in questions)
    assert all(q.psychology for q in questions)


def test_the_company_name_is_filled_in_not_left_as_a_placeholder() -> None:
    engine = DiscoveryQuestionsEngine(db=None)

    questions = engine.generate_questions({"company_name": "TechCorp"}, "initial_contact")

    assert any("TechCorp" in q.question for q in questions)
    assert all("{company_name}" not in q.question for q in questions)


async def test_a_discovery_answer_is_stored_with_its_pain(db_session, deal) -> None:
    engine = DiscoveryQuestionsEngine(db_session)

    row = await engine.record_response(str(deal), "¿Dónde pierden tiempo?", "Perdemos 20 horas por semana, es urgente")

    assert row.pain_points == ["Perdemos 20 horas por semana, es urgente"]
    assert row.urgency_level == 8  # "urgente" is a timing signal
    assert await _count(db_session, _discovery_model(), deal) == 1


def _discovery_model():
    from app.models.psychology_sales import DiscoveryResponse

    return DiscoveryResponse


# ── NeedCreationEngine ─────────────────────────────────────────────────────


async def test_the_cost_in_the_narrative_is_the_one_the_prospect_named(db_session, deal) -> None:
    engine = NeedCreationEngine(db_session)

    result = await engine.create_need_narrative(str(deal), ["Perdemos $2000 por mes con los errores"])

    assert result.financial_impact == 24000.0  # $2000 a month, annualised
    assert "24,000" in result.narrative
    assert await _count(db_session, _need_model(), deal) == 1


async def test_no_cost_named_means_no_cost_claimed(db_session, deal) -> None:
    """The old engine invented a $50,000 minimum. With no figure from the prospect there is none."""
    engine = NeedCreationEngine(db_session)

    result = await engine.create_need_narrative(str(deal), ["Estamos muy mal con los reclamos"])

    assert result.financial_impact == 0.0
    assert "50,000" not in result.narrative and "$" not in result.narrative


def _need_model():
    from app.models.psychology_sales import NeedNarrative

    return NeedNarrative


# ── PsychologyObjectionHandler ─────────────────────────────────────────────


@pytest.mark.parametrize(
    ("objection", "expected_type"),
    [
        ("Es muy caro para nosotros", "price"),
        ("No tengo tiempo para implementarlo", "time"),
        ("Tengo que consultarlo con mi socio", "authority"),
        ("No lo necesito por ahora", "need"),
    ],
)
def test_objections_are_classified_in_spanish(objection: str, expected_type: str) -> None:
    assert PsychologyObjectionHandler(db=None)._classify_objection(objection) == expected_type


def test_a_price_objection_gets_the_price_framework_in_spanish() -> None:
    reply = PsychologyObjectionHandler(db=None).handle_objection("Es muy caro", {"role": "decision_maker"})

    assert reply == "Entiendo que el presupuesto importa. ¿Cuánto les cuesta hoy no resolverlo?"


# ── UrgencyTriggerEngine ───────────────────────────────────────────────────


def test_no_urgency_without_facts_from_the_business() -> None:
    assert UrgencyTriggerEngine(db=None).generate_urgency_triggers({}) == []


def test_scarcity_appears_only_with_real_capacity() -> None:
    triggers = UrgencyTriggerEngine(db=None).generate_urgency_triggers(
        {"capacity_slots": 2, "capacity_reason": "Un solo consultor disponible"}
    )

    assert [t["type"] for t in triggers] == ["real_scarcity"]
    assert "2 lugares" in triggers[0]["messaging"]


# ── AssumptiveCloseEngine ──────────────────────────────────────────────────


def test_the_close_sequence_moves_one_step_per_yes() -> None:
    engine = AssumptiveCloseEngine(db=None)

    assert engine.get_close(0) == AssumptiveCloseEngine.CLOSE_SEQUENCE[0]["commitment"]
    assert engine.get_close(4) == AssumptiveCloseEngine.CLOSE_SEQUENCE[4]["commitment"]
    assert engine.get_close(99) == "¿Entonces estás listo para avanzar?"


@pytest.mark.parametrize(("reply", "expected"), [("sí, dale", True), ("Perfecto, avancemos", True), ("no, todavía no", False), ("¿cuánto cuesta?", False)])
def test_yes_and_no_are_read_in_spanish(reply: str, expected: bool) -> None:
    assert AssumptiveCloseEngine(db=None)._is_positive_response(reply) is expected


def test_a_no_stays_on_the_step_and_a_yes_advances() -> None:
    engine = AssumptiveCloseEngine(db=None)

    assert engine.get_next_close("no, todavía no")[0] == "objection"
    assert engine.get_next_close("sí")[0] == "advance"


# ── The whole flow ─────────────────────────────────────────────────────────


async def test_discovery_to_close_is_stored_step_by_step(db_session, deal) -> None:
    """Discovery answers, a need narrative from them, then a yes to the first close: each step leaves its record."""
    discovery = DiscoveryQuestionsEngine(db_session)
    need = NeedCreationEngine(db_session)
    close = AssumptiveCloseEngine(db_session)

    answers = ["Perdemos $2000 por mes con los errores", "Estoy frustrado con el proceso"]
    for answer in answers:
        await discovery.record_response(str(deal), "¿Qué pasa hoy?", answer)
    narrative = await need.create_need_narrative(str(deal), answers)
    outcome, step = close.get_next_close("sí, agendemos")

    assert await _count(db_session, _discovery_model(), deal) == 2
    assert await _count(db_session, _need_model(), deal) == 1
    assert narrative.financial_impact == 24000.0
    assert outcome == "advance" and step == AssumptiveCloseEngine.CLOSE_SEQUENCE
