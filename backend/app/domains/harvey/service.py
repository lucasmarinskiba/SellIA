"""HarveyService — profile, prospects, drafting, approval and reply handling for one business."""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.businesses.models import Business
from app.domains.harvey import mailer
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
    "icp", "postal_address", "opt_out_line", "do_not_contact", "max_daily_drafts", "max_daily_sends",
})

# Sequence: step -> days to wait after the previous step was SENT before drafting it.
FOLLOWUP_DELAYS_DAYS = {2: 3, 3: 4}
MAX_STEP = 3
MAX_SEND_ATTEMPTS = 3
# A prospect in one of these states gets no more email, whatever is still queued.
STOP_STATUSES = (
    ProspectStatus.OPTED_OUT.value,
    ProspectStatus.REPLIED.value,
    ProspectStatus.BOUNCED.value,
)

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

    async def _outbox_item(self, business_id: uuid.UUID, prospect_id: uuid.UUID, step: int) -> HarveyOutboxItem | None:
        return (
            await self.db.execute(
                select(HarveyOutboxItem).where(
                    HarveyOutboxItem.business_id == business_id,
                    HarveyOutboxItem.prospect_id == prospect_id,
                    HarveyOutboxItem.step == step,
                )
            )
        ).scalar_one_or_none()

    @staticmethod
    def _step_prompt(step: int, prospect: HarveyProspect, previous: list[HarveyOutboxItem], inbox_rule: str) -> str:
        facts = fence(HarveyService._facts(prospect), "investigación del prospecto")
        if step == 1:
            return f"""Escribí UN email en frío (el primer contacto) para esta persona.

HECHOS — todo lo que sabés. Cada afirmación sobre el prospecto tiene que salir de acá:
{facts}

{UNTRUSTED_RULE}

Requisitos:
- Menos de 75 palabras. Una observación específica de los HECHOS y una pregunta. Sin pitch.
- Texto final real, sin variables tipo {{{{nombre}}}}.
- Asunto en minúsculas, 2 a 5 palabras.
- No incluyas dirección postal ni línea de baja: se agregan solos.{inbox_rule}

Respondé SOLO con JSON: {{"subject": "...", "body": "..."}}"""

        sent = "\n\n".join(f"[Email {p.step}]\nAsunto: {p.subject}\n{p.body}" for p in previous)
        if step == 2:
            goal = (
                "Es el seguimiento, 3 días después del primer email y sin respuesta. Usá un ángulo "
                "distinto al anterior y UN dato concreto tomado solo de lo que ofrece el negocio "
                "(oferta y beneficios del sistema). No inventes casos de clientes, cifras ni resultados. "
                "Menos de 75 palabras y una pregunta simple de responder."
            )
        else:
            goal = (
                "Es el último email (cierre amable). Menos de 40 palabras. Sin culpa ni presión: "
                "reconocé que quizá no es el momento y dejá la puerta abierta."
            )
        return f"""{goal}

HECHOS sobre el prospecto:
{facts}

{UNTRUSTED_RULE}

EMAILS YA ENVIADOS (no repitas lo mismo):
{sent}

Requisitos:
- Texto final real, sin variables tipo {{{{nombre}}}}. Empezá con un saludo breve.
- No repitas el asunto ni agregues "Re:": se reutiliza el del primer email.
- No incluyas dirección postal ni línea de baja: se agregan solos.{inbox_rule}

Respondé SOLO con JSON: {{"body": "..."}}"""

    async def draft_step(
        self, business: Business, profile: HarveyProfile, prospect: HarveyProspect, step: int = 1
    ) -> HarveyOutboxItem:
        """Draft email ``step`` (1-3) of the sequence and stage it for human review."""
        if not 1 <= step <= MAX_STEP:
            raise HarveyError(f"La secuencia tiene {MAX_STEP} pasos", 422)
        existing = await self._outbox_item(business.id, prospect.id, step)
        if existing is not None:
            return existing
        if prospect.status in STOP_STATUSES:
            raise HarveyError(f"El prospecto está en estado '{prospect.status}'", 409)

        previous: list[HarveyOutboxItem] = []
        for n in range(1, step):
            prev = await self._outbox_item(business.id, prospect.id, n)
            if prev is None or prev.status != OutboxStatus.SENT.value:
                raise HarveyError(f"El email {n} todavía no se envió", 409)
            previous.append(prev)

        if await self._drafts_today(business.id) >= profile.max_daily_drafts:
            raise HarveyError("Se alcanzó el máximo de borradores diarios de este negocio", 429)
        if not llm_available():
            raise HarveyError("El redactor no está disponible (falta la API key del modelo)", 503)

        inbox_rule = (
            "\n- Va a la casilla general: no uses nombre propio, abrí con un saludo al equipo."
            if prospect.is_company_inbox
            else ""
        )
        prompt = self._step_prompt(step, prospect, previous, inbox_rule)
        result = await ask_json(_system_prompt(business, profile), prompt)
        # Follow-ups keep the first subject: same thread, no fake "Re:".
        subject = previous[0].subject if previous else str((result or {}).get("subject") or "").strip()[:120]
        body = str((result or {}).get("body") or "").strip()[:2000]
        if not subject or not body:
            raise HarveyError("El modelo no devolvió un borrador utilizable; probá de nuevo", 502)

        body += self._footer(profile)
        gate = self._gate(profile, prospect, subject, body)
        item = HarveyOutboxItem(
            business_id=business.id,
            prospect_id=prospect.id,
            step=step,
            to_email=prospect.email,
            subject=subject,
            body=body,
            in_reply_to=previous[-1].message_id if previous else None,
            status=OutboxStatus.PENDING_REVIEW.value if gate.ok else OutboxStatus.BLOCKED.value,
            gate_reasons=gate.reasons,
        )
        self.db.add(item)
        if step == 1:
            prospect.status = ProspectStatus.DRAFTED.value
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def draft_first_email(
        self, business: Business, profile: HarveyProfile, prospect: HarveyProspect
    ) -> HarveyOutboxItem:
        return await self.draft_step(business, profile, prospect, 1)

    async def plan_followups(self, business: Business, profile: HarveyProfile) -> dict[str, int]:
        """Draft steps 2 and 3 for every prospect whose previous email went out long enough ago
        without an answer. Drafts still wait for human approval like any other."""
        now = _utcnow()
        drafted = skipped = 0
        for step, days in FOLLOWUP_DELAYS_DAYS.items():
            due_before = now - timedelta(days=days)
            sent_prev = (
                await self.db.execute(
                    select(HarveyOutboxItem, HarveyProspect)
                    .join(HarveyProspect, HarveyProspect.id == HarveyOutboxItem.prospect_id)
                    .where(
                        HarveyOutboxItem.business_id == business.id,
                        HarveyOutboxItem.step == step - 1,
                        HarveyOutboxItem.status == OutboxStatus.SENT.value,
                        HarveyOutboxItem.sent_at <= due_before,
                        HarveyProspect.status.not_in(STOP_STATUSES),
                    )
                    .order_by(HarveyOutboxItem.sent_at)
                )
            ).all()
            for _, prospect in sent_prev:
                if await self._outbox_item(business.id, prospect.id, step) is not None:
                    continue
                try:
                    await self.draft_step(business, profile, prospect, step)
                    drafted += 1
                except HarveyError as e:
                    if e.status_code in (429, 503):
                        # Cap reached or no model: every remaining prospect would fail the same way.
                        return {"drafted": drafted, "skipped": skipped, "stopped": e.status_code}
                    skipped += 1
        return {"drafted": drafted, "skipped": skipped, "stopped": 0}

    # ── outbox ────────────────────────────────────────────────────────────
    async def list_outbox(
        self, business_id: uuid.UUID, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[HarveyOutboxItem]:
        q = select(HarveyOutboxItem).where(HarveyOutboxItem.business_id == business_id)
        if status:
            q = q.where(HarveyOutboxItem.status == status)
        q = q.order_by(HarveyOutboxItem.created_at.desc()).limit(limit).offset(offset)
        return list((await self.db.execute(q)).scalars())

    async def get_outbox_item(self, business_id: uuid.UUID, item_id: uuid.UUID) -> HarveyOutboxItem:
        item = (
            await self.db.execute(
                select(HarveyOutboxItem).where(
                    HarveyOutboxItem.id == item_id, HarveyOutboxItem.business_id == business_id
                )
            )
        ).scalar_one_or_none()
        if item is None:
            raise HarveyError("Borrador no encontrado", 404)
        return item

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

    # ── sending ───────────────────────────────────────────────────────────
    async def _sent_today(self, business_id: uuid.UUID) -> int:
        start = _utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return (
            await self.db.execute(
                select(func.count())
                .select_from(HarveyOutboxItem)
                .where(
                    HarveyOutboxItem.business_id == business_id,
                    HarveyOutboxItem.status == OutboxStatus.SENT.value,
                    HarveyOutboxItem.sent_at >= start,
                )
            )
        ).scalar_one()

    async def require_account(self, business_id: uuid.UUID) -> mailer.EmailAccount:
        account = await mailer.get_email_account(self.db, business_id)
        if account is None:
            raise HarveyError(
                "Este negocio no tiene un canal de email conectado (SMTP). "
                "Conectalo en Canales antes de enviar o leer respuestas.",
                409,
            )
        return account

    async def _thread_ids(self, business_id: uuid.UUID, item: HarveyOutboxItem) -> list[str]:
        """Message-IDs of the earlier emails of this sequence, so follow-ups land in the same thread."""
        rows = (
            await self.db.execute(
                select(HarveyOutboxItem.message_id)
                .where(
                    HarveyOutboxItem.business_id == business_id,
                    HarveyOutboxItem.prospect_id == item.prospect_id,
                    HarveyOutboxItem.step < item.step,
                    HarveyOutboxItem.message_id.is_not(None),
                )
                .order_by(HarveyOutboxItem.step)
            )
        ).scalars()
        return list(rows)

    async def _block(self, item: HarveyOutboxItem, reasons: list[str]) -> HarveyOutboxItem:
        item.status = OutboxStatus.BLOCKED.value
        item.gate_reasons = reasons
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def send_item(
        self,
        business: Business,
        profile: HarveyProfile,
        item: HarveyOutboxItem,
        account: mailer.EmailAccount,
    ) -> HarveyOutboxItem:
        """Send one APPROVED item through the business's own mailbox.

        Never raises for an SMTP failure: the failure is recorded on the item (and it is retried a
        limited number of times) so one bad address cannot stop the rest of a batch.
        """
        if item.status != OutboxStatus.APPROVED.value:
            raise HarveyError(f"El borrador está en estado '{item.status}'; hay que aprobarlo primero", 409)
        if await self._sent_today(business.id) >= profile.max_daily_sends:
            raise HarveyError("Se alcanzó el máximo de envíos diarios de este negocio", 429)

        prospect = await self.get_prospect(business.id, item.prospect_id)
        # Last look before it leaves: the list or the prospect may have changed since approval.
        reasons = list(self._gate(profile, prospect, item.subject, item.body).reasons)
        if prospect.status in STOP_STATUSES:
            reasons.append(f"el prospecto está en estado '{prospect.status}'")
        if reasons:
            return await self._block(item, reasons)

        # Claim the item atomically: two concurrent requests must not both send the same email.
        claimed = await self.db.execute(
            update(HarveyOutboxItem)
            .where(HarveyOutboxItem.id == item.id, HarveyOutboxItem.status == OutboxStatus.APPROVED.value)
            .values(status=OutboxStatus.SENDING.value)
        )
        await self.db.commit()
        if claimed.rowcount != 1:
            await self.db.refresh(item)
            raise HarveyError("El borrador ya se está enviando", 409)

        chain = await self._thread_ids(business.id, item)
        msg = mailer.build_message(
            account,
            to_email=item.to_email,
            subject=item.subject,
            body=item.body,
            sender_name=profile.persona_name or business.name,
            in_reply_to=chain[-1] if chain else "",
            references=chain,
        )
        message_id = str(msg["Message-ID"])
        try:
            await mailer.send(account, msg)
        except Exception as e:
            attempts = (item.send_attempts or 0) + 1
            item.send_attempts = attempts
            item.send_error = f"{type(e).__name__}: {str(e)[:300]}"
            item.status = (
                OutboxStatus.FAILED.value if attempts >= MAX_SEND_ATTEMPTS else OutboxStatus.APPROVED.value
            )
            logger.warning("harvey: send failed for item %s (attempt %s): %s", item.id, attempts, type(e).__name__)
            await self.db.commit()
            await self.db.refresh(item)
            return item

        item.status = OutboxStatus.SENT.value
        item.sent_at = _utcnow()
        item.message_id = message_id
        item.send_error = ""
        prospect.status = (
            ProspectStatus.COMPLETED.value if item.step >= MAX_STEP else ProspectStatus.CONTACTED.value
        )
        await self.db.commit()
        await self.db.refresh(item)
        return item

    async def send_approved(
        self, business: Business, profile: HarveyProfile, limit: int = 20
    ) -> dict[str, int]:
        """Send up to ``limit`` approved items, oldest first, within the daily cap."""
        account = await self.require_account(business.id)
        items = list(
            (
                await self.db.execute(
                    select(HarveyOutboxItem)
                    .where(
                        HarveyOutboxItem.business_id == business.id,
                        HarveyOutboxItem.status == OutboxStatus.APPROVED.value,
                    )
                    .order_by(HarveyOutboxItem.created_at)
                    .limit(limit)
                )
            ).scalars()
        )
        sent = failed = blocked = 0
        capped = False
        for item in items:
            try:
                result = await self.send_item(business, profile, item, account)
            except HarveyError as e:
                if e.status_code == 429:
                    capped = True
                    break
                continue
            if result.status == OutboxStatus.SENT.value:
                sent += 1
            elif result.status == OutboxStatus.BLOCKED.value:
                blocked += 1
            else:
                failed += 1
        return {"sent": sent, "failed": failed, "blocked": blocked, "daily_cap_reached": int(capped)}

    # ── inbox ─────────────────────────────────────────────────────────────
    async def sync_inbox(self, business: Business, profile: HarveyProfile) -> dict[str, int]:
        """Read new mail from the business's inbox and turn replies to our emails into replies/opt-outs.

        Reading is read-only (the owner's unread flags are untouched) and idempotent: a message is
        recorded once, by Message-ID, however many times the sync runs.
        """
        account = await self.require_account(business.id)
        first_sent = (
            await self.db.execute(
                select(func.min(HarveyOutboxItem.sent_at)).where(
                    HarveyOutboxItem.business_id == business.id,
                    HarveyOutboxItem.status == OutboxStatus.SENT.value,
                )
            )
        ).scalar_one()
        zero = {"read": 0, "replies": 0, "bounces": 0, "ignored": 0, "more": 0}
        if first_sent is None:
            return zero  # nothing sent yet, so nothing can be a reply
        if first_sent.tzinfo is None:
            first_sent = first_sent.replace(tzinfo=timezone.utc)

        limit = 100
        try:
            inbound = await mailer.fetch_new(account, profile.imap_last_uid or 0, first_sent, limit)
        except Exception as e:
            logger.warning("harvey: inbox sync failed for business %s: %s", business.id, type(e).__name__)
            raise HarveyError(
                f"No se pudo leer la bandeja ({type(e).__name__}). Revisá host, usuario y contraseña IMAP del canal.",
                502,
            ) from e

        stats = dict(zero, read=len(inbound), more=int(len(inbound) >= limit))
        own = account.from_address.lower()
        for mail in inbound:
            kind = await self._handle_inbound(business, profile, mail, own)
            stats[kind] += 1

        if inbound:
            profile.imap_last_uid = max(profile.imap_last_uid or 0, *(m.uid for m in inbound))
        profile.inbox_synced_at = _utcnow()
        await self.db.commit()
        return stats

    async def _handle_inbound(
        self, business: Business, profile: HarveyProfile, mail: mailer.InboundEmail, own_address: str
    ) -> str:
        """Returns the stats bucket: replies | bounces | ignored."""
        if mail.is_bounce:
            marked = 0
            for address in mail.bounced_recipients:
                prospect = (
                    await self.db.execute(
                        select(HarveyProspect).where(
                            HarveyProspect.business_id == business.id, HarveyProspect.email == address
                        )
                    )
                ).scalar_one_or_none()
                if prospect is not None:
                    prospect.email_status = "invalid"
                    prospect.status = ProspectStatus.BOUNCED.value
                    marked += 1
            await self.db.commit()
            return "bounces" if marked else "ignored"
        if mail.is_auto or not mail.from_email or mail.from_email == own_address:
            return "ignored"
        if mail.message_id:
            seen = (
                await self.db.execute(
                    select(HarveyReply.id).where(
                        HarveyReply.business_id == business.id, HarveyReply.message_id == mail.message_id
                    )
                )
            ).first()
            if seen is not None:
                return "ignored"

        prospect = await self._match_prospect(business.id, mail)
        if prospect is None:
            return "ignored"  # mail from someone who is not on this business's list
        text = mail.body or mail.subject
        if not text.strip():
            return "ignored"
        await self.record_reply(business, profile, prospect, text, message_id=mail.message_id or None)
        return "replies"

    async def _match_prospect(self, business_id: uuid.UUID, mail: mailer.InboundEmail) -> HarveyProspect | None:
        """The prospect an email answers: by the thread first, then by sender address."""
        refs = [r for r in [mail.in_reply_to, *mail.references] if r]
        if refs:
            prospect_id = (
                await self.db.execute(
                    select(HarveyOutboxItem.prospect_id).where(
                        HarveyOutboxItem.business_id == business_id, HarveyOutboxItem.message_id.in_(refs)
                    )
                )
            ).scalars().first()
            if prospect_id is not None:
                return await self.get_prospect(business_id, prospect_id)
        return (
            await self.db.execute(
                select(HarveyProspect).where(
                    HarveyProspect.business_id == business_id, HarveyProspect.email == mail.from_email
                )
            )
        ).scalar_one_or_none()

    # ── replies ───────────────────────────────────────────────────────────
    async def record_reply(
        self,
        business: Business,
        profile: HarveyProfile,
        prospect: HarveyProspect,
        body: str,
        message_id: str | None = None,
    ) -> HarveyReply:
        body = (body or "").strip()[:5000]
        classification, needs_human, answer = await self._classify(business, profile, prospect, body)

        reply = HarveyReply(
            business_id=business.id,
            prospect_id=prospect.id,
            body=body,
            message_id=message_id,
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
        # Someone who answered must not receive the follow-ups that are still queued.
        await self.db.execute(
            update(HarveyOutboxItem)
            .where(
                HarveyOutboxItem.business_id == business.id,
                HarveyOutboxItem.prospect_id == prospect.id,
                HarveyOutboxItem.status.in_(
                    [OutboxStatus.PENDING_REVIEW.value, OutboxStatus.APPROVED.value]
                ),
            )
            .values(status=OutboxStatus.REJECTED.value, send_error="el prospecto respondió")
        )
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
