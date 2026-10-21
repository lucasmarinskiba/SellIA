"""Let the business owner answer webhook-token rotation proposals in the SellIA assistant chat.

The proposals are ``Recommendation`` rows (see ``token_rotation``). The owner can already answer
them through the recommendations API; this lets them do it by talking to the assistant.

Rotating a token breaks the webhook URL set up on the external platform, so the chat does not hand
that decision to the language model: the message is read by plain rules, and anything that is not
clearly a yes or a no only gets the proposals listed again.

* Asking about it ("quiero rotar el token", "ver rotaciones pendientes") lists the pending
  proposals with what accepting means. Nothing changes.
* A clear **no** ("rechazar", "dejalo como está", "más adelante") dismisses them. Always safe.
* A clear **yes** rotates, but only when the owner has just seen the proposal (the previous
  assistant message was the listing) or says so explicitly together with the topic
  ("acepto la rotación del token"). A bare "sí" out of the blue never rotates anything.
* With several proposals the owner names the channel or says "todas".
* The new token is never written in the chat (the history is stored); the reply says where to
  find the new URL.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.alerts.models import Recommendation, RecommendationStatus
from app.domains.alerts.service import AlertService
from app.domains.businesses.models import Business
from app.domains.channels.models import ChannelConnection
from app.domains.channels.token_rotation import ROTATION_KIND, RotationNotPossible

#: Value of the ``action`` field of the assistant message that lists the proposals.
LISTING_ACTION = "ROTATION_PROPOSAL"


class Intent(str, Enum):
    NONE = "none"  # not about token rotation: the normal assistant answers
    LIST = "list"
    ACCEPT = "accept"
    REJECT = "reject"
    UNCLEAR = "unclear"  # about rotation, but yes/no is not clear


def _plain(text: str) -> str:
    """Lowercase without accents, so "sí"/"si" and "rotación"/"rotacion" match the same."""
    decomposed = unicodedata.normalize("NFD", text.lower())
    return "".join(ch for ch in decomposed if unicodedata.category(ch) != "Mn")


_TOPIC = re.compile(
    r"(rotacion|rotaciones|(token|webhook)\w*.*\b(rot[aeo]\w*|renov\w*|cambi\w*|actualiz\w*|nuevo)\b"
    r"|\b(rot[aeo]\w*|renov\w*|cambi\w*|actualiz\w*)\b.*\b(token|webhook)\w*)"
)
_REJECT_VERB = re.compile(
    r"\b(rechaz\w*|cancel\w*|ignor\w*|posterg\w*|despues|mas adelante|ahora no|todavia no|no quiero|no rotes|"
    r"deja\w*\s+(todo\s+)?(como|asi)|que siga igual)\b"
)
_REJECT_SHORT = re.compile(
    r"(^\W*no\b|\bno\W*$)"
)  # a short reply that starts or ends with "no"
_SHORT_REPLY_WORDS = (
    8  # "no"/"sí" only count in a reply this short, not inside a long sentence
)
_ACCEPT_EXPLICIT = re.compile(
    r"\b(acept\w*|aprueb\w*|aprob\w*|confirm\w*|autoriz\w*)\b"
)
_ACCEPT_SHORT = re.compile(
    r"\b(si|dale|ok|okay|adelante|hacelo|hazlo|procede|procedan?|de acuerdo)\b"
)
_ALL = re.compile(r"\b(todas|todos|ambas|ambos|las dos|los dos)\b")


def interpret(message: str, *, just_listed: bool) -> Intent:
    """What the owner means. ``just_listed``: the previous assistant message was the listing."""
    text = _plain(message)
    topic = bool(_TOPIC.search(text))
    if not topic and not just_listed:
        return Intent.NONE

    short_reply = len(text.split()) <= _SHORT_REPLY_WORDS
    reject = bool(_REJECT_VERB.search(text)) or (
        short_reply and bool(_REJECT_SHORT.search(text))
    )
    affirmative = _REJECT_VERB.sub(
        " ", text
    )  # "más adelante" is a no, its "adelante" is not a yes
    explicit = bool(_ACCEPT_EXPLICIT.search(affirmative))
    accept = explicit or (short_reply and bool(_ACCEPT_SHORT.search(affirmative)))

    if reject and accept:
        return Intent.UNCLEAR
    if reject:
        return Intent.REJECT
    if accept:
        # A yes counts when the proposal was just shown, or it names the topic and is explicit.
        if just_listed or (topic and explicit):
            return Intent.ACCEPT
        return Intent.LIST if topic else Intent.NONE
    return Intent.LIST if topic else Intent.NONE


@dataclass
class Reply:
    action: str
    response: str
    extra: dict = field(default_factory=dict)

    def as_result(self) -> dict:
        return {"action": self.action, "response": self.response, **self.extra}


@dataclass
class _Pending:
    rec: Recommendation
    channel_name: str
    platform: str


async def _pending(db: AsyncSession, business_id: uuid.UUID) -> list[_Pending]:
    recs = (
        (
            await db.execute(
                select(Recommendation)
                .where(
                    Recommendation.business_id == business_id,
                    Recommendation.status == RecommendationStatus.PENDING,
                    Recommendation.context_data["kind"].astext == ROTATION_KIND,
                )
                .order_by(Recommendation.created_at)
            )
        )
        .scalars()
        .all()
    )
    out: list[_Pending] = []
    for rec in recs:
        channel = (
            await db.execute(
                select(ChannelConnection).where(
                    ChannelConnection.id
                    == uuid.UUID(str(rec.context_data["channel_id"]))
                )
            )
        ).scalar_one_or_none()
        out.append(
            _Pending(
                rec=rec,
                channel_name=channel.name if channel else "(canal eliminado)",
                platform=str(rec.context_data.get("platform", "")),
            )
        )
    return out


async def count_pending(db: AsyncSession, business_id: uuid.UUID) -> int:
    return len(await _pending(db, business_id))


def _listing(pending: list[_Pending]) -> Reply:
    lines = "\n".join(
        f"  {i}. «{p.channel_name}» ({p.platform})" for i, p in enumerate(pending, 1)
    )
    text = (
        f"Tenés {len(pending)} renovación(es) de token de webhook pendiente(s):\n{lines}\n\n"
        "Si aceptás, se genera un token nuevo y la URL actual deja de funcionar: tenés que pegar la nueva "
        "en la plataforma (la ves en Canales) y, hasta entonces, no llegarán mensajes de ese canal. "
        "Si rechazás, no cambia nada y te lo vuelvo a proponer en 90 días.\n\n"
        "Decime «aceptar» o «rechazar»"
        + (" (y el nombre del canal, o «todas»)." if len(pending) > 1 else ".")
    )
    return Reply(LISTING_ACTION, text, {"pending_rotations": len(pending)})


def _select(pending: list[_Pending], message: str) -> list[_Pending] | None:
    """The proposals the owner refers to: the only one, "todas", or the channels they name."""
    if len(pending) == 1:
        return pending
    text = _plain(message)
    if _ALL.search(text):
        return pending
    named = [
        p for p in pending if _plain(p.channel_name) and _plain(p.channel_name) in text
    ]
    return named or None


async def handle(
    db: AsyncSession,
    *,
    user_id: uuid.UUID,
    business_id: uuid.UUID | None,
    message: str,
    previous_action: str | None,
) -> Reply | None:
    """The assistant's answer when ``message`` is about token rotation, else ``None``.

    ``None`` also when the business is not the user's: the normal assistant flow continues.
    """
    if business_id is None:
        return None
    just_listed = previous_action == LISTING_ACTION
    intent = interpret(message, just_listed=just_listed)
    if intent is Intent.NONE:
        return None

    owned = await db.execute(
        select(Business.id).where(
            Business.id == business_id, Business.user_id == user_id
        )
    )
    if owned.first() is None:
        return None

    pending = await _pending(db, business_id)
    if not pending:
        return Reply(
            "ROTATION_NONE",
            "No tenés renovaciones de token de webhook pendientes.",
            {"pending_rotations": 0},
        )

    if intent in (Intent.LIST, Intent.UNCLEAR):
        return _listing(pending)

    chosen = _select(pending, message)
    if chosen is None:
        return _listing(pending)

    service = AlertService(db)
    done: list[str] = []
    failed: list[str] = []
    for item in chosen:
        try:
            if intent is Intent.ACCEPT:
                await service.apply_recommendation(item.rec.id, user_id)
            else:
                await service.dismiss_recommendation(item.rec.id)
            done.append(f"«{item.channel_name}» ({item.platform})")
        except RotationNotPossible:
            await db.rollback()
            failed.append(f"«{item.channel_name}»")

    left = await count_pending(db, business_id)
    parts: list[str] = []
    if done and intent is Intent.ACCEPT:
        parts.append(
            "Listo, renové el token de "
            + ", ".join(done)
            + ". La URL anterior ya no funciona: copiá la nueva "
            "desde Canales y pegala en la plataforma para que vuelvan a llegar los mensajes."
        )
    elif done:
        parts.append(
            "Entendido, no cambio nada en "
            + ", ".join(done)
            + ". Te lo vuelvo a proponer en 90 días."
        )
    if failed:
        parts.append(
            "No pude renovar "
            + ", ".join(failed)
            + ": el canal ya no existe o está inactivo."
        )
    if left:
        parts.append(f"Todavía te quedan {left} pendiente(s).")
    action = "ROTATION_APPLIED" if intent is Intent.ACCEPT else "ROTATION_DISMISSED"
    return Reply(action, " ".join(parts), {"pending_rotations": left})
