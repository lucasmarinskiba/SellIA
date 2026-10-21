"""Store real prospects as InboundLead rows, skipping the ones already stored.

Two real sources feed this module: Google Places results (places_source.py) and
CSV files the business uploads with its own contacts. Nothing here generates or
guesses contact data.
"""

import csv
import io
import logging
import re
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.growth.models import InboundLead, InboundLeadSource, NurturingStage
from app.domains.lead_generation.places_source import PlaceProspect

logger = logging.getLogger(__name__)

MAX_CSV_BYTES = 1_000_000
MAX_CSV_ROWS = 1000
MAX_REJECTIONS_REPORTED = 20
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
CSV_FIELDS = ("name", "email", "phone", "company", "website")


@dataclass
class CaptureResult:
    created: list[dict[str, Any]] = field(default_factory=list)
    skipped_duplicates: int = 0


@dataclass
class CsvParseResult:
    contacts: list[dict[str, Any]] = field(default_factory=list)
    rejected: list[dict[str, Any]] = field(default_factory=list)
    rejected_count: int = 0


def normalize_phone(raw: Optional[str]) -> str:
    """Keep digits only, so '+54 11 4444-5555' and '1144445555' compare equal."""
    return re.sub(r"\D", "", raw or "")


async def _stored_contact_info(db: AsyncSession, business_id: uuid.UUID) -> list[dict[str, Any]]:
    result = await db.execute(
        select(InboundLead.contact_info).where(
            InboundLead.business_id == business_id,
            InboundLead.is_active == True,  # noqa: E712 - SQLAlchemy column comparison
        )
    )
    return [info for info in result.scalars().all() if info]


async def save_place_prospects(
    db: AsyncSession,
    business_id: uuid.UUID,
    prospects: list[PlaceProspect],
    query: str,
) -> CaptureResult:
    """Persist prospects that this business does not already have (matched by place_id)."""
    known_place_ids = {info.get("place_id") for info in await _stored_contact_info(db, business_id)}
    outcome = CaptureResult()
    rows: list[InboundLead] = []

    for prospect in prospects:
        if prospect.place_id in known_place_ids:
            outcome.skipped_duplicates += 1
            continue
        known_place_ids.add(prospect.place_id)
        rows.append(InboundLead(
            business_id=business_id,
            source_type=InboundLeadSource.ORGANIC_SEARCH,
            source_detail=f"google_places: {query}"[:200],
            contact_info=prospect.to_contact_info(),
            nurturing_stage=NurturingStage.NEW,
        ))
        outcome.created.append(prospect.to_contact_info())

    if rows:
        db.add_all(rows)
        await db.commit()
    logger.info("Places capture business=%s created=%d duplicates=%d",
                business_id, len(outcome.created), outcome.skipped_duplicates)
    return outcome


def parse_csv_contacts(raw: bytes) -> CsvParseResult:
    """Validate a contacts CSV. Each row needs a name and an email or phone.

    Headers are matched case-insensitively against CSV_FIELDS. Raises ValueError
    for files that cannot be read at all; bad rows are reported, not fatal.
    """
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("El archivo debe estar codificado en UTF-8") from exc

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or "name" not in {h.strip().lower() for h in reader.fieldnames}:
        raise ValueError("El CSV necesita una columna 'name' en la primera fila")

    outcome = CsvParseResult()
    seen_emails: set[str] = set()
    seen_phones: set[str] = set()

    for line_number, row in enumerate(reader, start=2):
        if line_number - 1 > MAX_CSV_ROWS:
            raise ValueError(f"El CSV supera el máximo de {MAX_CSV_ROWS} filas")

        values = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
        contact = {key: values.get(key, "") for key in CSV_FIELDS}
        email = contact["email"].lower()
        phone_digits = normalize_phone(contact["phone"])

        reason = None
        if not contact["name"]:
            reason = "falta el nombre"
        elif not email and not phone_digits:
            reason = "falta email o teléfono"
        elif email and not EMAIL_PATTERN.match(email):
            reason = "email inválido"
        elif (email and email in seen_emails) or (phone_digits and phone_digits in seen_phones):
            reason = "duplicado dentro del archivo"

        if reason:
            outcome.rejected_count += 1
            if len(outcome.rejected) < MAX_REJECTIONS_REPORTED:
                outcome.rejected.append({"line": line_number, "reason": reason})
            continue

        contact["email"] = email
        if email:
            seen_emails.add(email)
        if phone_digits:
            seen_phones.add(phone_digits)
        outcome.contacts.append(contact)

    return outcome


async def save_csv_contacts(
    db: AsyncSession,
    business_id: uuid.UUID,
    contacts: list[dict[str, Any]],
    source_name: str,
) -> CaptureResult:
    """Persist CSV contacts, skipping emails or phones this business already has."""
    stored = await _stored_contact_info(db, business_id)
    known_emails = {(info.get("email") or "").lower() for info in stored} - {""}
    known_phones = {normalize_phone(info.get("phone")) for info in stored} - {""}
    outcome = CaptureResult()
    rows: list[InboundLead] = []
    detail = f"csv_import: {source_name}"[:200]

    for contact in contacts:
        phone_digits = normalize_phone(contact["phone"])
        if (contact["email"] and contact["email"] in known_emails) or (phone_digits and phone_digits in known_phones):
            outcome.skipped_duplicates += 1
            continue
        rows.append(InboundLead(
            business_id=business_id,
            source_type=InboundLeadSource.DIRECT,
            source_detail=detail,
            contact_info={k: v for k, v in contact.items() if v},
            nurturing_stage=NurturingStage.NEW,
        ))
        outcome.created.append(contact)

    if rows:
        db.add_all(rows)
        await db.commit()
    logger.info("CSV capture business=%s created=%d duplicates=%d",
                business_id, len(outcome.created), outcome.skipped_duplicates)
    return outcome
