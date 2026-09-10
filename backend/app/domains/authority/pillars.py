"""The six pillars of authority, each computed from rows that really exist.

Design rule inherited from the rest of this codebase: a pillar with no evidence
scores 0 and says what is missing. It never starts at 50 "to look reasonable" --
a new account genuinely has no authority yet, and telling it otherwise is how a
dashboard becomes decoration.

Where the numbers come from:
  identidad     web_presence (hub, Organization schema, sameAs) + BusinessContext
  red           web_presence authority_report (cross-linking between properties)
  prueba_social platform_reviews / testimonials / awards rows
  respuesta     conversations + messages (real reply rate and speed)
  contenido     the real page audits stored by web_presence
  verificacion  user flags, domain/website state, connected channels

Each pillar is split in two: a pure `*_from(...)` core that scores primitives,
and a thin adapter that pulls those primitives out of the domain objects. The
split exists so a recommendation can be PRICED by replaying the same maths with
hypothetical inputs (see `score_gain`) instead of carrying a hand-written "+12"
that nothing keeps honest.
"""

from __future__ import annotations

from typing import Any, Optional

#: pillar key -> (label, weight). Weights sum to 1.0.
PILLARS: dict[str, tuple[str, float]] = {
    "identidad": ("Identidad de marca", 0.20),
    "red": ("Red de propiedades", 0.20),
    "prueba_social": ("Prueba social", 0.20),
    "respuesta": ("Respuesta a clientes", 0.15),
    "contenido": ("Contenido", 0.15),
    "verificacion": ("Verificación", 0.10),
}


def _pillar(score: float, inputs: dict[str, Any], missing: list[str]) -> dict[str, Any]:
    return {
        "score": round(max(0.0, min(100.0, score)), 1),
        "inputs": inputs,
        "missing": missing,
    }


# ── identidad ───────────────────────────────────────────────────────────────
def identidad_from(
    *,
    has_hub: bool,
    org_schema: bool,
    same_as: bool,
    has_value_proposition: bool,
    has_target_audience: bool,
) -> dict[str, Any]:
    score = 0.0
    missing: list[str] = []

    if has_hub:
        score += 30
    else:
        missing.append("Cargá tu sitio propio como centro de tu marca")

    if org_schema:
        score += 30
    else:
        missing.append("Declarar tu negocio con schema Organization en tu web")

    if same_as:
        score += 20
    else:
        missing.append("Declarar tus perfiles con sameAs en tu web")

    if has_value_proposition and has_target_audience:
        score += 20
    else:
        missing.append("Definir propuesta de valor y público objetivo en el cuestionario")

    return _pillar(score, {
        "has_hub": has_hub,
        "org_schema": org_schema,
        "same_as": same_as,
        "has_value_proposition": has_value_proposition,
        "has_target_audience": has_target_audience,
    }, missing)


def identidad(authority_report: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
    """Does the market have something to recognise? A hub, a declared identity,
    and a stated promise are what turn a set of accounts into a brand."""
    checks = {c["key"]: c["passed"] for c in authority_report.get("checks", [])}
    ctx = context or {}
    return identidad_from(
        has_hub=bool(authority_report.get("hub")),
        org_schema=bool(checks.get("org_schema")),
        same_as=bool(checks.get("same_as")),
        has_value_proposition=bool(ctx.get("value_proposition")),
        has_target_audience=bool(ctx.get("target_audience")),
    )


# ── red ─────────────────────────────────────────────────────────────────────
def red_from(
    *, profiles: int, linked_from_hub: int, linking_back: int, back_verifiable: int
) -> dict[str, Any]:
    if profiles == 0:
        return _pillar(0.0, {
            "profiles": 0, "linked_from_hub": 0, "linking_back": 0, "back_verifiable": 0,
        }, ["Sumá tus redes y tiendas para poder conectarlas con tu web"])

    score = (linked_from_hub / profiles) * 60
    if back_verifiable:
        score += (linking_back / back_verifiable) * 40

    missing: list[str] = []
    if linked_from_hub < profiles:
        missing.append(
            f"Enlazá desde tu web los {profiles - linked_from_hub} perfiles que todavía no enlazás"
        )
    if back_verifiable and linking_back < back_verifiable:
        missing.append("Poné el link a tu web en la bio de los perfiles que no la enlazan")

    return _pillar(score, {
        "profiles": profiles,
        "linked_from_hub": linked_from_hub,
        "linking_back": linking_back,
        "back_verifiable": back_verifiable,
    }, missing)


def red(authority_report: dict[str, Any]) -> dict[str, Any]:
    """Search engines pass authority along links. Properties that do not point
    at each other each start from zero."""
    profiles = authority_report.get("profiles", [])
    return red_from(
        profiles=len(profiles),
        linked_from_hub=sum(1 for p in profiles if p.get("linked_from_hub")),
        linking_back=sum(1 for p in profiles if p.get("links_back_to_hub") is True),
        back_verifiable=sum(1 for p in profiles if p.get("links_back_to_hub") is not None),
    )


# ── prueba social ───────────────────────────────────────────────────────────
def prueba_social_from(
    *, reviews: int, rating: float, answered: int, testimonials: int, awards: int
) -> dict[str, Any]:
    score = 0.0
    missing: list[str] = []

    # Volume: 1 review = 8 pts, 5 = 30, 20 = 45, saturating at 50. Steep at the
    # start on purpose -- 0 to 5 changes whether a stranger trusts you, 200 to
    # 205 does not.
    if reviews:
        score += min(50.0, 8 + 22 * min(1.0, (reviews - 1) / 4) + 15 * min(1.0, (reviews - 5) / 15))
    else:
        missing.append(
            "Conseguí tus primeras reseñas: sin ninguna, un desconocido no tiene en qué apoyarse"
        )

    if reviews and rating:
        score += min(20.0, max(0.0, (rating - 3.0) / 2.0 * 20))

    if reviews:
        answer_rate = answered / reviews
        score += answer_rate * 15
        if answer_rate < 0.8:
            missing.append("Respondé todas las reseñas, también las malas: se lee como responsabilidad")

    if testimonials:
        score += min(10.0, testimonials * 3.0)
    else:
        missing.append("Sumá testimonios de clientes reales con nombre y caso concreto")

    if awards:
        score += min(5.0, awards * 2.5)

    return _pillar(score, {
        "reviews": reviews,
        "rating": rating,
        "answered_reviews": answered,
        "testimonials": testimonials,
        "awards": awards,
    }, missing)


def prueba_social(trust: dict[str, Any] | None) -> dict[str, Any]:
    """Reviews, testimonials and awards that really exist as rows."""
    components = (trust or {}).get("components", {}) if trust else {}
    return prueba_social_from(
        reviews=int(components.get("review_count", 0) or 0),
        rating=float(components.get("review_rating", 0) or 0),
        answered=int(components.get("responded_reviews", 0) or 0),
        testimonials=int(components.get("testimonial_count", 0) or 0),
        awards=int(components.get("award_count", 0) or 0),
    )


# ── respuesta ───────────────────────────────────────────────────────────────
def respuesta_from(
    *, inbound: int, answered: int, median_minutes: Optional[float]
) -> dict[str, Any]:
    if inbound == 0:
        return _pillar(0.0, {"inbound": 0, "answered": 0, "median_minutes": None},
                       ["Todavía no entraron consultas: conectá un canal para empezar a medirlo"])

    rate = answered / inbound
    score = rate * 70
    missing: list[str] = []
    if rate < 0.95:
        missing.append(f"Quedaron {inbound - answered} consultas sin responder")

    if median_minutes is None:
        missing.append("Sin tiempos de respuesta medidos todavía")
    elif median_minutes <= 5:
        score += 30
    elif median_minutes <= 30:
        score += 22
    elif median_minutes <= 120:
        score += 14
    elif median_minutes <= 1440:
        score += 7
    else:
        missing.append("La mitad de tus clientes espera más de un día: es la fuga más cara que tenés")

    return _pillar(score, {
        "inbound": inbound,
        "answered": answered,
        "response_rate": round(rate * 100, 1),
        "median_minutes": median_minutes,
    }, missing)


def respuesta(conversations: dict[str, Any], median_minutes: float | None) -> dict[str, Any]:
    """Answering, and answering fast, is the authority signal a small business
    can move this week -- unlike backlinks or awards."""
    return respuesta_from(
        inbound=int(conversations.get("inbound", 0) or 0),
        answered=int(conversations.get("answered", 0) or 0),
        median_minutes=median_minutes,
    )


# ── contenido ───────────────────────────────────────────────────────────────
def contenido_from(
    *, pages: int, average_seo_score: float, average_words: float, pages_with_schema: int
) -> dict[str, Any]:
    if pages == 0:
        return _pillar(0.0, {
            "pages": 0, "average_seo_score": 0, "average_words": 0, "pages_with_schema": 0,
        }, ["Cargá y analizá al menos una página tuya"])

    # Half the pillar is page quality, a quarter depth, a quarter structure.
    score = average_seo_score * 0.5
    score += min(25.0, average_words / 800 * 25)
    score += (pages_with_schema / pages) * 25

    missing: list[str] = []
    if average_words < 300:
        missing.append("Tus páginas tienen poco texto: sumá descripción real, casos y preguntas frecuentes")
    if pages_with_schema < pages:
        missing.append(f"{pages - pages_with_schema} página(s) sin datos estructurados")
    if pages < 3:
        missing.append("Publicá más páginas útiles: una sola página deja poco por donde entrar")

    return _pillar(score, {
        "pages": pages,
        "average_seo_score": round(average_seo_score, 1),
        "average_words": round(average_words),
        "pages_with_schema": pages_with_schema,
    }, missing)


def contenido(seo_report: dict[str, Any]) -> dict[str, Any]:
    """Pages that actually say something, with structure a crawler understands."""
    pages = [p for p in seo_report.get("pages", []) if p.get("score") is not None]
    if not pages:
        return contenido_from(pages=0, average_seo_score=0, average_words=0, pages_with_schema=0)

    words = [p.get("word_count") or 0 for p in pages]
    return contenido_from(
        pages=len(pages),
        average_seo_score=sum(p["score"] for p in pages) / len(pages),
        average_words=sum(words) / len(words),
        pages_with_schema=sum(1 for p in pages if p.get("json_ld_types")),
    )


# ── verificación ────────────────────────────────────────────────────────────
def verificacion_from(
    *,
    email_verified: bool,
    two_factor_enabled: bool,
    has_business: bool,
    website_published: bool,
    domain_verified: bool,
    channels: int,
) -> dict[str, Any]:
    checks = [
        (email_verified, 20, "Verificá tu email"),
        (two_factor_enabled, 15, "Activá la verificación en dos pasos"),
        (has_business, 15, "Creá tu negocio"),
        (website_published, 20, "Publicá tu sitio"),
        (domain_verified, 20, "Verificá tu dominio"),
        (channels > 0, 10, "Conectá al menos un canal de atención"),
    ]
    return _pillar(
        sum(points for ok, points, _ in checks if ok),
        {
            "email_verified": email_verified,
            "two_factor_enabled": two_factor_enabled,
            "website_published": website_published,
            "domain_verified": domain_verified,
            "channels_connected": channels,
        },
        [label for ok, _, label in checks if not ok],
    )


def verificacion(verification: dict[str, Any], channels: int) -> dict[str, Any]:
    """Cheap, binary trust signals. Each one is a reason not to be mistaken for
    a throwaway account."""
    return verificacion_from(
        email_verified=bool(verification.get("email_verified")),
        two_factor_enabled=bool(verification.get("two_factor_enabled")),
        has_business=bool(verification.get("has_business")),
        website_published=bool(verification.get("website_published")),
        domain_verified=bool(verification.get("domain_verified")),
        channels=channels,
    )


def total_score(pillar_scores: dict[str, dict[str, Any]]) -> float:
    """Weighted average of the six pillars."""
    total = sum(
        pillar_scores.get(key, {}).get("score", 0.0) * weight
        for key, (_, weight) in PILLARS.items()
    )
    return round(total, 1)


def flatten_signals(pillar_scores: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Flat measurements for snapshot-to-snapshot diffing by the analyst."""
    flat: dict[str, Any] = {}
    for key, data in pillar_scores.items():
        flat[f"{key}_score"] = data.get("score")
        for input_key, value in (data.get("inputs") or {}).items():
            if isinstance(value, (int, float, bool)):
                flat[f"{key}.{input_key}"] = value
    return flat


# ── Simulación: cuánto sumaría realmente cerrar una brecha ──────────────────
#
# El impacto de cada recomendación se calcula volviendo a correr LA MISMA
# función del pilar con los datos hipotéticos. Si mañana cambia el peso de un
# chequeo, el número que ve el usuario cambia solo, porque sale de la fórmula
# y no de una constante escrita a mano.

_SIMULATORS = {
    "identidad": lambda d: identidad_from(
        has_hub=bool(d.get("has_hub")),
        org_schema=bool(d.get("org_schema")),
        same_as=bool(d.get("same_as")),
        has_value_proposition=bool(d.get("has_value_proposition")),
        has_target_audience=bool(d.get("has_target_audience")),
    ),
    "red": lambda d: red_from(
        profiles=int(d.get("profiles", 0) or 0),
        linked_from_hub=int(d.get("linked_from_hub", 0) or 0),
        linking_back=int(d.get("linking_back", 0) or 0),
        back_verifiable=int(d.get("back_verifiable", 0) or 0),
    ),
    "prueba_social": lambda d: prueba_social_from(
        reviews=int(d.get("reviews", 0) or 0),
        rating=float(d.get("rating", 0) or 0),
        answered=int(d.get("answered_reviews", 0) or 0),
        testimonials=int(d.get("testimonials", 0) or 0),
        awards=int(d.get("awards", 0) or 0),
    ),
    "respuesta": lambda d: respuesta_from(
        inbound=int(d.get("inbound", 0) or 0),
        answered=int(d.get("answered", 0) or 0),
        median_minutes=d.get("median_minutes"),
    ),
    "contenido": lambda d: contenido_from(
        pages=int(d.get("pages", 0) or 0),
        average_seo_score=float(d.get("average_seo_score", 0) or 0),
        average_words=float(d.get("average_words", 0) or 0),
        pages_with_schema=int(d.get("pages_with_schema", 0) or 0),
    ),
    "verificacion": lambda d: verificacion_from(
        email_verified=bool(d.get("email_verified")),
        two_factor_enabled=bool(d.get("two_factor_enabled")),
        has_business=bool(d.get("has_business", True)),
        website_published=bool(d.get("website_published")),
        domain_verified=bool(d.get("domain_verified")),
        channels=int(d.get("channels_connected", 0) or 0),
    ),
}


def simulate(pillar_key: str, inputs: dict[str, Any], **overrides: Any) -> float:
    """Score this pillar would have if `overrides` were true."""
    simulator = _SIMULATORS.get(pillar_key)
    if simulator is None:
        return 0.0
    return simulator({**inputs, **overrides})["score"]


def score_gain(pillar_key: str, inputs: dict[str, Any], **overrides: Any) -> float:
    """Points this would add to the TOTAL score (pillar delta x its weight).

    This is the number shown to the user as "+X.X pts": a real projection from
    the scoring model, not an estimate of business impact -- closing the gap
    moves the score by exactly this much.
    """
    _, weight = PILLARS.get(pillar_key, ("", 0.0))
    current = simulate(pillar_key, inputs)
    projected = simulate(pillar_key, inputs, **overrides)
    return round(max(0.0, projected - current) * weight, 1)
