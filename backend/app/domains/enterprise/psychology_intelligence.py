"""Sales intelligence for the psychology module: buyer readiness, persuasion moves and FOMO.

It reads what the prospect said in discovery and what the business can prove, then says which move
fits next. Loss framing quotes the prospect's own words and numbers. Scarcity, deadlines, customer
proof and guarantees are offered only when the business supplies the fact behind them: a move that
needs a fact nobody gave comes back as "blocked", never filled with an invented claim.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.psychology_sales import DiscoveryResponse, ObjectionHandling


def _pattern(source: str) -> "re.Pattern[str]":
    return re.compile(source, re.IGNORECASE)


# Spanish first (the buyers write Spanish), English kept for the mixed-language answers.
PAIN_RX = _pattern(
    r"\b(?:pierd\w*|perd(?:emos|er|ió|ía|ida|idas|idos|iendo)|frustr\w*|problem\w*|dolor\w*"
    r"|complic\w*|quej\w*|reclam\w*|estr[eé]s\w*|agot\w*|no funcion\w*|se rompe\w*"
    r"|losing|wasting|frustrat\w*|struggl\w*|broken|pain)\b"
)
# Money with a currency the prospect named (pesos are left out: they are not comparable to dollars).
AMOUNT_RX = _pattern(
    r"(?:(?:\$|u\$s|usd)\s?(\d[\d.,]*)(?:\s?(mil|millones))?"
    r"|(\d[\d.,]*)\s?(?:(mil|millones)\s?)?(?:usd|d[oó]lares|€))"
)
COST_RX = _pattern(r"\$|\busd\b|€|\bd[oó]lares\b|\b\d+(?:[.,]\d+)?\s?(?:horas?|hs)\b")
TIMELINE_RX = _pattern(
    r"\b(?:urgent\w*|asap|inmediat\w*|cuanto antes|ya mismo|esta semana|este mes|este trimestre"
    r"|la semana que viene|fin de (?:mes|a[ñn]o|trimestre)|para el \d{1,2})\b"
)
STATUS_QUO_RX = _pattern(
    r"\b(?:usamos|probamos|intentamos|excel|planillas?|a mano|manual(?:mente)?|lo hacemos"
    r"|hacemos (?:todo )?(?:a mano|manual\w*)|ya (?:tenemos|tengo|usamos|probamos|intentamos)"
    r"|tenemos un\w*)\b"
)
APPROVAL_RX = _pattern(
    r"\b(?:mi (?:jefe|jefa|socio|socia|director(?:a)?|gerente|esposo|esposa|directorio)|mis socios"
    r"|el directorio|tengo que consultar|hay que consultar|consultarlo con"
    r"|lo (?:decide|aprueba|aprueban) (?:otra persona|alguien|el directorio|mi jefe|mis socios)"
    r"|aprobaci[oó]n|la junta|comit[eé]|lo tiene que aprobar|me lo tienen que aprobar)\b"
)
DECISION_RX = _pattern(
    r"\b(?:lo decido yo|decido yo|yo decido|yo lo apruebo|soy (?:el |la )?(?:due[ñn]o|due[ñn]a"
    r"|gerente|director(?:a)?|socio|socia|fundador(?:a)?|ceo)|la decisi[oó]n es m[ií]a)\b"
)
BUYING_RX = _pattern(
    r"\b(?:cu[aá]nto (?:cuesta|sale|val[ea])|c[oó]mo (?:empiezo|arrancamos|seguimos|es el proceso)"
    r"|cu[aá]ndo (?:podemos|arrancamos|empezamos)|arrancar|empezar|contratar"
    r"|quiero (?:probar|contratar|empezar)|firmar|facturar|c[oó]mo (?:pago|se paga))\b"
)
PRICE_RX = _pattern(r"\b(?:caro|cara|es mucho|no tengo (?:la )?plata|no me alcanza|presupuesto|precio alto|descuento)\b")
TIME_RX = _pattern(
    r"\b(?:no tengo tiempo|sin tiempo|ocupad[oa]s?|implementar|implementaci[oó]n|m[aá]s adelante|ahora no)\b"
)
POSITIVE_RX = _pattern(
    r"\b(?:s[ií]|claro|dale|ok|okey|perfecto|de acuerdo|avancemos|hag[aá]mos ?lo|listo|me sirve"
    r"|suena bien|sounds good|yes|sure|let'?s)\b"
)
NEGATIVE_START_RX = _pattern(r"^\s*no\b")

_SCALE = {"mil": 1_000, "millones": 1_000_000}
_PERIODS = (
    (_pattern(r"\b(?:al mes|por mes|mensual\w*)\b"), 12),
    (_pattern(r"\b(?:por semana|a la semana|semanal\w*)\b"), 52),
    (_pattern(r"\b(?:al a[ñn]o|por a[ñn]o|anual\w*)\b"), 1),
)
_SIGNALS = (
    ("pain", PAIN_RX),
    ("cost", COST_RX),
    ("timeline", TIMELINE_RX),
    ("status_quo", STATUS_QUO_RX),
    ("approval", APPROVAL_RX),
    ("buying", BUYING_RX),
    ("price", PRICE_RX),
)
QUOTE_LIMIT = 140

DRIVER_LABELS = {
    "buying": "Ya preguntó por precio o por cómo empezar: cerrar con compromisos pequeños.",
    "approval": "Necesita que otra persona apruebe: darle argumentos para venderlo internamente.",
    "price": "Tiene objeción de precio: encuadrar contra el costo que ya describió.",
    "cost": "Ya cuantificó lo que le cuesta el problema: usar sus propios números.",
    "status_quo": "Describió cómo lo resuelve hoy: mostrar que esa forma de trabajar tiene costo.",
    "pain": "Habló del dolor sin cuantificarlo: preguntarle cuánto le cuesta.",
    "discovery": "Todavía no dio suficiente información: seguir preguntando.",
}

EVIDENCE_FIELDS = (
    "customers_same_industry",
    "case_result",
    "capacity_slots",
    "capacity_reason",
    "price_change_date",
    "price_change_detail",
    "guarantee",
    "free_offer",
    "price_summary",
)


def _quote(text: str) -> str:
    clean = " ".join(text.split())
    if len(clean) <= QUOTE_LIMIT:
        return clean
    return clean[:QUOTE_LIMIT].rsplit(" ", 1)[0] + "…"


def _parse_number(raw: str) -> float:
    """'1.500' and '1,500' are one thousand five hundred; '500,50' is five hundred and a half."""
    return float(re.sub(r"[.,](?=\d{3}(?!\d))", "", raw).replace(",", "."))


def annual_amounts(text: str) -> List[float]:
    """Money the prospect named with a period, annualised. No period means no amount: nothing is guessed."""
    period = next((months for rx, months in _PERIODS if rx.search(text)), None)
    if period is None:
        return []
    amounts = []
    for match in AMOUNT_RX.finditer(text):
        raw = match.group(1) or match.group(3)
        scale = (match.group(2) or match.group(4) or "").lower()
        try:
            value = _parse_number(raw) * _SCALE.get(scale, 1)
        except ValueError:
            continue
        amounts.append(value * period)
    return amounts


@dataclass(frozen=True)
class ProspectSignals:
    answers: int
    avg_words: float
    # First answer that shows each signal, trimmed: pain, cost, timeline, status_quo, approval, buying, price.
    quotes: Dict[str, str]
    pain_answers: int
    decision_maker: bool
    # Biggest yearly cost the prospect named in one answer. 0.0 when none could be annualised.
    annual_cost: float


def extract_signals(answers: Sequence[str]) -> ProspectSignals:
    texts = [" ".join(a.split()) for a in answers if a and a.strip()]
    quotes: Dict[str, str] = {}
    pain_answers = 0
    decision_maker = False
    annual_cost = 0.0
    for text in texts:
        pain_answers += bool(PAIN_RX.search(text))
        for name, rx in _SIGNALS:
            if name not in quotes and rx.search(text):
                quotes[name] = _quote(text)
        decision_maker = decision_maker or bool(DECISION_RX.search(text))
        annual_cost = max(annual_cost, sum(annual_amounts(text)))
    avg_words = sum(len(t.split()) for t in texts) / len(texts) if texts else 0.0
    return ProspectSignals(
        answers=len(texts),
        avg_words=avg_words,
        quotes=quotes,
        pain_answers=pain_answers,
        decision_maker=decision_maker,
        annual_cost=annual_cost,
    )


def readiness_score(signals: ProspectSignals, open_objections: int) -> int:
    score = min(signals.pain_answers, 3) * 10
    score += 15 if "cost" in signals.quotes else 0
    score += 10 if "timeline" in signals.quotes else 0
    score += 20 if "buying" in signals.quotes else 0
    score += 10 if signals.decision_maker else 0
    score += 10 if signals.avg_words >= 12 else 0
    score -= min(open_objections, 2) * 10
    return max(0, min(100, score))


def stage_for(readiness: int) -> str:
    if readiness < 30:
        return "cold"
    if readiness < 60:
        return "warming"
    if readiness < 80:
        return "ready"
    return "closing"


def driver_for(signals: ProspectSignals, readiness: int) -> str:
    """The lever that fits this prospect best right now."""
    quotes = signals.quotes
    if "buying" in quotes and readiness >= 50:
        return "buying"
    if "approval" in quotes and not signals.decision_maker:
        return "approval"
    if "price" in quotes:
        return "price"
    if "cost" in quotes:
        return "cost"
    if "status_quo" in quotes:
        return "status_quo"
    if "pain" in quotes:
        return "pain"
    return "discovery"


@dataclass(frozen=True)
class BuyerProfile:
    readiness: int
    stage: str
    driver: str
    signals: ProspectSignals
    open_objections: int


def build_profile(signals: ProspectSignals, open_objections: int) -> BuyerProfile:
    readiness = readiness_score(signals, open_objections)
    return BuyerProfile(
        readiness=readiness,
        stage=stage_for(readiness),
        driver=driver_for(signals, readiness),
        signals=signals,
        open_objections=open_objections,
    )


@dataclass(frozen=True)
class Tactic:
    id: str
    kind: str  # "persuasion" or "urgency"
    principle: str
    line: str  # Spanish sentence; placeholders are quotes ({cost_quote}) or business facts ({capacity_slots})
    why: str
    drivers: Tuple[str, ...] = ()
    needs_answer: Optional[str] = None  # a signal the prospect must have given (a key of ProspectSignals.quotes)
    needs_evidence: Tuple[str, ...] = ()  # facts the business must have given
    min_readiness: int = 0


TACTICS: Tuple[Tactic, ...] = (
    Tactic(
        id="cost_of_inaction",
        kind="persuasion",
        principle="Aversión a la pérdida: duele más perder que ganar (Kahneman)",
        line='Me dijiste: "{cost_quote}". Si eso sigue igual otros 12 meses, ¿cuánto te cuesta? Hagamos la cuenta con tus números.',
        why="Usa el costo que la persona ya nombró, sin cifras propias.",
        drivers=("cost", "pain", "price"),
        needs_answer="cost",
    ),
    Tactic(
        id="mirror_pain",
        kind="persuasion",
        principle="Reflejo empático: que se sienta escuchado (rapport)",
        line='Me dijiste: "{pain_quote}". ¿Qué cambiaría en tu semana si eso dejara de pasar?',
        why="Repite sus palabras; no afirma nada sobre el mercado.",
        drivers=("pain", "discovery"),
        needs_answer="pain",
    ),
    Tactic(
        id="status_quo_cost",
        kind="persuasion",
        principle="Sesgo del statu quo: esperar también tiene costo",
        line='Hoy lo resuelven así: "{status_quo_quote}". Cada mes que sigue igual es un mes más con esa forma de trabajar. ¿Qué te frena a cambiarla ahora?',
        why="Muestra el costo de no cambiar con sus propias palabras.",
        drivers=("status_quo", "pain"),
        needs_answer="status_quo",
    ),
    Tactic(
        id="internal_seller",
        kind="persuasion",
        principle="Autoridad: darle a tu contacto con qué convencer a quien decide",
        line="Entiendo que esto lo decide alguien más. ¿Qué necesita ver esa persona para aprobarlo? Te preparo un resumen de una página con tus números para llevarlo.",
        why="Quien compra internamente necesita argumentos, no más presión.",
        drivers=("approval",),
        needs_answer="approval",
    ),
    Tactic(
        id="free_offer",
        kind="persuasion",
        principle="Reciprocidad: dar valor primero genera ganas de devolverlo",
        line="Antes de hablar de precio, te preparo sin costo {free_offer}.",
        why="Requiere una oferta gratuita real que el negocio ofrezca.",
        drivers=("discovery", "price", "pain"),
        needs_evidence=("free_offer",),
    ),
    Tactic(
        id="social_proof",
        kind="persuasion",
        principle="Prueba social verificable (Cialdini)",
        line="Hoy trabajamos con {customers_same_industry} empresas de tu rubro. Una de ellas: {case_result}.",
        why="Solo se usa con cantidad y resultado reales de clientes.",
        drivers=("approval", "price", "discovery"),
        needs_evidence=("customers_same_industry", "case_result"),
    ),
    Tactic(
        id="real_scarcity",
        kind="urgency",
        principle="Escasez real: solo si la capacidad está limitada de verdad (Cialdini)",
        line="Este trimestre tenemos {capacity_slots} lugares de implementación disponibles. {capacity_reason}. Si te interesa uno, conviene reservarlo esta semana.",
        why="Requiere capacidad realmente limitada.",
        drivers=("buying", "approval"),
        needs_evidence=("capacity_slots", "capacity_reason"),
        min_readiness=60,
    ),
    Tactic(
        id="real_deadline",
        kind="urgency",
        principle="Fecha límite real: un cambio que va a ocurrir (Cialdini)",
        line="Desde el {price_change_date}, {price_change_detail}. Si arrancas antes, mantienes las condiciones actuales.",
        why="Requiere un cambio de precio con fecha que el negocio ya decidió.",
        drivers=("buying", "price"),
        needs_evidence=("price_change_date", "price_change_detail"),
        min_readiness=50,
    ),
    Tactic(
        id="risk_reversal",
        kind="persuasion",
        principle="Reversión del riesgo: quitar el riesgo de la decisión (aversión a la pérdida)",
        line="{guarantee}. Así decides con resultados a la vista, no con promesas.",
        why="Requiere una garantía que el negocio realmente ofrezca.",
        drivers=("price", "buying", "approval"),
        needs_evidence=("guarantee",),
    ),
    Tactic(
        id="price_vs_cost",
        kind="persuasion",
        principle="Encuadre: comparar la inversión con el costo que ya describió (anclaje)",
        line='Me dijiste que el problema les cuesta: "{cost_quote}". Frente a eso, la inversión es {price_summary}.',
        why="Compara con su propio costo, no con un precio aislado.",
        drivers=("price",),
        needs_answer="cost",
        needs_evidence=("price_summary",),
    ),
    Tactic(
        id="small_yes",
        kind="persuasion",
        principle="Compromiso y coherencia: un sí pequeño antes del cierre (Belfort)",
        line="¿Te parece si agendamos 30 minutos con quien decide para mostrarle tus números?",
        why="Un compromiso chico hace más probable el siguiente.",
        drivers=("buying", "approval", "cost", "pain", "status_quo", "discovery", "price"),
        min_readiness=30,
    ),
)


@dataclass(frozen=True)
class Move:
    id: str
    kind: str
    principle: str
    why: str
    line: Optional[str]  # the sentence to say; None while the move is blocked
    missing: Tuple[str, ...]  # business facts still needed; empty when ready


@dataclass(frozen=True)
class MovePlan:
    ready: List[Move]
    blocked: List[Move]


def known_facts(facts: Mapping[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in facts.items() if v not in (None, "")}


def _render(tactic: Tactic, values: Mapping[str, Any]) -> str:
    return tactic.line.format_map(values)


def plan_moves(profile: BuyerProfile, facts: Mapping[str, Any], limit: int = 3) -> MovePlan:
    """Moves that fit this prospect. Ready ones are sayable now; blocked ones name the facts still missing."""
    known = known_facts(facts)
    quotes = {f"{name}_quote": text for name, text in profile.signals.quotes.items()}
    ranked: List[Tuple[int, int, Tactic, Tuple[str, ...]]] = []
    for order, tactic in enumerate(TACTICS):
        if tactic.needs_answer and tactic.needs_answer not in profile.signals.quotes:
            continue
        if profile.readiness < tactic.min_readiness:
            continue
        fit = 0 if profile.driver in tactic.drivers else 1
        missing = tuple(f for f in tactic.needs_evidence if f not in known)
        ranked.append((fit, order, tactic, missing))
    ranked.sort(key=lambda item: (item[0], item[1]))

    ready = [
        Move(t.id, t.kind, t.principle, t.why, _render(t, {**quotes, **known}), ())
        for _, _, t, missing in ranked
        if not missing
    ][:limit]
    blocked = [
        Move(t.id, t.kind, t.principle, t.why, None, missing)
        for fit, _, t, missing in ranked
        if missing and fit == 0
    ]
    return MovePlan(ready=ready, blocked=blocked)


def urgency_triggers(facts: Mapping[str, Any]) -> List[Dict[str, Any]]:
    """Urgency lines the business can back with facts. Without facts the list is empty."""
    known = known_facts(facts)
    triggers = []
    for tactic in TACTICS:
        if tactic.kind != "urgency" or any(f not in known for f in tactic.needs_evidence):
            continue
        triggers.append(
            {
                "type": tactic.id,
                "messaging": _render(tactic, known),
                "based_on": {f: known[f] for f in tactic.needs_evidence},
            }
        )
    return triggers


_OBJECTION_ORDER = (("price", PRICE_RX), ("authority", APPROVAL_RX), ("time", TIME_RX))


def classify_objection(text: str) -> str:
    for name, rx in _OBJECTION_ORDER:
        if rx.search(text):
            return name
    return "need"


def is_positive_reply(text: str) -> bool:
    if NEGATIVE_START_RX.search(text):
        return False
    return bool(POSITIVE_RX.search(text))


async def load_profile(db: AsyncSession, deal_id: str) -> BuyerProfile:
    """Build the buyer profile from the answers stored for the deal."""
    answers = (
        await db.execute(
            select(DiscoveryResponse.response_text)
            .where(DiscoveryResponse.deal_id == str(deal_id))
            .order_by(DiscoveryResponse.asked_at)
        )
    ).scalars().all()
    open_objections = (
        await db.execute(
            select(func.count())
            .select_from(ObjectionHandling)
            .where(
                ObjectionHandling.deal_id == str(deal_id),
                or_(ObjectionHandling.resolved.is_(None), ObjectionHandling.resolved.is_(False)),
            )
        )
    ).scalar_one()
    return build_profile(extract_signals(answers), open_objections)
