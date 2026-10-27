"""Psychology automations: an event about a prospect or customer in, the psychological response out.

Four goals: attract (captar), trust (confianza), close (cerrar), retain (fidelizar). Each rule maps one
business event to one response. A rule needs the prospect's own words when it quotes them, and the
business's facts when it claims something (a guarantee, a real customer, a real deadline). Without
them the rule is reported as blocked with the missing facts; it is never filled with an invented claim.

The output is a draft. Sending it to a customer is a separate step that needs the owner's approval.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from app.domains.enterprise.psychology_intelligence import BuyerProfile, known_facts

GOALS = {
    "attract": "Captar",
    "trust": "Generar confianza",
    "close": "Cerrar",
    "retain": "Fidelizar",
}

EVENTS = {
    "first_contact": "Primer contacto del prospecto",
    "new_lead": "Lead nuevo",
    "silent_3_days": "Tres días sin respuesta",
    "objection_price": "Objeción de precio",
    "objection_time": "Objeción de tiempo",
    "proposal_sent": "Propuesta enviada",
    "deal_won": "Cliente nuevo (venta cerrada)",
    "inactive_30_days": "Cliente sin actividad hace 30 días",
}


@dataclass(frozen=True)
class Rule:
    id: str
    event: str
    goal: str
    principle: str
    text: str  # Spanish; placeholders are the prospect's quotes ({pain_quote}) or business facts
    needs_quote: Optional[str] = None  # a signal the prospect must have given
    needs_facts: Tuple[str, ...] = ()  # facts the business must have given


RULES: Tuple[Rule, ...] = (
    Rule(
        id="free_value_first",
        event="new_lead",
        goal="attract",
        principle="Reciprocidad: dar valor primero genera ganas de devolverlo",
        text="Antes de decidir nada, te mando sin costo {free_offer}. ¿Qué te gustaría que mire primero?",
        needs_facts=("free_offer",),
    ),
    Rule(
        id="ask_their_goal",
        event="first_contact",
        goal="attract",
        principle="Curiosidad: una pregunta abierta hace que hable él",
        text="¿Qué te gustaría resolver en los próximos 90 días?",
    ),
    Rule(
        id="proof_from_their_peers",
        event="new_lead",
        goal="trust",
        principle="Prueba social verificable (Cialdini)",
        text="Hoy trabajamos con {customers_same_industry} empresas de tu rubro. {case_result}.",
        needs_facts=("customers_same_industry", "case_result"),
    ),
    Rule(
        id="admit_limits",
        event="first_contact",
        goal="trust",
        principle="Admitir límites: la honestidad genera confianza",
        text="Si en la llamada vemos que no te conviene, te lo digo y no seguimos. Lo cumplimos.",
    ),
    Rule(
        id="remind_their_pain",
        event="silent_3_days",
        goal="close",
        principle="Consistencia: recordarle lo que él mismo dijo",
        text='Me dijiste: "{pain_quote}". ¿Sigue siendo prioridad, o cambió algo?',
        needs_quote="pain",
    ),
    Rule(
        id="ask_for_a_decision",
        event="silent_3_days",
        goal="close",
        principle="Pedir una decisión explícita: el silencio se vuelve un sí o un no",
        text="¿Seguimos con lo que hablamos, o prefieres que lo dejemos para más adelante?",
    ),
    Rule(
        id="price_against_their_cost",
        event="objection_price",
        goal="close",
        principle="Encuadre: comparar la inversión con el costo que él describió (anclaje)",
        text='Me dijiste que el problema les cuesta: "{cost_quote}". Frente a eso, la inversión es {price_summary}.',
        needs_quote="cost",
        needs_facts=("price_summary",),
    ),
    Rule(
        id="risk_reversal",
        event="objection_price",
        goal="close",
        principle="Reversión del riesgo: quitar el riesgo de la decisión (aversión a la pérdida)",
        text="{guarantee}. Así decides con resultados a la vista, no con promesas.",
        needs_facts=("guarantee",),
    ),
    Rule(
        id="time_reframe",
        event="objection_time",
        goal="close",
        principle="Reencuadre: pensar cuánto tiempo devuelve, no solo cuánto pide",
        text="Tiene sentido. ¿Cuánto vale una hora de tu tiempo hoy? Te propongo una llamada de 15 minutos, nada más.",
    ),
    Rule(
        id="small_yes_after_proposal",
        event="proposal_sent",
        goal="close",
        principle="Compromiso pequeño antes del cierre (Belfort)",
        text="¿Te parece si agendamos 30 minutos con quien decide para revisar la propuesta?",
    ),
    Rule(
        id="real_deadline",
        event="proposal_sent",
        goal="close",
        principle="Fecha límite real: un cambio que va a ocurrir (Cialdini)",
        text="Desde el {price_change_date}, {price_change_detail}. Si arrancas antes, mantienes las condiciones actuales.",
        needs_facts=("price_change_date", "price_change_detail"),
    ),
    Rule(
        id="their_goal_after_sale",
        event="deal_won",
        goal="retain",
        principle="Compromiso y coherencia: recordarle su propio objetivo",
        text='Al inicio me dijiste: "{pain_quote}". ¿Cómo está eso hoy?',
        needs_quote="pain",
    ),
    Rule(
        id="ask_for_review",
        event="deal_won",
        goal="trust",
        principle="Prueba social generada por el propio cliente, solo si la quiere dar",
        text="¿Cómo te fue estas semanas? Si te sirvió, ¿nos cuentas qué cambió en tu día a día?",
    ),
    Rule(
        id="referral_ask",
        event="deal_won",
        goal="retain",
        principle="Reciprocidad: el cliente devuelve el favor",
        text="Si te sirvió, ¿a quién de tu red le vendría bien lo mismo? Con gusto le escribo yo.",
    ),
    Rule(
        id="reactivate_with_their_pain",
        event="inactive_30_days",
        goal="retain",
        principle="Reactivar con su propio dolor, no con una promoción",
        text='Hace un mes me dijiste: "{pain_quote}". ¿Cambió algo, o sigue igual?',
        needs_quote="pain",
    ),
)


@dataclass(frozen=True)
class Draft:
    id: str
    goal: str
    principle: str
    text: Optional[str]  # None while blocked
    missing: Tuple[str, ...]


@dataclass(frozen=True)
class AutomationPlan:
    event: str
    ready: List[Draft]
    blocked: List[Draft]


def plan_automation(event: str, profile: BuyerProfile, facts: dict) -> AutomationPlan:
    """Responses for one event. Rules that need a quote the prospect never gave do not apply at all."""
    known = known_facts(facts)
    quotes = {f"{name}_quote": text for name, text in profile.signals.quotes.items()}
    ready: List[Draft] = []
    blocked: List[Draft] = []
    for rule in RULES:
        if rule.event != event:
            continue
        if rule.needs_quote and rule.needs_quote not in profile.signals.quotes:
            continue
        missing = tuple(f for f in rule.needs_facts if f not in known)
        if missing:
            blocked.append(Draft(rule.id, rule.goal, rule.principle, None, missing))
        else:
            ready.append(Draft(rule.id, rule.goal, rule.principle, rule.text.format_map({**quotes, **known}), ()))
    return AutomationPlan(event=event, ready=ready, blocked=blocked)

