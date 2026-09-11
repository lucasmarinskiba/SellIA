"""How a bot must behave on each platform, as opposed to what it wants to say.

A reply that works in a WhatsApp chat is wrong in a MercadoLibre question: ML
moderates pre-sale messages and strips or penalises contact details and external
links, so a bot that helpfully answers "escribime al +54 9 11…" gets the seller's
listing sanctioned. Instagram DMs are short and informal; email needs a subject
and a sign-off; a Telegram bot can use markdown that Instagram would print
literally.

None of that is derivable from the connector classes — it is platform policy and
convention, real-world knowledge — so it is declared here as data, with the
reason written next to each rule. What IS derivable (whether SellIA can even
send a message there) stays in platform_commerce.capabilities and is read, never
repeated.

The output is a prompt fragment plus a hard character budget. The fragment is
advice to the model; the budget is enforced in code, because "be brief" is not a
guarantee and a truncated-by-the-platform reply reads as a broken bot.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass(frozen=True)
class Playbook:
    """The rules of engagement on one platform."""

    platform: str
    label: str
    #: Hard cap applied in code before sending.
    max_chars: int
    #: Whether a link in the reply is acceptable on this surface.
    allow_links: bool
    #: Whether sharing phone/email/address is acceptable BEFORE a sale closes.
    allow_contact_details: bool
    #: Formatting the surface actually renders.
    formatting: str
    #: How people write here.
    register: str
    #: Platform-specific rules, each one a sentence for the prompt.
    rules: list[str] = field(default_factory=list)
    #: Why this matters for the seller, shown in the UI.
    why: str = ""


#: Conservative by design: when a platform's policy is ambiguous, the stricter
#: reading is used, because the cost of being wrong is the seller's account.
PLAYBOOKS: dict[str, Playbook] = {
    "mercadolibre": Playbook(
        platform="mercadolibre",
        label="MercadoLibre",
        max_chars=900,
        allow_links=False,
        allow_contact_details=False,
        formatting="plain",
        register="formal y concreto",
        rules=[
            "Nunca des teléfono, email, redes, dirección ni links: MercadoLibre moderá los "
            "mensajes previos a la venta y sancioná la publicación que intenta sacar al "
            "comprador de la plataforma.",
            "No sugieras pagar por fuera de MercadoLibre en ningún caso.",
            "Respondé la pregunta concreta primero, en una o dos frases, y después agregá el dato útil.",
            "Si el comprador pide algo que no podés confirmar (stock exacto, fecha de entrega), "
            "decilo en vez de estimar.",
        ],
        why="Compartir contacto o links antes de la venta es causa de sanción a la publicación.",
    ),
    "instagram": Playbook(
        platform="instagram",
        label="Instagram",
        max_chars=900,
        allow_links=True,
        allow_contact_details=True,
        formatting="plain",
        register="cercano, como un DM entre personas",
        rules=[
            "Escribí corto: en un DM, un bloque largo no se lee.",
            "Una sola pregunta por mensaje, para que la conversación siga.",
            "Los links en DM reducen el alcance del perfil: mandá uno solo cuando hace falta de verdad.",
            "No uses markdown: Instagram lo muestra literal (los asteriscos se ven).",
        ],
        why="El DM es conversación, no catálogo: los mensajes largos se abandonan.",
    ),
    "whatsapp": Playbook(
        platform="whatsapp",
        label="WhatsApp",
        max_chars=1000,
        allow_links=True,
        allow_contact_details=True,
        formatting="whatsapp",
        register="cercano y directo",
        rules=[
            "Mensajes cortos, como los escribiría una persona desde el teléfono.",
            "Negrita con *asteriscos simples*, que es lo que WhatsApp renderiza.",
            "Si la respuesta necesita varios datos, usá una lista corta con guiones.",
            "Cerrá con una pregunta o un paso concreto: en WhatsApp es donde se cierra la venta.",
        ],
        why="Es el canal donde más se cierra: cada mensaje debería acercar la decisión.",
    ),
    "telegram": Playbook(
        platform="telegram",
        label="Telegram",
        max_chars=1200,
        allow_links=True,
        allow_contact_details=True,
        formatting="markdown",
        register="informal y claro",
        rules=[
            "Podés usar markdown simple (*negrita*, `código`): Telegram lo renderiza.",
            "Sirve para explicar con listas cuando el producto lo necesita.",
        ],
        why="Soporta formato, así que una explicación estructurada se lee bien.",
    ),
    "messenger": Playbook(
        platform="messenger",
        label="Messenger",
        max_chars=900,
        allow_links=True,
        allow_contact_details=True,
        formatting="plain",
        register="cercano",
        rules=[
            "Mensajes cortos, sin markdown.",
            "Si el comprador escribió desde un anuncio, retomá eso que vio en vez de empezar de cero.",
        ],
        why="Llega mucha consulta de anuncios: retomar el anuncio sube la conversión.",
    ),
    "email": Playbook(
        platform="email",
        label="Email",
        max_chars=2500,
        allow_links=True,
        allow_contact_details=True,
        formatting="email",
        register="profesional pero humano",
        rules=[
            "Abrí con una línea que diga de qué se trata, sin 'Espero que estés muy bien'.",
            "Podés dar más contexto que en un chat, pero no más de lo necesario.",
            "Cerrá con una firma y un próximo paso claro.",
            "No uses emojis salvo que el cliente los haya usado primero.",
        ],
        why="Es el único canal que no depende de un algoritmo ajeno: conviene cuidarlo.",
    ),
    "webchat": Playbook(
        platform="webchat",
        label="Chat del sitio",
        max_chars=900,
        allow_links=True,
        allow_contact_details=True,
        formatting="plain",
        register="atento y rápido",
        rules=[
            "Quien escribe acá ya está mirando tu producto: respondé la duda que lo frena, no el catálogo.",
            "Si podés, nombrá la página donde está parado.",
        ],
        why="Es la consulta más caliente que existe: ya está en tu sitio.",
    ),
    "tiktok": Playbook(
        platform="tiktok",
        label="TikTok",
        max_chars=500,
        allow_links=False,
        allow_contact_details=False,
        formatting="plain",
        register="muy informal y breve",
        rules=[
            "Dos o tres frases como máximo: es una respuesta de comentario, no un mensaje.",
            "No pongas links ni contacto: TikTok restringe los mensajes que sacan al usuario de la app.",
            "Invitá a seguir la conversación por el canal que el vendedor ya usa.",
        ],
        why="Los comentarios son públicos y muy cortos; los links se penalizan.",
    ),
    "twitter": Playbook(
        platform="twitter",
        label="X / Twitter",
        max_chars=270,
        allow_links=True,
        allow_contact_details=False,
        formatting="plain",
        register="directo y breve",
        rules=[
            "Una idea por respuesta: hay 280 caracteres y el corte se ve.",
            "Si el tema necesita más, ofrecé pasar a mensaje privado.",
        ],
        why="El límite es duro: una respuesta cortada por la plataforma parece un bot roto.",
    ),
    "threads": Playbook(
        platform="threads",
        label="Threads",
        max_chars=480,
        allow_links=True,
        allow_contact_details=False,
        formatting="plain",
        register="conversacional",
        rules=["Respuestas breves, sin markdown."],
        why="Conversación pública y corta, ligada a tu Instagram.",
    ),
    "linkedin": Playbook(
        platform="linkedin",
        label="LinkedIn",
        max_chars=1200,
        allow_links=True,
        allow_contact_details=True,
        formatting="plain",
        register="profesional, sin jerga de ventas",
        rules=[
            "Hablás con alguien que decide por su empresa: foco en el problema de negocio, no en features.",
            "Nada de urgencia falsa ni descuentos por tiempo limitado: acá queman la credibilidad.",
            "Si corresponde, proponé una llamada corta en vez de seguir escribiendo.",
        ],
        why="Es B2B: la decisión es racional y el historial queda a la vista.",
    ),
    "shopify": Playbook(
        platform="shopify",
        label="Shopify",
        max_chars=1500,
        allow_links=True,
        allow_contact_details=True,
        formatting="plain",
        register="claro y servicial",
        rules=["Es tu propia tienda: podés dar links a tus productos y a tu política de envíos."],
        why="Tienda propia: ninguna regla ajena limita lo que podés responder.",
    ),
    "woocommerce": Playbook(
        platform="woocommerce",
        label="WooCommerce",
        max_chars=1500,
        allow_links=True,
        allow_contact_details=True,
        formatting="plain",
        register="claro y servicial",
        rules=["Es tu propio sitio: podés enlazar productos, envíos y devoluciones."],
        why="Tienda propia: sin restricciones de plataforma.",
    ),
    "amazon": Playbook(
        platform="amazon",
        label="Amazon",
        max_chars=900,
        allow_links=False,
        allow_contact_details=False,
        formatting="plain",
        register="formal y escueto",
        rules=[
            "No incluyas links externos, contacto ni pedidos de reseña: Amazon lo prohíbe en la "
            "mensajería con compradores.",
            "Limitate a responder sobre el pedido o el producto.",
        ],
        why="La mensajería de Amazon está estrictamente moderada: un link puede costar la cuenta.",
    ),
    "etsy": Playbook(
        platform="etsy",
        label="Etsy",
        max_chars=900,
        allow_links=False,
        allow_contact_details=False,
        formatting="plain",
        register="cálido y personal",
        rules=[
            "No saques la conversación de Etsy ni pidas pagar por fuera: es motivo de suspensión.",
            "El comprador de Etsy valora el detalle hecho a mano: contá el cómo, no solo el precio.",
        ],
        why="Etsy prohíbe desviar la venta fuera de la plataforma.",
    ),
    "facebook_marketplace": Playbook(
        platform="facebook_marketplace",
        label="Facebook Marketplace",
        max_chars=800,
        allow_links=True,
        allow_contact_details=True,
        formatting="plain",
        register="informal y rápido",
        rules=[
            "Mucha consulta es '¿sigue disponible?': respondé eso primero y en una línea.",
            "Acordá lugar y horario concretos si la entrega es en mano.",
        ],
        why="Son compradores locales que deciden rápido: la primera línea define si siguen.",
    ),
    "hotmart": Playbook(
        platform="hotmart",
        label="Hotmart",
        max_chars=1200,
        allow_links=True,
        allow_contact_details=True,
        formatting="plain",
        register="claro y orientado al resultado",
        rules=[
            "Se vende una transformación, no un archivo: hablá del resultado que consigue la persona.",
            "Sé explícito con lo que incluye y lo que no, para evitar reembolsos.",
        ],
        why="En infoproductos, la expectativa mal puesta vuelve como reembolso.",
    ),
}

#: Used for any platform without its own entry, so a new connector behaves
#: conservatively instead of unpredictably.
DEFAULT_PLAYBOOK = Playbook(
    platform="default",
    label="Genérico",
    max_chars=900,
    allow_links=False,
    allow_contact_details=False,
    formatting="plain",
    register="claro y respetuoso",
    rules=[
        "No incluyas links ni datos de contacto: no se sabe si esta plataforma los permite.",
        "Respondé en pocas frases.",
    ],
    why="Sin reglas conocidas para esta plataforma, se aplica lo más conservador.",
)


def for_platform(platform: str) -> Playbook:
    return PLAYBOOKS.get((platform or "").lower(), DEFAULT_PLAYBOOK)


FORMATTING_HINTS = {
    "plain": "Escribí en texto plano. No uses markdown ni asteriscos: se ven literales.",
    "markdown": "Podés usar markdown simple (*negrita*, `código`).",
    "whatsapp": "Para resaltar usá *un asterisco por lado*, que es lo que WhatsApp renderiza.",
    "email": "Podés usar párrafos y una lista corta. Cerrá con una firma.",
}


def prompt_fragment(platform: str, *, language: Optional[str] = None) -> str:
    """The platform's rules, written as instructions for the reply model."""
    book = for_platform(platform)
    lines = [
        f"REGLAS DE {book.label.upper()} (la plataforma donde estás respondiendo):",
        f"- Tono: {book.register}.",
        f"- Largo máximo: {book.max_chars} caracteres. Si no entra, priorizá responder la pregunta.",
        f"- {FORMATTING_HINTS.get(book.formatting, FORMATTING_HINTS['plain'])}",
    ]
    if not book.allow_links:
        lines.append("- No incluyas ningún link.")
    if not book.allow_contact_details:
        lines.append("- No incluyas teléfono, email, redes ni dirección.")
    lines += [f"- {rule}" for rule in book.rules]
    if language:
        lines.append(f"- Respondé en {language}.")
    return "\n".join(lines)


def describe(platform: str) -> dict[str, Any]:
    """The playbook as the UI shows it, so the seller sees the rules being applied."""
    book = for_platform(platform)
    return {
        "platform": book.platform,
        "label": book.label,
        "max_chars": book.max_chars,
        "allow_links": book.allow_links,
        "allow_contact_details": book.allow_contact_details,
        "formatting": book.formatting,
        "register": book.register,
        "rules": list(book.rules),
        "why": book.why,
        "is_default": book.platform == "default",
    }


#: A phone number as people actually write one: eight or more digits with
#: spaces, dashes, dots or parentheses between them. A single run of 8 digits is
#: not enough on its own — "+54 9 11 2345 6789" has no run longer than four, and
#: that is exactly the form a bot would hand a buyer.
_PHONE_RE = re.compile(r"(?:\+?\d[\s().\-]{0,2}){8,}")
#: An email, loosely: enough to catch one, not to validate it.
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
#: Anything that takes the buyer off the platform.
_LINK_RE = re.compile(r"(https?://|www\.|wa\.me/|t\.me/|instagram\.com/|bit\.ly/)", re.IGNORECASE)


def violations(platform: str, reply: str) -> list[str]:
    """What in this reply breaks the platform's rules.

    Checked after generation, not only asked for in the prompt: the model
    complies most of the time, and "most of the time" is not a policy.
    """
    book = for_platform(platform)
    found: list[str] = []

    if not book.allow_links and _LINK_RE.search(reply):
        found.append("incluye un link y esta plataforma no lo permite")
    if not book.allow_contact_details:
        if _EMAIL_RE.search(reply):
            found.append("incluye lo que parece un email")
        for candidate in _PHONE_RE.findall(reply):
            digits = "".join(ch for ch in candidate if ch.isdigit())
            if len(digits) >= 8:
                found.append("incluye lo que parece un teléfono")
                break
    if len(reply) > book.max_chars:
        found.append(f"supera el largo máximo ({len(reply)} de {book.max_chars} caracteres)")
    return found


def enforce(platform: str, reply: str) -> tuple[str, list[str]]:
    """Return the reply trimmed to the platform's budget, plus what was wrong.

    Only the length is repaired automatically — cutting at a sentence boundary so
    the message still reads as finished. A reply carrying a forbidden link or
    phone number is NOT silently edited: stripping it could change what was
    promised to the buyer, so the caller decides (the auto-reply path holds it
    for a human).
    """
    problems = violations(platform, reply)
    book = for_platform(platform)
    trimmed = reply
    if len(reply) > book.max_chars:
        cut = reply[: book.max_chars]
        for stop in (".\n", ". ", "\n", " "):
            index = cut.rfind(stop)
            if index > book.max_chars * 0.6:
                cut = cut[: index + 1]
                break
        trimmed = cut.rstrip()
    return trimmed, problems


def blocking_problems(platform: str, reply: str) -> list[str]:
    """Problems that must stop the message from being sent as-is."""
    return [
        problem
        for problem in violations(platform, reply)
        if "largo máximo" not in problem  # length is repaired, not blocking
    ]
