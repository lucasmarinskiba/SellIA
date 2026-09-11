"""Everything a platform bot needs to know before it writes, assembled once.

Three sources were already being written by the seller and none of them reached
the reply: the platform's own rules (playbooks.py), the business configuration
from the Configuración screen (niche, languages, tastes, banned topics, voice
notes) and the bot's own row. A "smart" bot that ignores the instructions its
owner typed is not smart, so this module gathers them and produces the brief
that goes into the prompt.

It also answers two operational questions the reply path has to ask before
generating at all: is this bot within its hours, and may this particular reply
be sent on this platform.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.chatbots import playbooks

logger = get_logger(__name__)

LANGUAGE_NAMES = {
    "es": "español",
    "en": "inglés",
    "pt": "portugués",
    "it": "italiano",
    "fr": "francés",
    "de": "alemán",
}


@dataclass
class HoursVerdict:
    """Whether the bot may speak now, and what to say if not."""

    within_hours: bool
    reason: Optional[str] = None
    after_hours_message: Optional[str] = None


def check_hours(active_hours: Optional[dict[str, Any]], now: Optional[datetime] = None) -> HoursVerdict:
    """Is the current moment inside the bot's window?

    The window is stored in the seller's local time with an explicit UTC offset,
    because "9 to 21" means nothing without knowing whose 9. A window that wraps
    midnight (22 → 6) is supported: a night-shift business is a real business.
    """
    if not isinstance(active_hours, dict):
        return HoursVerdict(True)
    start, end = active_hours.get("from"), active_hours.get("to")
    if start is None or end is None:
        return HoursVerdict(True)
    try:
        start, end = int(start), int(end)
        offset = int(active_hours.get("utc_offset", 0))
    except (TypeError, ValueError):
        return HoursVerdict(True)
    if start == end:
        return HoursVerdict(True)  # a zero-width window means "no restriction"

    now = now or datetime.now(timezone.utc)
    local_hour = (now + timedelta(hours=offset)).hour
    inside = start < end and (start <= local_hour < end)
    inside = inside or (start > end and (local_hour >= start or local_hour < end))
    if inside:
        return HoursVerdict(True)
    return HoursVerdict(
        False,
        reason=f"fuera del horario configurado ({start}:00–{end}:00, UTC{offset:+d}); son las {local_hour}:00 ahí",
    )


@dataclass
class BotBrief:
    """The assembled instructions, plus what the reply path needs to decide."""

    platform: str
    prompt: str
    max_chars: int
    language: Optional[str]
    #: Names of the sources that really contributed, for the UI and the logs.
    sources: list[str]
    #: Configuration the seller filled in that could not be read.
    missing: list[str]


async def build_brief(
    db: AsyncSession,
    business_id: uuid.UUID,
    platform: str,
    bot: Any = None,
) -> BotBrief:
    """The brief for this platform's bot: platform rules + seller configuration."""
    book = playbooks.for_platform(platform)
    sources = ["reglas de la plataforma"]
    missing: list[str] = []
    sections: list[str] = []

    prefs = None
    try:
        from app.domains.preferences.models import SellerPreferences

        result = await db.execute(
            select(SellerPreferences).where(SellerPreferences.business_id == business_id)
        )
        prefs = result.scalar_one_or_none()
    except Exception as e:  # noqa: BLE001
        logger.warning("bot brief: seller preferences unreadable: %s", str(e)[:160])
        try:
            await db.rollback()
        except Exception:  # noqa: BLE001
            pass
        missing.append("preferencias del vendedor")

    language_name = None
    if prefs is not None:
        languages = [str(code) for code in (prefs.languages or [])]
        if languages:
            names = [LANGUAGE_NAMES.get(code, code) for code in languages]
            language_name = names[0]
            sections.append(
                "IDIOMAS: respondé en el idioma del comprador si es uno de estos: "
                + ", ".join(names)
                + f". Si no lo reconocés, usá {names[0]}."
            )
            sources.append("idiomas configurados")

        if prefs.banned_topics:
            # Hard constraint, stated as such: this is the seller forbidding
            # something in their own name.
            sections.append(
                "PROHIBIDO (el vendedor lo prohibió expresamente): nunca menciones ni ofrezcas "
                + "; ".join(str(topic) for topic in prefs.banned_topics)
                + ". Si te lo piden, decí que eso lo define una persona del equipo."
            )
            sources.append("temas prohibidos")

        if prefs.voice_notes:
            sections.append(f"CÓMO ESCRIBE ESTE VENDEDOR: {prefs.voice_notes}")
            sources.append("instrucciones de voz")

        if prefs.tastes:
            sections.append(
                "ESTILO QUE LE GUSTA AL VENDEDOR (usalo como referencia de tono, no lo citas): "
                + ", ".join(str(taste) for taste in prefs.tastes)
            )
            sources.append("gustos del vendedor")

        if prefs.autonomous_replies is False:
            # Surfaced rather than silently ignored: the caller decides.
            sections.append(
                "NOTA: el vendedor pidió revisar las respuestas antes de enviarlas."
            )

    if bot is not None and getattr(bot, "custom_instructions", None):
        sections.append(f"INSTRUCCIONES DEL VENDEDOR PARA ESTE CANAL: {bot.custom_instructions}")
        sources.append("instrucciones del canal")

    prompt = playbooks.prompt_fragment(platform, language=language_name)
    if sections:
        prompt += "\n\n" + "\n\n".join(sections)

    return BotBrief(
        platform=platform,
        prompt=prompt,
        max_chars=book.max_chars,
        language=language_name,
        sources=sources,
        missing=missing,
    )


@dataclass
class SendVerdict:
    """Whether a generated reply may be sent, after the platform's rules."""

    send: bool
    text: str
    problems: list[str]
    trimmed: bool


def vet_reply(platform: str, reply: str, *, hold_on_violation: bool = True) -> SendVerdict:
    """Check a generated reply against the platform before it goes out.

    Length is repaired (trimmed at a sentence boundary). A forbidden link or
    phone number is not edited out — removing it could change what the buyer was
    promised — so either the message is held for a human or it is sent with the
    problem recorded, depending on the bot's setting.
    """
    trimmed_text, problems = playbooks.enforce(platform, reply)
    blocking = playbooks.blocking_problems(platform, reply)
    if blocking and hold_on_violation:
        return SendVerdict(False, trimmed_text, problems, trimmed_text != reply)
    return SendVerdict(True, trimmed_text, problems, trimmed_text != reply)
