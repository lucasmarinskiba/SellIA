"""HarveyService — profile, prospects, drafting, approval and reply handling for one business."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.businesses.models import Business
from app.domains.harvey.gate import (
    UNTRUSTED_RULE,
    GateResult,
    do_not_contact_entry,
    do_not_contact_match,
    fence,
    normalize_do_not_contact,
    pre_send_check,
)
from app.domains.harvey.llm import ask_json, llm_available
from app.domains.harvey.models import (
    HarveyOutboxItem,
    HarveyProfile,
    HarveyProspect,
    HarveyReply,
    OutboxStatus,
    ProspectStatus,
    ReplyClass,
)

logger = get_logger(__name__)

# Fields a caller may change through update_profile.
PROFILE_FIELDS = frozenset({
    "is_enabled", "persona_name", "persona_role", "tone", "language", "offer", "benefits",
    "icp", "postal_address", "opt_out_line", "do_not_contact", "max_daily_drafts",
})

_OPT_OUT_RE = re.compile(
    r"\b(no gracias|no me (escribas|contactes|envíes|envies|mandes)|dame de baja|dar de baja|"
    r"darme de baja|desuscrib\w*|baja de (la )?lista|no (me )?interesa más|"
    r"unsubscribe|remove me|stop (emailing|contacting)|no thanks|do not contact)\b",
    re.IGNORECASE,
)


class HarveyError(Exception):
    """Business-rule failure; ``status_code`` is what the router should answer."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _system_prompt(business: Business, profile: HarveyProfile) -> str:
    benefits = "\n".join(f"- {b}" for b in (profile.benefits or []))
    return (
        f"Sos {profile.persona_name or 'un representante'}, {profile.persona_role} en {business.name}. "
        f"Tono: {profile.tone}. Idioma: {profile.language}.\n"
        f"Qué ofrece {business.name}: {profile.offer or business.description or '(sin descripción)'}\n"
        f"Beneficios:\n{benefits or '- (sin lista)'}\n\n"
        "REGLAS ESTRICTAS DEL EMAIL: texto plano, sin links, sin emojis, sin asuntos en mayúsculas, "
        "sin promesas de resultados, sin urgencia falsa. Cada afirmación sobre el prospecto debe salir "
        "de los HECHOS; si un dato no está listado, no lo sabés: no inventes rondas de inversión, "
        "contactos en común, métricas ni nada parecido. Siempre respondés SOLO con un objeto JSON."
    )


class HarveyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── profile ───────────────────────────────────────────────────────────
    async def get_or_create_profile(self, business: Business) -> HarveyProfile:
        """A business's profile, created on first use from what SellIA already knows."""
        profile = (
            await self.db.execute(select(HarveyProfile).where(HarveyProfile.business_id == business.id))
        ).scalar_one_or_none()
        if profile is not None:
            return profile
        profile = HarveyProfile(
            business_id=business.id,
            offer=(business.description or "")[:2000],
            benefits=[],
            icp={},
            do_not_contact=[],
        )
        self.db.add(profile)
        try:
            await self.db.commit()
        except IntegrityError:
            # A concurrent request created it first (unique business_id).
            await self.db.rollback()
            return (
                await self.db.execute(select(HarveyProfile).where(HarveyProfile.business_id == business.id))
            ).scalar_one()
        await self.db.refresh(profile)
        return profile

    async def update_profile(self, business: Business, changes: dict[str, Any]) -> HarveyProfile:
        profile = await self.get_or_create_profile(business)
        for key, value in changes.items():
            if key not in PROFILE_FIELDS:
                continue
            if key == "do_not_contact":
                try:
                    value = normalize_do_not_contact(list(value or []))
                except ValueError as e:
                    raise HarveyError(str(e), 422) from e
            setattr(profile, key, value)
        await self.db.commit()
        await self.db.refresh(profile)
        return profile

    # ── prospects ─────────────────────────────────────────────────────────
    async def add_prospects(
        self, business_id: uuid.UUID, profile: HarveyProfile, items: list[dict[str, Any]]
    ) -> tuple[list[HarveyProspect], list[dict[str, str]]]:
        created: list[HarveyProspect] = []
        skipped: list[dict[str, str]] = []
        existing = set(
            (
                await self.db.execute(
                    select(HarveyProspect.email).where(HarveyProspect.business_id == business_id)
                )
            ).scalars()
        )
        for item in items:
            email = str(item.get("email") or "").strip().lower()
            if email in existing:
                skipped.append({"email": email, "reason": "ya existe"})
                continue
            blocked = do_not_contact_match(email, profile.do_not_contact or [])
            if blocked:
                skipped.append({"email": email, "reason": f"en la lista de no contactar ({blocked})"})
                continue
            prospect = HarveyProspect(business_id=business_id, **{**item, "email": email})
            self.db.add(prospect)
            existing.add(email)
            created.append(prospect)
        await self.db.commit()
        for p in created:
            await self.db.refresh(p)
        return created, skipped

    async def get_prospect(self, business_id: uuid.UUID, prospect_id: uuid.UUID) -> HarveyProspect:
        """Scoped by business: another business's prospect id is a 404, not a hit."""
        prospect = (
            await self.db.execute(
                select(HarveyProspect).where(
                    HarveyProspect.id == prospect_id, HarveyProspect.business_id == business_id
                )
            )
        ).scalar_one_or_none()
        if prospect is None:
            raise HarveyError("Prospecto no encontrado", 404)
        return prospect

    async def list_prospects(
        self, business_id: uuid.UUID, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[HarveyProspect]:
        q = select(HarveyProspect).where(HarveyProspect.business_id == business_id)
        if status:
            q = q.where(HarveyProspect.status == status)
        q = q.order_by(HarveyProspect.created_at.desc()).limit(limit).offset(offset)
        return list((await self.db.execute(q)).scalars())

    # ── drafting ──────────────────────────────────────────────────────────
    async def _drafts_today(self, business_id: uuid.UUID) -> int:
        start = _utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return (
            await self.db.execute(
                select(func.count())
                .select_from(HarveyOutboxItem)
                .where(HarveyOutboxItem.business_id == business_id, HarveyOutboxItem.created_at >= start)
            )
        ).scalar_one()

    @staticmethod
    def _facts(prospect: HarveyProspect) -> str:
        if prospect.is_company_inbox:
            lines = [f"- Nombre: desconocido (casilla general de la empresa, {prospect.email})"]
        else:
            lines = [f"- Nombre: {prospect.full_name() or 'desconocido'}"]
            if prospect.title:
                lines.append(f"- Cargo: {prospect.title}")
        if prospect.company:
            lines.append(f"- Empresa: {prospect.company}")
        if prospect.industry:
            lines.append(f"- Rubro: {prospect.industry}")
        if prospect.website:
            lines.append(f"- Sitio: {prospect.website}")
        for signal in (prospect.signals or [])[:3]:
            if isinstance(signal, dict):
                lines.append(f"- Señal ({signal.get('type', 'señal')}): {signal.get('detail', '')}")
        if prospect.notes:
            lines.append(f"- Notas de investigación: {prospect.notes}")
        return "\n".join(lines)

    @staticmethod
    def _footer(profile: HarveyProfile) -> str:
        parts = [p.strip() for p in (profile.postal_address, profile.opt_out_line) if p and p.strip()]
        return "\n\n" + "\n".join(parts) if parts else ""

    def _gate(self, profile: HarveyProfile, prospect: HarveyProspect, subject: str, body: str) -> GateResult:
        return pre_send_check(
            prospect.email,
            subject,
            body,
            prospect_email=prospect.email,
            email_status=prospect.email_status,
            do_not_contact=profile.do_not_contact or [],
            opt_out_line=profile.opt_out_line or "",
            postal_address=profile.postal_address or "",
        )

    async def draft_first_email(
        self, business: Business, profile: HarveyProfile, prospect: HarveyProspect
    ) -> HarveyOutboxItem:
        existing = (
            await self.db.execute(
                select(HarveyOutboxItem).where(
                    HarveyOutboxItem.business_id == business.id,
                    HarveyOutboxItem.prospect_id == prospect.id,
                    HarveyOutboxItem.step == 1,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return existing
        if prospect.status in (ProspectStatus.OPTED_OUT.value, ProspectStatus.REPLIED.value):
            raise HarveyError(f"El prospecto está en estado '{prospect.status}'", 409)
        if await self._drafts_today(business.id) >= profile.max_daily_drafts:
            raise HarveyError("Se alcanzó el máximo de borradores diarios de este negocio", 429)
        if not llm_available():
            raise HarveyError("El redactor no está disponible (falta la API key del modelo)", 503)

        inbox_rule = (
            "\n- Va a la casilla general: no uses nombre propio, abrí con un saludo al equipo."
            if prospect.is_company_inbox
            else ""
        )
        prompt = f"""Escribí UN email en frío (el primer contacto) para esta persona.

HECHOS — todo lo que sabés. Cada afirmación sobre el prospecto tiene que salir de acá:
{fence(self._facts(prospect), "investigación del prospecto")}

{UNTRUSTED_RULE}

Requisitos:
- Menos de 75 palabras. Una observación específica de los HECHOS y una pregunta. Sin pitch.
- Texto final real, sin variables tipo {{{{nombre}}}}.
- Asunto en minúsculas, 2 a 5 palabras.
- No incluyas dirección postal ni línea de baja: se agregan solos.{inbox_rule}

Respondé SOLO con JSON: {{"subject": "...", "body": "..."}}"""
        result = await ask_json(_system_prompt(business, profile), prompt)
        subject = str((result or {}).get("subject") or "").strip()[:120]
        body = str((result or {}).get("body") or "").strip()[:2000]
        if not subject or not body:
            raise HarveyError("El modelo no devolvió un borrador utilizable; probá de nuevo", 502)

        body += self._footer(profile)
        gate = self._gate(profile, prospect, subject, body)
        item = HarveyOutboxItem(
            business_id=business.id,
            prospect_id=prospect.id,
            step=1,
            to_email=prospect.email,
            subject=subject,
            body=body,
            status=OutboxStatus.PENDING_REVIEW.value if gate.ok else OutboxStatus.BLOCKED.value,
            gate_reasons=gate.reasons,
        )
        self.db.add(item)
        prospect.status = ProspectStatus.DRAFTED.value
        await self.db.commit()
        await self.db.refresh(item)
        return item

    # ── outbox ────────────────────────────────────────────────────────────
    async def list_outbox(
        self, business_id: uuid.UUID, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[HarveyOutboxItem]:
        q = select(HarveyOutboxItem).where(HarveyOutboxItem.business_id == business_id)
        if status:
            q = q.where(HarveyOutboxItem.status == status)
        q = q.order_by(HarveyOutboxItem.created_at.desc()).limit(limit).offset(offset)
        return list((await self.db.execute(q)).scalars())

    async def decide(
        self,
        business_id: uuid.UUID,
        profile: HarveyProfile,
        item_id: uuid.UUID,
        user_id: uuid.UUID,
        approve: bool,
    ) -> HarveyOutboxItem:
        item = (
            await self.db.execute(
                select(HarveyOutboxItem).where(
                    HarveyOutboxItem.id == item_id, HarveyOutboxItem.business_id == business_id
                )
            )
        ).scalar_one_or_none()
        if item is None:
            raise HarveyError("Borrador no encontrado", 404)
        if item.status != OutboxStatus.PENDING_REVIEW.value:
            raise HarveyError(f"El borrador está en estado '{item.status}'", 409)

        if approve:
            prospect = await self.get_prospect(business_id, item.prospect_id)
            # Re-check at approval time: the do-not-contact list or the prospect may
            # have changed since the draft was written.
            gate = self._gate(profile, prospect, item.subject, item.body)
            reasons = list(gate.reasons)
            if prospect.status in (ProspectStatus.OPTED_OUT.value, ProspectStatus.REPLIED.value):
                reasons.append(f"el prospecto está en estado '{prospect.status}'")
            if reasons:
                item.status = OutboxStatus.BLOCKED.value
                item.gate_reasons = reasons
                await self.db.commit()
                await self.db.refresh(item)
                return item
            item.status = OutboxStatus.APPROVED.value
        else:
            item.status = OutboxStatus.REJECTED.value
        item.decided_by = user_id
        item.decided_at = _utcnow()
        await self.db.commit()
        await self.db.refresh(item)
        return item

    # ── replies ───────────────────────────────────────────────────────────
    async def record_reply(
        self, business: Business, profile: HarveyProfile, prospect: HarveyProspect, body: str
    ) -> HarveyReply:
        body = (body or "").strip()[:5000]
        classification, needs_human, answer = await self._classify(business, profile, prospect, body)

        reply = HarveyReply(
            business_id=business.id,
            prospect_id=prospect.id,
            body=body,
            classification=classification.value,
            needs_human=needs_human,
            draft_answer=answer,
        )
        self.db.add(reply)
        if classification in (ReplyClass.OPT_OUT, ReplyClass.NOT_INTERESTED):
            prospect.status = ProspectStatus.OPTED_OUT.value
            if classification is ReplyClass.OPT_OUT:
                entry = do_not_contact_entry(prospect.email)
                current = list(profile.do_not_contact or [])
                if entry and entry not in current:
                    profile.do_not_contact = current + [entry]
        else:
            prospect.status = ProspectStatus.REPLIED.value
        await self.db.commit()
        await self.db.refresh(reply)
        return reply

    async def _classify(
        self, business: Business, profile: HarveyProfile, prospect: HarveyProspect, body: str
    ) -> tuple[ReplyClass, bool, str]:
        # Opt-outs are decided in code, never left to the model: a missed one is a legal problem.
        if _OPT_OUT_RE.search(body):
            return ReplyClass.OPT_OUT, False, ""

        prompt = f"""{prospect.full_name() or prospect.email} respondió a nuestro email. Clasificá la respuesta y,
si corresponde, redactá una respuesta corta (menos de 60 palabras) que lleve la conversación hacia
{("una llamada" if profile.offer else "el próximo paso")}.

{fence(body, "respuesta del prospecto")}

{UNTRUSTED_RULE}

Clases: interested, objection, question, not_interested, handoff.
Usá handoff si pide contrato, precios especiales, algo legal, o si no podés responder solo con los datos del negocio.
Respondé SOLO con JSON: {{"classification": "...", "answer": "..."}}"""
        result = await ask_json(_system_prompt(business, profile), prompt, max_tokens=500)
        raw = str((result or {}).get("classification") or "").strip().lower()
        try:
            classification = ReplyClass(raw)
        except ValueError:
            # Model unavailable or off-script: a person reads it.
            return ReplyClass.HANDOFF, True, ""
        answer = str((result or {}).get("answer") or "").strip()[:1000]
        needs_human = classification is ReplyClass.HANDOFF
        if classification in (ReplyClass.NOT_INTERESTED, ReplyClass.HANDOFF):
            answer = ""
        return classification, needs_human, answer

    async def list_replies(self, business_id: uuid.UUID, limit: int = 100, offset: int = 0) -> list[HarveyReply]:
        q = (
            select(HarveyReply)
            .where(HarveyReply.business_id == business_id)
            .order_by(HarveyReply.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list((await self.db.execute(q)).scalars())
