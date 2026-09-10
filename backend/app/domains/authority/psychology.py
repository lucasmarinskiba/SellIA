"""Specialist agents: established persuasion psychology applied to real numbers.

Each agent owns one well-documented principle of influence and looks at the one
pillar where that principle actually operates. An agent only speaks when the
account's own measurements give it something to say -- the social-proof agent
stays quiet about review counts it cannot see, and none of them ever quotes an
invented statistic ("+37% de conversión") to justify a suggestion.

Ethics boundary, enforced in the copy itself: scarcity and urgency are only ever
suggested where the scarcity is REAL (actual stock, an actual deadline).
Manufacturing false urgency works briefly and then costs exactly the thing this
whole module is meant to build, which is being believed.

Principles used are attributed to their source in `principle`; the wording of
each recommendation is derived from the account's own figures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from .models import ActionMode


@dataclass
class Recommendation:
    action_key: str
    pillar: str
    agent: str
    principle: str
    title: str
    rationale: str
    mode: ActionMode = ActionMode.MANUAL
    impact_points: int = 5
    channel: str | None = None
    script: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "action_key": self.action_key,
            "pillar": self.pillar,
            "agent": self.agent,
            "principle": self.principle,
            "title": self.title,
            "rationale": self.rationale,
            "mode": self.mode.value,
            "impact_points": self.impact_points,
            "channel": self.channel,
            "script": self.script,
        }


@dataclass
class Agent:
    key: str
    name: str
    principle: str
    source: str
    pillar: str
    focus: str
    analyze: Callable[[dict[str, Any], dict[str, Any]], list[Recommendation]] = field(repr=False)

    def as_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "principle": self.principle,
            "source": self.source,
            "pillar": self.pillar,
            "focus": self.focus,
        }


def _business_name(ctx: dict[str, Any]) -> str:
    return ctx.get("business_name") or "tu negocio"


def _what_you_sell(ctx: dict[str, Any]) -> str:
    return ctx.get("industry") or ctx.get("business_type") or "lo que vendés"


def _audience(ctx: dict[str, Any]) -> str:
    return ctx.get("target_audience") or "tu público"


# ── Agente 1 · Prueba social ────────────────────────────────────────────────
def _social_proof(pillars: dict[str, Any], ctx: dict[str, Any]) -> list[Recommendation]:
    data = pillars.get("prueba_social", {}).get("inputs", {})
    reviews = int(data.get("reviews", 0) or 0)
    answered = int(data.get("answered_reviews", 0) or 0)
    testimonials = int(data.get("testimonials", 0) or 0)
    conv = pillars.get("respuesta", {}).get("inputs", {})
    answered_convs = int(conv.get("answered", 0) or 0)
    out: list[Recommendation] = []

    if reviews == 0:
        out.append(Recommendation(
            action_key="ask_first_reviews",
            pillar="prueba_social",
            agent="social_proof",
            principle="Prueba social",
            title="Pedí tus primeras reseñas a quienes ya te compraron",
            rationale=(
                f"No tenés ninguna reseña cargada. Frente a un desconocido, {_business_name(ctx)} "
                "es una afirmación sin respaldo: la gente mira lo que hicieron otros antes de "
                "decidir, sobre todo cuando no conoce la marca."
                + (f" Ya tenés {answered_convs} conversaciones atendidas: ahí están tus candidatos."
                   if answered_convs else "")
            ),
            mode=ActionMode.ASSISTED if answered_convs else ActionMode.MANUAL,
            impact_points=15,
            channel="whatsapp",
            script=(
                f"Hola {{nombre}}, soy de {_business_name(ctx)}. Vi que te llevaste "
                f"{{producto}} hace unos días. ¿Te está funcionando bien?\n\n"
                "Si quedaste conforme, me ayudaría muchísimo que lo cuentes en dos líneas acá: "
                "{link}. A quien está por comprar por primera vez le sirve más leer a alguien "
                "como vos que cualquier cosa que diga yo.\n\n"
                "Y si algo no salió como esperabas, contámelo a mí primero y lo resolvemos."
            ),
        ))
    elif reviews < 10:
        out.append(Recommendation(
            action_key="grow_reviews",
            pillar="prueba_social",
            agent="social_proof",
            principle="Prueba social",
            title=f"Llevá tus {reviews} reseñas a diez",
            rationale=(
                f"Tenés {reviews} reseña(s). El salto de credibilidad más grande está entre "
                "ninguna y las primeras diez: a partir de ahí deja de parecer un caso aislado "
                "y empieza a parecer un patrón."
            ),
            mode=ActionMode.ASSISTED,
            impact_points=10,
            channel="whatsapp",
            script=(
                f"Hola {{nombre}}, gracias por elegir {_business_name(ctx)}. "
                "¿Me dejás tu opinión en un minuto? Acá: {link}\n"
                "Contá lo concreto: qué necesitabas, qué te llevaste y cómo te fue."
            ),
        ))

    if reviews and answered < reviews:
        pending = reviews - answered
        out.append(Recommendation(
            action_key="answer_reviews",
            pillar="prueba_social",
            agent="social_proof",
            principle="Prueba social",
            title=f"Respondé las {pending} reseñas sin responder",
            rationale=(
                "Quien lee reseñas mira sobre todo cómo responde el vendedor, y muy especialmente "
                "a las malas. Una crítica bien contestada convence más que diez elogios, porque "
                "muestra qué pasa cuando algo sale mal."
            ),
            mode=ActionMode.MANUAL,
            impact_points=8,
        ))

    if testimonials == 0 and reviews:
        out.append(Recommendation(
            action_key="add_testimonials",
            pillar="prueba_social",
            agent="social_proof",
            principle="Prueba social",
            title="Convertí tus mejores reseñas en testimonios con nombre y caso",
            rationale=(
                "Una estrella es un número; un testimonio con nombre, situación y resultado es "
                "una historia con la que alguien parecido a tu cliente se identifica. "
                f"Sobre todo si tu público es {_audience(ctx)}."
            ),
            mode=ActionMode.MANUAL,
            impact_points=6,
        ))

    return out


# ── Agente 2 · Autoridad ────────────────────────────────────────────────────
def _authority(pillars: dict[str, Any], ctx: dict[str, Any]) -> list[Recommendation]:
    ident = pillars.get("identidad", {}).get("inputs", {})
    verif = pillars.get("verificacion", {}).get("inputs", {})
    out: list[Recommendation] = []

    if not ident.get("org_schema"):
        out.append(Recommendation(
            action_key="publish_org_schema",
            pillar="identidad",
            agent="authority",
            principle="Autoridad",
            title="Declará tu negocio como entidad (JSON-LD Organization)",
            rationale=(
                "Google necesita entender que tu web, tus redes y tu tienda son un mismo negocio "
                "para tratarte como una marca y no como páginas sueltas. El código ya está "
                "generado con tus datos reales en la herramienta SEO: falta pegarlo."
            ),
            mode=ActionMode.ASSISTED,
            impact_points=12,
        ))

    if not verif.get("domain_verified"):
        out.append(Recommendation(
            action_key="verify_domain",
            pillar="verificacion",
            agent="authority",
            principle="Autoridad",
            title="Verificá tu dominio propio",
            rationale=(
                "Un dominio propio verificado es la diferencia entre una marca y un perfil "
                "alquilado en la plataforma de otro. Además es lo que te deja reclamar la "
                "autoría de tu contenido."
            ),
            mode=ActionMode.MANUAL,
            impact_points=10,
        ))

    if not ident.get("has_value_proposition"):
        out.append(Recommendation(
            action_key="define_promise",
            pillar="identidad",
            agent="authority",
            principle="Autoridad",
            title="Escribí en una frase por qué te compran a vos",
            rationale=(
                "Sin una promesa explícita, el cliente te compara sólo por precio, que es la "
                "única dimensión que queda cuando no hay otra. Definirla es lo que después "
                "permite sostener el mismo mensaje en todos tus canales."
            ),
            mode=ActionMode.MANUAL,
            impact_points=8,
        ))

    return out


# ── Agente 3 · Reciprocidad ─────────────────────────────────────────────────
def _reciprocity(pillars: dict[str, Any], ctx: dict[str, Any]) -> list[Recommendation]:
    content = pillars.get("contenido", {}).get("inputs", {})
    pages = int(content.get("pages", 0) or 0)
    words = int(content.get("average_words", 0) or 0)
    out: list[Recommendation] = []

    if pages and words < 300:
        out.append(Recommendation(
            action_key="publish_useful_content",
            pillar="contenido",
            agent="reciprocity",
            principle="Reciprocidad",
            title="Publicá algo que sirva aunque no te compren",
            rationale=(
                f"Tus páginas promedian {words} palabras: alcanzan para vender, no para ayudar. "
                "Cuando alguien recibe algo útil primero, queda predispuesto a devolver el gesto, "
                f"y de paso te posiciona como quien sabe de {_what_you_sell(ctx)}."
            ),
            mode=ActionMode.MANUAL,
            impact_points=10,
            channel="web",
            script=(
                f"Ideas concretas para {_what_you_sell(ctx)}:\n"
                "· Cómo elegir bien: los 3 errores que ves siempre en tus clientes nuevos.\n"
                "· Comparación honesta entre las opciones que existen, incluida la que no vendés.\n"
                "· El caso de un cliente: qué necesitaba, qué probó antes, cómo terminó.\n"
                "Escribilo como se lo explicarías a alguien en el mostrador, no como un folleto."
            ),
        ))

    return out


# ── Agente 4 · Compromiso y coherencia ──────────────────────────────────────
def _consistency(pillars: dict[str, Any], ctx: dict[str, Any]) -> list[Recommendation]:
    red = pillars.get("red", {}).get("inputs", {})
    total = int(red.get("profiles", 0) or 0)
    linked = int(red.get("linked_from_hub", 0) or 0)
    back = int(red.get("linking_back", 0) or 0)
    verifiable = int(red.get("back_verifiable", 0) or 0)
    out: list[Recommendation] = []

    if total and linked < total:
        out.append(Recommendation(
            action_key="link_profiles_from_site",
            pillar="red",
            agent="consistency",
            principle="Compromiso y coherencia",
            title=f"Enlazá desde tu web los {total - linked} perfiles que faltan",
            rationale=(
                "Una marca que se muestra igual en todos lados se percibe como más sólida, y los "
                "buscadores usan literalmente esos enlaces para repartir autoridad. Hoy tenés "
                f"{linked} de {total} perfiles enlazados desde tu sitio."
            ),
            mode=ActionMode.MANUAL,
            impact_points=10,
        ))

    if verifiable and back < verifiable:
        out.append(Recommendation(
            action_key="link_back_to_site",
            pillar="red",
            agent="consistency",
            principle="Compromiso y coherencia",
            title="Poné el link a tu web en la bio de cada perfil",
            rationale=(
                "El circuito tiene que cerrarse en las dos direcciones: quien te descubre en una "
                "red tiene que poder llegar a tu casa propia, donde vos ponés las reglas y nadie "
                "te cambia el alcance."
            ),
            mode=ActionMode.MANUAL,
            impact_points=8,
        ))

    return out


# ── Agente 5 · Simpatía y trato ─────────────────────────────────────────────
def _liking(pillars: dict[str, Any], ctx: dict[str, Any]) -> list[Recommendation]:
    resp = pillars.get("respuesta", {}).get("inputs", {})
    inbound = int(resp.get("inbound", 0) or 0)
    answered = int(resp.get("answered", 0) or 0)
    median = resp.get("median_minutes")
    out: list[Recommendation] = []

    if inbound and answered < inbound:
        out.append(Recommendation(
            action_key="close_unanswered",
            pillar="respuesta",
            agent="liking",
            principle="Simpatía y reciprocidad",
            title=f"Contestá las {inbound - answered} consultas que quedaron abiertas",
            rationale=(
                "Cada consulta sin responder es alguien que ya había levantado la mano. No hay "
                "acción de marketing con mejor retorno que atender a quien ya te escribió."
            ),
            mode=ActionMode.MANUAL,
            impact_points=12,
        ))

    if isinstance(median, (int, float)) and median > 60:
        out.append(Recommendation(
            action_key="speed_up_first_reply",
            pillar="respuesta",
            agent="liking",
            principle="Simpatía y reciprocidad",
            title="Bajá el tiempo de primera respuesta",
            rationale=(
                f"La mitad de tus clientes espera más de {round(median)} minutos. La atención de "
                "quien pregunta dura poco: cuando llega la respuesta, muchas veces ya compró en "
                "otro lado. Activar la respuesta automática de la IA cubre justo esa ventana."
            ),
            mode=ActionMode.AUTOMATIC,
            impact_points=10,
            channel="whatsapp",
            script=(
                f"¡Hola! Gracias por escribir a {_business_name(ctx)}. "
                "Contame qué estás buscando y te digo enseguida si lo tengo, cuánto sale y en "
                "cuánto llega. Si preferís, decime tu ciudad y te paso las opciones de envío."
            ),
        ))

    return out


# ── Agente 6 · Escasez honesta ──────────────────────────────────────────────
def _scarcity(pillars: dict[str, Any], ctx: dict[str, Any]) -> list[Recommendation]:
    """Only ever recommends scarcity that is real, and says so explicitly."""
    resp = pillars.get("respuesta", {}).get("inputs", {})
    if not int(resp.get("inbound", 0) or 0):
        return []

    return [Recommendation(
        action_key="honest_scarcity",
        pillar="respuesta",
        agent="scarcity",
        principle="Escasez (sólo si es real)",
        title="Comunicá tus límites reales de stock o agenda",
        rationale=(
            "Decir lo que de verdad se agota o el plazo que de verdad existe ayuda a decidir a "
            "quien ya estaba dudando. Inventar urgencia funciona una vez y después destruye "
            "exactamente lo que este panel intenta construir: que te crean. "
            "Si no tenés un límite real, no lo uses."
        ),
        mode=ActionMode.MANUAL,
        impact_points=4,
        channel="instagram",
        script=(
            "Quedan {cantidad} unidades de {producto} de esta tanda.\n"
            "La próxima entra el {fecha}, así que si lo estabas viendo, ahora es cuando.\n"
            "(Si te lo perdés, escribime y te aviso cuando vuelva.)"
        ),
    )]


# ── Agente 7 · Mera exposición ──────────────────────────────────────────────
def _mere_exposure(pillars: dict[str, Any], ctx: dict[str, Any]) -> list[Recommendation]:
    red = pillars.get("red", {}).get("inputs", {})
    if int(red.get("profiles", 0) or 0) == 0:
        return [Recommendation(
            action_key="be_present",
            pillar="red",
            agent="mere_exposure",
            principle="Mera exposición",
            title="Elegí dos canales y aparecé seguido en ellos",
            rationale=(
                "La familiaridad genera confianza por repetición: cuanto más te ven, más confiable "
                "parecés, aun sin comprar. Es mejor estar de forma constante en dos canales que "
                "aparecer una vez en seis."
            ),
            mode=ActionMode.MANUAL,
            impact_points=8,
        )]
    return []


AGENTS: list[Agent] = [
    Agent(
        key="social_proof",
        name="Especialista en prueba social",
        principle="Prueba social",
        source="Cialdini, «Influence»",
        pillar="prueba_social",
        focus="Conseguir y mostrar evidencia de que otros ya confiaron en vos.",
        analyze=_social_proof,
    ),
    Agent(
        key="authority",
        name="Especialista en autoridad percibida",
        principle="Autoridad",
        source="Cialdini, «Influence»",
        pillar="identidad",
        focus="Señales verificables de que sos quien decís ser y sabés de lo tuyo.",
        analyze=_authority,
    ),
    Agent(
        key="reciprocity",
        name="Especialista en reciprocidad",
        principle="Reciprocidad",
        source="Cialdini, «Influence»",
        pillar="contenido",
        focus="Dar valor antes de pedir la compra.",
        analyze=_reciprocity,
    ),
    Agent(
        key="consistency",
        name="Especialista en coherencia de marca",
        principle="Compromiso y coherencia",
        source="Cialdini, «Influence»",
        pillar="red",
        focus="Que la marca se vea igual y conectada en todos lados.",
        analyze=_consistency,
    ),
    Agent(
        key="liking",
        name="Especialista en trato y cercanía",
        principle="Simpatía",
        source="Cialdini, «Influence»",
        pillar="respuesta",
        focus="Cómo y cuán rápido tratás a quien te escribe.",
        analyze=_liking,
    ),
    Agent(
        key="scarcity",
        name="Especialista en escasez honesta",
        principle="Escasez",
        source="Cialdini, «Influence»",
        pillar="respuesta",
        focus="Comunicar límites reales sin fabricar urgencia falsa.",
        analyze=_scarcity,
    ),
    Agent(
        key="mere_exposure",
        name="Especialista en presencia sostenida",
        principle="Mera exposición",
        source="Zajonc, 1968",
        pillar="red",
        focus="Constancia: aparecer seguido en pocos canales.",
        analyze=_mere_exposure,
    ),
]


def run_agents(pillars: dict[str, Any], context: dict[str, Any]) -> list[Recommendation]:
    """Every agent inspects the real pillar data and speaks only if it has
    something grounded to say. Ordered by the size of the gap they close."""
    recommendations: list[Recommendation] = []
    for agent in AGENTS:
        try:
            recommendations.extend(agent.analyze(pillars, context))
        except Exception:  # noqa: BLE001 -- one agent must not break the panel
            continue
    return sorted(recommendations, key=lambda r: -r.impact_points)
