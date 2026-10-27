"""Sales intelligence rules: what the prospect said becomes readiness, a lever, and only the moves the business can back.

No database here: these are the rules. The HTTP side is in test_psychology_intelligence_http.py.
"""

import pytest

from app.domains.enterprise import psychology_intelligence as pi


def profile_for(*answers: str, open_objections: int = 0) -> pi.BuyerProfile:
    return pi.build_profile(pi.extract_signals(list(answers)), open_objections)


# Ready to buy: pain + cost + "soy el dueño" + a buying question. Readiness 55, driver "buying".
BUYING_ANSWERS = (
    "Perdemos $2000 por mes con los errores y estoy frustrado",
    "Soy el dueño, lo decido yo. ¿Cuánto cuesta y cómo empiezo?",
)


def test_money_is_annualised_only_when_the_prospect_names_a_period() -> None:
    assert pi.annual_amounts("Perdemos $2000 por mes") == [24000.0]
    assert pi.annual_amounts("Perdemos $500 por venta") == []  # no period: nothing is guessed
    assert pi.annual_amounts("Perdemos 20 horas por semana") == []  # hours are not money


def test_spanish_number_formats_and_scales() -> None:
    assert pi.annual_amounts("Nos cuesta 1.500 dólares al mes") == [18000.0]
    assert pi.annual_amounts("Nos cuesta $20 mil al año") == [20000.0]
    assert pi.annual_amounts("Nos cuesta 500,50 usd al año") == [500.5]


def test_pain_cost_and_buying_are_read_in_spanish() -> None:
    signals = pi.extract_signals(["Pierde 20 horas por semana, está frustrado", "¿Cuánto cuesta y cómo empiezo?"])

    assert {"pain", "cost", "buying"} <= set(signals.quotes)
    assert signals.pain_answers == 1


def test_no_invented_amount_when_none_was_named() -> None:
    # The old narrative silently used a $50,000 minimum. Nothing named, nothing claimed.
    assert pi.extract_signals(["Estamos muy mal con los reclamos"]).annual_cost == 0.0


def test_readiness_and_driver_for_a_buyer() -> None:
    profile = profile_for(*BUYING_ANSWERS)

    assert profile.readiness == 55  # pain 10 + cost 15 + decision maker 10 + buying 20
    assert profile.driver == "buying"


def test_an_approver_who_is_not_the_decider_drives_the_internal_seller() -> None:
    profile = profile_for("Tengo que consultarlo con mi socio")

    assert profile.driver == "approval"


def test_a_decider_is_not_treated_as_needing_approval() -> None:
    profile = profile_for("Lo decido yo, pero lo tengo que consultar con mi socio")

    assert profile.signals.decision_maker is True
    assert profile.driver != "approval"


def test_long_quotes_are_trimmed_not_cut_mid_word() -> None:
    long_answer = "Perdemos mucho tiempo " + "con los reportes manuales que hacemos cada semana " * 6
    quote = pi.extract_signals([long_answer]).quotes["pain"]

    assert len(quote) <= pi.QUOTE_LIMIT + 1
    assert quote.endswith("…")


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Es muy caro para nosotros", "price"),
        ("No tengo tiempo para implementarlo ahora", "time"),
        ("Tengo que consultarlo con mi socio", "authority"),
        ("No lo necesito por ahora", "need"),
    ],
)
def test_objections_are_classified_in_spanish(text: str, expected: str) -> None:
    assert pi.classify_objection(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [("sí, dale", True), ("Perfecto, avancemos", True), ("no, todavía no", False), ("¿cuánto cuesta?", False)],
)
def test_close_replies_are_read_in_spanish(text: str, expected: bool) -> None:
    assert pi.is_positive_reply(text) is expected


def test_scarcity_and_deadlines_stay_blocked_without_business_facts() -> None:
    profile = profile_for(*BUYING_ANSWERS, "Lo necesitamos esta semana")  # adds timeline: readiness 65

    plan = pi.plan_moves(profile, {})
    ready_ids = {m.id for m in plan.ready}
    blocked = {m.id: m for m in plan.blocked}

    assert "real_scarcity" not in ready_ids
    assert "real_deadline" not in ready_ids
    assert blocked["real_scarcity"].missing == ("capacity_slots", "capacity_reason")
    assert blocked["real_scarcity"].line is None


def test_scarcity_is_offered_only_with_the_real_capacity_behind_it() -> None:
    profile = profile_for(*BUYING_ANSWERS, "Lo necesitamos esta semana")

    plan = pi.plan_moves(
        profile,
        {"capacity_slots": 3, "capacity_reason": "El equipo de implementación tiene 3 lugares este trimestre"},
    )
    scarcity = next(m for m in plan.ready if m.id == "real_scarcity")

    assert "3 lugares" in scarcity.line
    assert scarcity.missing == ()


def test_loss_framing_quotes_the_prospect_and_nothing_else() -> None:
    profile = profile_for(*BUYING_ANSWERS, "Lo necesitamos esta semana")

    plan = pi.plan_moves(profile, {})
    cost_move = next(m for m in plan.ready if m.id == "cost_of_inaction")

    assert "Perdemos $2000 por mes" in cost_move.line


def test_urgency_lines_need_real_facts() -> None:
    assert pi.urgency_triggers({}) == []

    triggers = pi.urgency_triggers({"capacity_slots": 2, "capacity_reason": "Un solo consultor disponible"})

    assert [t["type"] for t in triggers] == ["real_scarcity"]
    assert triggers[0]["based_on"] == {"capacity_slots": 2, "capacity_reason": "Un solo consultor disponible"}


def test_every_tactic_renders_with_every_quote_and_fact() -> None:
    quotes = {name: f"texto de {name}" for name in ("pain", "cost", "timeline", "status_quo", "approval", "buying", "price")}
    values = {f"{name}_quote": text for name, text in quotes.items()}
    values.update({field: f"valor de {field}" for field in pi.EVIDENCE_FIELDS})
    values.update({"customers_same_industry": 4, "capacity_slots": 2})

    for tactic in pi.TACTICS:
        assert pi._render(tactic, values)  # a placeholder with no value would raise KeyError here
