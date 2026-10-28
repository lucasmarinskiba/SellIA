"""Competitor map per business: who it studies, what their sites say, and a brief that feeds Harvey's drafts.

Three kinds of site: direct and indirect competitors, and the business's own site (read the same way, so the
comparison is like with like). Only what the sites publish is stored. The brief interprets it; with no model it
degrades to the plain facts and Harvey's drafts simply get no extra angle.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlparse

import httpx
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.businesses.models import Business
from app.domains.harvey import competitors as reader
from app.domains.harvey import discovery
from app.domains.harvey.discovery import DiscoveryError
from app.domains.harvey.gate import UNTRUSTED_RULE, fence
from app.domains.harvey.llm import ask_json, llm_available
from app.domains.harvey.models import (
    CompetitorKind,
    HarveyCompetitiveBrief,
    HarveyCompetitor,
    HarveyProfile,
)

logger = get_logger(__name__)

MAX_COMPETITORS = 15
RESCAN_AFTER = timedelta(minutes=10)  # one site is not re-read more often than this
STALE_AFTER = timedelta(hours=24)  # "analyze" re-reads sites older than this
KINDS = {k.value for k in CompetitorKind}


class CompetitorError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime | None) -> datetime | None:
    return value if value is None or value.tzinfo else value.replace(tzinfo=timezone.utc)


def clean_list(value: Any, limit: int, width: int = 180) -> list[str]:
    """Model output as a short list of short strings; anything else is dropped."""
    if not isinstance(value, list):
        return []
    return [str(v).strip()[:width] for v in value if isinstance(v, str) and v.strip()][:limit]


class CompetitorService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self, business_id: uuid.UUID) -> list[HarveyCompetitor]:
        rows = await self.db.execute(
            select(HarveyCompetitor)
            .where(HarveyCompetitor.business_id == business_id)
            .order_by(HarveyCompetitor.created_at)
        )
        return list(rows.scalars())

    async def get(self, business_id: uuid.UUID, competitor_id: uuid.UUID) -> HarveyCompetitor:
        row = (
            await self.db.execute(
                select(HarveyCompetitor).where(
                    HarveyCompetitor.id == competitor_id, HarveyCompetitor.business_id == business_id
                )
            )
        ).scalar_one_or_none()
        if row is None:
            raise CompetitorError("Competidor no encontrado", 404)
        return row

    async def add(self, business_id: uuid.UUID, url: str, kind: str, name: str = "") -> HarveyCompetitor:
        if kind not in KINDS:
            raise CompetitorError("Tipo inválido: usá direct, indirect u own", 422)
        try:
            clean_url = discovery.normalize_url(url)
            await discovery.assert_public_url(clean_url)
        except DiscoveryError as e:
            raise CompetitorError(str(e), 422) from e
        parsed = urlparse(clean_url)
        root = f"{parsed.scheme}://{parsed.netloc}".lower()

        count = (
            await self.db.execute(
                select(func.count(HarveyCompetitor.id)).where(HarveyCompetitor.business_id == business_id)
            )
        ).scalar_one()
        if count >= MAX_COMPETITORS:
            raise CompetitorError(f"Podés estudiar hasta {MAX_COMPETITORS} sitios", 409)
        if kind == CompetitorKind.OWN.value:
            has_own = (
                await self.db.execute(
                    select(HarveyCompetitor.id).where(
                        HarveyCompetitor.business_id == business_id, HarveyCompetitor.kind == CompetitorKind.OWN.value
                    )
                )
            ).first()
            if has_own:
                raise CompetitorError("Ya cargaste el sitio propio; borralo para cambiarlo", 409)
        dup = (
            await self.db.execute(
                select(HarveyCompetitor.id).where(
                    HarveyCompetitor.business_id == business_id, HarveyCompetitor.url == root
                )
            )
        ).first()
        if dup:
            raise CompetitorError("Ese sitio ya está en tu lista", 409)

        row = HarveyCompetitor(business_id=business_id, url=root, kind=kind, name=(name or "").strip()[:160])
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def remove(self, business_id: uuid.UUID, competitor_id: uuid.UUID) -> None:
        row = await self.get(business_id, competitor_id)
        await self.db.delete(row)
        await self.db.commit()

    async def scan_one(
        self, row: HarveyCompetitor, client: httpx.AsyncClient | None = None, *, force: bool = False
    ) -> HarveyCompetitor:
        last = _aware(row.last_scanned_at)
        if not force and last and _now() - last < RESCAN_AFTER and not row.last_error:
            raise CompetitorError("Este sitio se leyó hace pocos minutos; probá más tarde", 429)
        own_client = client is None
        client = client or discovery.make_client()
        try:
            snapshot = await reader.scan(client, row.url)
            row.snapshot = snapshot
            row.last_error = ""
            if not row.name:
                row.name = (snapshot.get("title") or "")[:80] or urlparse(row.url).netloc
        except (DiscoveryError, httpx.HTTPError) as e:
            row.last_error = str(e)[:300] or "No se pudo leer el sitio"
        finally:
            row.last_scanned_at = _now()
            if own_client:
                await client.aclose()
        await self.db.commit()
        await self.db.refresh(row)
        return row

    # ── brief ─────────────────────────────────────────────────────────────
    async def get_brief(self, business_id: uuid.UUID) -> HarveyCompetitiveBrief | None:
        return (
            await self.db.execute(
                select(HarveyCompetitiveBrief).where(HarveyCompetitiveBrief.business_id == business_id)
            )
        ).scalar_one_or_none()

    @staticmethod
    def _facts_block(rows: list[HarveyCompetitor]) -> str:
        parts = []
        for r in rows:
            s = r.snapshot or {}
            if not s:
                continue
            parts.append(
                f"[{r.kind}] {r.name or r.url} ({r.url})\n"
                f"  titulares: {'; '.join(s.get('headlines', [])) or '-'}\n"
                f"  precios: {' | '.join(s.get('prices', [])) or '-'}\n"
                f"  ofertas: {' | '.join(s.get('offers', [])) or '-'}"
            )
        return "\n\n".join(parts)

    async def analyze(self, business: Business, profile: HarveyProfile) -> HarveyCompetitiveBrief:
        rows = await self.list_all(business.id)
        if not rows:
            raise CompetitorError("Cargá al menos un sitio para analizar", 422)
        async with discovery.make_client() as client:
            for r in rows:
                last = _aware(r.last_scanned_at)
                if last is None or _now() - last > STALE_AFTER or r.last_error:
                    await self.scan_one(r, client, force=True)
        readable = [r for r in rows if r.snapshot]
        if not readable:
            raise CompetitorError("No pudimos leer ninguno de los sitios cargados", 422)

        brief: dict[str, Any] = {
            "summary": "", "gaps": [], "opportunities": [], "angles": [], "icp_hints": [], "source": "facts",
        }
        if llm_available():
            own = "\n".join(
                [f"Oferta: {profile.offer or business.description or '-'}", *(f"- {b}" for b in (profile.benefits or []))]
            )
            prompt = f"""Compará lo que publica el mercado con lo que ofrece este negocio.

LO PROPIO (cargado por el dueño):
{own}

LO QUE PUBLICAN LOS SITIOS (propio y competidores):
{fence(self._facts_block(readable), "sitios estudiados")}

{UNTRUSTED_RULE}

Reglas: usá SOLO lo que aparece arriba; no inventes precios, cifras ni ofertas. Si falta un dato, decí que falta.
Respondé SOLO con JSON:
{{"summary": "2-3 frases",
 "gaps": ["en qué el negocio está peor o no dice nada frente a los demás"],
 "opportunities": ["qué hacen los demás que el negocio podría hacer o decir"],
 "angles": ["hasta 3 ángulos de diferenciación para escribirle a un cliente, sin nombrar competidores"],
 "icp_hints": ["a qué tipo de cliente conviene apuntar según lo anterior"]}}"""
            result = await ask_json(
                "Sos un analista de mercado para una pyme. Respondés SOLO con un objeto JSON.", prompt, max_tokens=1200
            )
            if result:
                brief = {
                    "summary": str(result.get("summary") or "").strip()[:600],
                    "gaps": clean_list(result.get("gaps"), 6),
                    "opportunities": clean_list(result.get("opportunities"), 6),
                    "angles": clean_list(result.get("angles"), 3, 160),
                    "icp_hints": clean_list(result.get("icp_hints"), 4),
                    "source": "model",
                }
        if brief["source"] == "facts":
            brief["summary"] = (
                f"Leímos {len(readable)} sitio(s). Sin el modelo disponible no hay interpretación; "
                "mirá abajo lo que publica cada uno."
            )

        row = await self.get_brief(business.id)
        if row is None:
            row = HarveyCompetitiveBrief(business_id=business.id, brief=brief)
            self.db.add(row)
        else:
            row.brief = brief
        row.generated_at = _now()
        await self.db.commit()
        await self.db.refresh(row)
        return row

    async def angles_for_prompt(self, business_id: uuid.UUID) -> str:
        """A fenced block of market angles for Harvey's drafts, or "" when there is none."""
        try:
            # A savepoint: if the table is not there yet, only this lookup fails, never the draft's transaction.
            async with self.db.begin_nested():
                row = await self.get_brief(business_id)
        except Exception:  # noqa: BLE001 - extra context must never block drafting
            logger.warning("harvey: competitive brief unavailable; drafting without it")
            return ""
        angles = clean_list((row.brief or {}).get("angles") if row else [], 3, 160)
        if not angles:
            return ""
        return (
            "\n- Ángulos de diferenciación del mercado (tomados de sitios públicos; usá uno solo si encaja con "
            "los HECHOS del prospecto, sin nombrar competidores ni comparar precios):\n"
            + fence("\n".join(f"- {a}" for a in angles), "ángulos de mercado")
        )
