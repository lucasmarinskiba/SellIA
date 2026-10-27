"""Psychology automations: each event gets a response built from the prospect's own words and the business's real facts.

No database: these are the rules. The HTTP side is in test_psychology_intelligence_http.py.
"""

import pytest

from app.domains.enterprise import psychology_automations as pa
from app.domains.enterprise import psychology_intelligence as pi


def profile_for(*answers: str) -> pi.BuyerProfile:
    return pi.build_profile(pi.extract_signals(list(answers)), 0)


PAIN_AND_COST = profile_for("Perdemos $2000 por mes con los errores y estoy frustrado")


def test_a_silent_prospect_is_reminded_of_his_own_words() -> None:
    plan = pa.plan_automation("silent_3_days", PAIN_AND_COST, {})
    ready = {d.id: d for d in plan.ready}

    assert 'Me dijiste: "Perdemos $2000 por mes' in ready["remind_their_pain"].text
    assert "ask_for_a_decision" in ready


def test_a_rule_quoting_words_the_prospect_never_said_does_not_apply() -> None:
    plan = pa.plan_automation("silent_3_days", profile_for("Hola, gracias por escribir"), {})

    ids = {d.id for d in plan.ready + plan.blocked}
    assert "remind_their_pain" not in ids
    assert "ask_for_a_decision" in ids  # needs no quote, so it still applies


def test_a_price_objection_is_answered_with_the_business_price_or_not_at_all() -> None:
    blocked = {d.id: d for d in pa.plan_automation("objection_price", PAIN_AND_COST, {}).blocked}
    assert blocked["price_against_their_cost"].missing == ("price_summary",)

    ready = {d.id: d for d in pa.plan_automation("objection_price", PAIN_AND_COST, {"price_summary": "US$ 300 al mes"}).ready}
    assert "Perdemos $2000 por mes" in ready["price_against_their_cost"].text
    assert "US$ 300 al mes" in ready["price_against_their_cost"].text


def test_a_guarantee_is_never_offered_without_one() -> None:
    plan = pa.plan_automation("objection_price", PAIN_AND_COST, {})

    assert "risk_reversal" in {d.id for d in plan.blocked}
    assert "risk_reversal" not in {d.id for d in plan.ready}


def test_a_real_deadline_needs_the_real_change_behind_it() -> None:
    plan = pa.plan_automation("proposal_sent", PAIN_AND_COST, {})

    blocked = {d.id: d for d in plan.blocked}
    assert blocked["real_deadline"].missing == ("price_change_date", "price_change_detail")
    assert "small_yes_after_proposal" in {d.id for d in plan.ready}


def test_a_won_deal_gets_a_review_and_a_referral_ask_with_no_facts_needed() -> None:
    plan = pa.plan_automation("deal_won", PAIN_AND_COST, {})

    ids = {d.id for d in plan.ready}
    assert {"ask_for_review", "referral_ask", "their_goal_after_sale"} <= ids


def test_an_inactive_customer_is_reactivated_with_his_own_pain() -> None:
    plan = pa.plan_automation("inactive_30_days", PAIN_AND_COST, {})

    ready = {d.id: d for d in plan.ready}
    assert 'Hace un mes me dijiste: "Perdemos $2000 por mes' in ready["reactivate_with_their_pain"].text


@pytest.mark.parametrize("rule", pa.RULES, ids=lambda r: r.id)
def test_every_rule_renders_with_every_quote_and_fact(rule: pa.Rule) -> None:
    values = {f"{name}_quote": f"texto de {name}" for name in ("pain", "cost", "timeline", "status_quo", "approval", "buying", "price")}
    values.update({field: f"valor de {field}" for field in pi.EVIDENCE_FIELDS})

    assert rule.text.format_map(values)


def test_every_rule_belongs_to_a_known_event_and_goal() -> None:
    assert {r.event for r in pa.RULES} <= set(pa.EVENTS)
    assert {r.goal for r in pa.RULES} <= set(pa.GOALS)
