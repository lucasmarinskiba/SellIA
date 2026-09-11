"""Reads and writes the seller's configuration across the tables that own it.

The screen shows one coherent profile, but the fields belong to three different
owners and stay there: BusinessContext keeps the niche, the audience, the
markets and the goals; UserMemory keeps the language, the tone and the
interests; SellerPreferences keeps what neither had. Copying them into a fourth
table would create two versions of the same fact, and the AI reads the originals.
"""

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger
from app.domains.preferences import catalog
from app.domains.preferences.models import SellerPreferences

logger = get_logger(__name__)

MAX_LIST_ITEMS = 30
MAX_ITEM_LENGTH = 80


def _clean_list(values: Any, *, allowed: Optional[set[str]] = None) -> list[str]:
    """Trim, de-duplicate and cap a list of short strings, preserving order."""
    if not isinstance(values, list):
        return []
    out: list[str] = []
    for raw in values:
        if not isinstance(raw, (str, int)):
            continue
        value = str(raw).strip()[:MAX_ITEM_LENGTH]
        if not value:
            continue
        if allowed is not None and value not in allowed:
            continue
        if value not in out:
            out.append(value)
        if len(out) >= MAX_LIST_ITEMS:
            break
    return out


async def _get_or_create_prefs(db: AsyncSession, business_id: uuid.UUID) -> SellerPreferences:
    result = await db.execute(
        select(SellerPreferences).where(SellerPreferences.business_id == business_id)
    )
    prefs = result.scalar_one_or_none()
    if prefs is None:
        prefs = SellerPreferences(business_id=business_id)
        db.add(prefs)
        await db.flush()
    return prefs


async def _get_context(db: AsyncSession, user_id: uuid.UUID, business_id: Optional[uuid.UUID]):
    from app.domains.business_context.models import BusinessContext

    query = select(BusinessContext).where(BusinessContext.user_id == user_id)
    if business_id:
        query = query.where(BusinessContext.business_id == business_id)
    result = await db.execute(query.order_by(BusinessContext.created_at.desc()).limit(1))
    return result.scalar_one_or_none()


async def _get_memory(db: AsyncSession, user_id: uuid.UUID):
    from app.domains.user_memory.models import UserMemory

    result = await db.execute(select(UserMemory).where(UserMemory.user_id == user_id))
    return result.scalar_one_or_none()


async def load_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    business_id: Optional[uuid.UUID],
) -> dict[str, Any]:
    """Everything the configuration screen shows, plus what is still missing."""
    prefs = await _get_or_create_prefs(db, business_id) if business_id else None
    context = await _get_context(db, user_id, business_id)
    memory = await _get_memory(db, user_id)

    profile: dict[str, Any] = {
        # Identity of the business — BusinessContext owns these.
        "business_type": context.business_type.value if context and context.business_type else None,
        "sales_model": context.sales_model.value if context and context.sales_model else None,
        "niche": context.industry if context else None,
        "target_audience": context.target_audience if context else None,
        "value_proposition": context.value_proposition if context else None,
        "price_range": context.price_range if context else None,
        "primary_goal": context.primary_goal if context else None,
        "country": context.country if context else None,
        "city": context.city if context else None,
        # Voice and taste — UserMemory owns these.
        "primary_language": memory.preferred_language if memory else "es",
        "tone": memory.preferred_tone if memory else "professional",
        "interests": list(memory.key_interests or []) if memory else [],
        "challenges": list(memory.key_challenges or []) if memory else [],
        # What only this domain has.
        "target_platforms": list(prefs.target_platforms or []) if prefs else [],
        "languages": list(prefs.languages or []) if prefs else [],
        "markets": list(prefs.markets or []) if prefs else [],
        "tastes": list(prefs.tastes or []) if prefs else [],
        "banned_topics": list(prefs.banned_topics or []) if prefs else [],
        "display_currency": prefs.display_currency if prefs else None,
        "voice_notes": prefs.voice_notes if prefs else None,
        "autonomous_replies": prefs.autonomous_replies if prefs else True,
    }

    # The markets list started life in BusinessContext.target_countries; if the
    # seller filled that in before this screen existed, show it rather than an
    # empty field.
    if not profile["markets"] and context and context.target_countries:
        profile["markets"] = _clean_list(context.target_countries)

    profile["completeness"] = _completeness(profile)
    return profile


#: Fields that change what the AI writes or where it sells. Anything not here is
#: nice to have and does not count against the seller.
IMPORTANT_FIELDS: list[tuple[str, str]] = [
    ("business_type", "Qué tipo de negocio es"),
    ("niche", "Tu nicho"),
    ("target_audience", "A quién le vendés"),
    ("value_proposition", "Por qué te compran a vos"),
    ("markets", "En qué países vendés"),
    ("languages", "En qué idiomas vendés"),
    ("target_platforms", "Dónde querés vender"),
    ("tone", "Cómo querés sonar"),
    ("primary_goal", "Qué querés lograr"),
]


def _completeness(profile: dict[str, Any]) -> dict[str, Any]:
    missing = [
        {"field": field, "label": label}
        for field, label in IMPORTANT_FIELDS
        if not profile.get(field)
    ]
    filled = len(IMPORTANT_FIELDS) - len(missing)
    return {
        "filled": filled,
        "total": len(IMPORTANT_FIELDS),
        "percent": round(100 * filled / len(IMPORTANT_FIELDS)),
        "missing": missing,
    }


async def save_profile(
    db: AsyncSession,
    user_id: uuid.UUID,
    business_id: uuid.UUID,
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Write each field back to the table that owns it. Absent keys are left alone."""
    from app.domains.business_context.models import BusinessContext, BusinessType, SalesModel
    from app.domains.user_memory.models import UserMemory

    prefs = await _get_or_create_prefs(db, business_id)
    known_platforms = set(catalog.PLATFORM_FIT)
    known_languages = {item["code"] for item in catalog.LANGUAGES}
    known_markets = {item["code"] for item in catalog.MARKETS}

    if "target_platforms" in payload:
        prefs.target_platforms = _clean_list(payload["target_platforms"], allowed=known_platforms)
    if "languages" in payload:
        prefs.languages = _clean_list(payload["languages"], allowed=known_languages)
    if "markets" in payload:
        prefs.markets = _clean_list(payload["markets"], allowed=known_markets)
    if "tastes" in payload:
        prefs.tastes = _clean_list(payload["tastes"])
    if "banned_topics" in payload:
        prefs.banned_topics = _clean_list(payload["banned_topics"])
    if "display_currency" in payload:
        raw = (payload["display_currency"] or "").strip().upper()
        prefs.display_currency = raw[:3] or None
    if "voice_notes" in payload:
        notes = (payload["voice_notes"] or "").strip()
        prefs.voice_notes = notes[:2000] or None
    if "autonomous_replies" in payload:
        prefs.autonomous_replies = bool(payload["autonomous_replies"])

    # --- BusinessContext ---
    context = await _get_context(db, user_id, business_id)
    context_fields = {
        "niche": "industry",
        "target_audience": "target_audience",
        "value_proposition": "value_proposition",
        "price_range": "price_range",
        "primary_goal": "primary_goal",
        "country": "country",
        "city": "city",
    }
    touches_context = any(key in payload for key in list(context_fields) + ["business_type", "sales_model", "markets"])
    if touches_context:
        if context is None:
            context = BusinessContext(user_id=user_id, business_id=business_id)
            db.add(context)
        for incoming, column in context_fields.items():
            if incoming in payload:
                value = payload[incoming]
                setattr(context, column, (str(value).strip()[:500] or None) if value else None)
        if payload.get("business_type"):
            try:
                context.business_type = BusinessType(payload["business_type"])
            except ValueError:
                logger.warning(f"Unknown business_type ignored: {payload['business_type']}")
        if payload.get("sales_model"):
            try:
                context.sales_model = SalesModel(payload["sales_model"])
            except ValueError:
                logger.warning(f"Unknown sales_model ignored: {payload['sales_model']}")
        if "markets" in payload:
            # Kept in sync because the SEO and shipping code already reads
            # target_countries; the preferences screen is not a second truth.
            context.target_countries = list(prefs.markets or [])

    # --- UserMemory ---
    memory = await _get_memory(db, user_id)
    touches_memory = any(key in payload for key in ("primary_language", "tone", "interests", "challenges"))
    if touches_memory:
        if memory is None:
            memory = UserMemory(user_id=user_id)
            db.add(memory)
        if payload.get("primary_language") in known_languages:
            memory.preferred_language = payload["primary_language"]
        if payload.get("tone") in {item["value"] for item in catalog.TONES}:
            memory.preferred_tone = payload["tone"]
        if "interests" in payload:
            memory.key_interests = _clean_list(payload["interests"])
        if "challenges" in payload:
            memory.key_challenges = _clean_list(payload["challenges"])

    await db.commit()
    return await load_profile(db, user_id, business_id)


async def connected_platforms(db: AsyncSession, business_id: uuid.UUID) -> set[str]:
    """Which platforms this business has actually connected."""
    from app.domains.channels.models import ChannelConnection

    result = await db.execute(
        select(ChannelConnection.platform).where(ChannelConnection.business_id == business_id)
    )
    return {
        (row[0].value if hasattr(row[0], "value") else str(row[0]))
        for row in result.all()
    }


async def suggest_platforms(
    db: AsyncSession,
    business_id: uuid.UUID,
    profile: dict[str, Any],
) -> dict[str, Any]:
    """Platforms that fit this seller, each with the reason it was suggested.

    There is no score out of 100 here on purpose. A number would imply a
    measurement, and nothing has been measured: these are matches between what
    the seller said about their business and where each platform operates. The
    reasons are the output; the ordering is just the reasons counted.
    """
    from app.domains.platform_commerce import capabilities

    connected = await connected_platforms(db, business_id)
    markets = set(profile.get("markets") or [])
    niche = profile.get("business_type")
    wanted = set(profile.get("target_platforms") or [])

    unknowns: list[str] = []
    if not markets:
        unknowns.append("No configuraste mercados, así que no se puede saber qué marketplace te llega.")
    if not niche:
        unknowns.append("No configuraste el tipo de negocio, así que la afinidad por rubro no se evaluó.")

    suggestions: list[dict[str, Any]] = []
    for platform, fit in catalog.PLATFORM_FIT.items():
        if platform in connected:
            continue
        reasons: list[str] = []
        if niche and niche in fit["suits"]:
            reasons.append(f"Encaja con tu rubro ({niche.replace('_', ' ')}).")
        if markets and fit["markets"]:
            overlap = markets & set(fit["markets"])
            if overlap:
                reasons.append("Opera en " + ", ".join(sorted(overlap)) + ".")
        elif markets and not fit["markets"]:
            reasons.append("No depende del país: funciona donde vendas.")
        if platform in wanted:
            reasons.append("Ya lo marcaste como plataforma donde querés vender.")
        if not reasons:
            continue

        caps = capabilities.capabilities_for(platform)
        available = [key for key, ok in caps.items() if ok]
        suggestions.append({
            "platform": platform,
            "label": fit["label"],
            "kind": fit["kind"],
            "note": fit["note"],
            "reasons": reasons,
            # What SellIA can really automate there once it is connected, read
            # off the connector — not a promise from this table.
            "capabilities": available,
            "can_import_orders": "orders" in available,
            "can_answer_messages": "messages" in available,
        })

    suggestions.sort(key=lambda item: (-len(item["reasons"]), item["label"].lower()))
    return {
        "connected": sorted(connected),
        "suggestions": suggestions[:8],
        "unknowns": unknowns,
    }
