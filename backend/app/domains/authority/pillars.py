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
"""

from __future__ import annotations

from typing import Any

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


def identidad(authority_report: dict[str, Any], context: dict[str, Any] | None) -> dict[str, Any]:
    """Does the market have something to recognise? A hub, a declared identity,
    and a stated promise are what turn a set of accounts into a brand."""
    hub = authority_report.get("hub")
    checks = {c["key"]: c["passed"] for c in authority_report.get("checks", [])}
    ctx = context or {}

    score = 0.0
    missing: list[str] = []

    if hub:
        score += 30
    else:
        missing.append("Cargá tu sitio propio como centro de tu marca")

    if checks.get("org_schema"):
        score += 30
    else:
        missing.append("Declarar tu negocio con schema Organization en tu web")

    if checks.get("same_as"):
        score += 20
    else:
        missing.append("Declarar tus perfiles con sameAs en tu web")

    has_promise = bool(ctx.get("value_proposition")) and bool(ctx.get("target_audience"))
    if has_promise:
        score += 20
    else:
        missing.append("Definir propuesta de valor y público objetivo en el cuestionario")

    return _pillar(score, {
        "has_hub": bool(hub),
        "org_schema": bool(checks.get("org_schema")),
        "same_as": bool(checks.get("same_as")),
        "has_value_proposition": bool(ctx.get("value_proposition")),
        "has_target_audience": bool(ctx.get("target_audience")),
    }, missing)


def red(authority_report: dict[str, Any]) -> dict[str, Any]:
    """Search engines pass authority along links. Properties that do not point
    at each other each start from zero."""
    profiles = authority_report.get("profiles", [])
    total = len(profiles)
    if total == 0:
        return _pillar(0.0, {"profiles": 0, "linked_from_hub": 0, "linking_back": 0},
                       ["Sumá tus redes y tiendas para poder conectarlas con tu web"])

    linked = sum(1 for p in profiles if p.get("linked_from_hub"))
    back = sum(1 for p in profiles if p.get("links_back_to_hub") is True)
    verifiable_back = sum(1 for p in profiles if p.get("links_back_to_hub") is not None)

    score = (linked / total) * 60
    if verifiable_back:
        score += (back / verifiable_back) * 40

    missing: list[str] = []
    if linked < total:
        missing.append(f"Enlazá desde tu web los {total - linked} perfiles que todavía no enlazás")
    if verifiable_back and back < verifiable_back:
        missing.append("Poné el link a tu web en la bio de los perfiles que no la enlazan")

    return _pillar(score, {
        "profiles": total,
        "linked_from_hub": linked,
        "linking_back": back,
        "back_verifiable": verifiable_back,
    }, missing)


def prueba_social(trust: dict[str, Any] | None) -> dict[str, Any]:
    """Reviews, testimonials and awards that really exist as rows.

    Scaling is deliberately steep at the start and flat later: going from 0 to 5
    reviews changes whether a stranger trusts you; going from 200 to 205 does
    not.
    """
    components = (trust or {}).get("components", {}) if trust else {}
    reviews = int(components.get("review_count", 0) or 0)
    rating = float(components.get("review_rating", 0) or 0)
    answered = int(components.get("responded_reviews", 0) or 0)
    testimonials = int(components.get("testimonial_count", 0) or 0)
    awards = int(components.get("award_count", 0) or 0)

    score = 0.0
    missing: list[str] = []

    # Volume: 1 review = 8 pts, 5 = 30, 20 = 45, then saturating at 50.
    if reviews:
        score += min(50.0, 8 + 22 * min(1.0, (reviews - 1) / 4) + 15 * min(1.0, (reviews - 5) / 15))
    else:
        missing.append("Conseguí tus primeras reseñas: sin ninguna, un desconocido no tiene en qué apoyarse")

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


def respuesta(conversations: dict[str, Any], median_minutes: float | None) -> dict[str, Any]:
    """Answering, and answering fast, is the authority signal a small business
    can move this week -- unlike backlinks or awards."""
    inbound = int(conversations.get("inbound", 0) or 0)
    answered = int(conversations.get("answered", 0) or 0)

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


def contenido(seo_report: dict[str, Any]) -> dict[str, Any]:
    """Pages that actually say something, with structure a crawler understands."""
    pages = [p for p in seo_report.get("pages", []) if p.get("score") is not None]
    if not pages:
        return _pillar(0.0, {"pages": 0}, ["Cargá y analizá al menos una página tuya"])

    avg_score = sum(p["score"] for p in pages) / len(pages)
    words = [p.get("word_count") or 0 for p in pages]
    avg_words = sum(words) / len(words)
    with_schema = sum(1 for p in pages if p.get("json_ld_types"))

    # Half the pillar is page quality, a quarter depth, a quarter structure.
    score = avg_score * 0.5
    score += min(25.0, avg_words / 800 * 25)
    score += (with_schema / len(pages)) * 25

    missing: list[str] = []
    if avg_words < 300:
        missing.append("Tus páginas tienen poco texto: sumá descripción real, casos y preguntas frecuentes")
    if with_schema < len(pages):
        missing.append(f"{len(pages) - with_schema} página(s) sin datos estructurados")
    if len(pages) < 3:
        missing.append("Publicá más páginas útiles: una sola página deja poco por donde entrar")

    return _pillar(score, {
        "pages": len(pages),
        "average_seo_score": round(avg_score, 1),
        "average_words": round(avg_words),
        "pages_with_schema": with_schema,
    }, missing)


def verificacion(verification: dict[str, Any], channels: int) -> dict[str, Any]:
    """Cheap, binary trust signals. Each one is a reason not to be mistaken for
    a throwaway account."""
    checks = [
        (bool(verification.get("email_verified")), 20, "Verificá tu email"),
        (bool(verification.get("two_factor_enabled")), 15, "Activá la verificación en dos pasos"),
        (bool(verification.get("has_business")), 15, "Creá tu negocio"),
        (bool(verification.get("website_published")), 20, "Publicá tu sitio"),
        (bool(verification.get("domain_verified")), 20, "Verificá tu dominio"),
        (channels > 0, 10, "Conectá al menos un canal de atención"),
    ]
    score = sum(points for ok, points, _ in checks if ok)
    missing = [label for ok, _, label in checks if not ok]

    return _pillar(score, {
        "email_verified": bool(verification.get("email_verified")),
        "two_factor_enabled": bool(verification.get("two_factor_enabled")),
        "website_published": bool(verification.get("website_published")),
        "domain_verified": bool(verification.get("domain_verified")),
        "channels_connected": channels,
    }, missing)


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
