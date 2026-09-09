"""Analytics read the way an analyst reads them.

The dashboard used to show percentages with no denominator and no time frame --
"conversión 8%" of what, over what period, out of how many. This service answers
each number together with the evidence behind it: the counts it came from, the
interval it could really be in, and, when the sample is too small, a plain
statement that nothing can be concluded yet.

Every row read here belongs to the signed-in account (businesses are filtered by
user_id first); there is no global aggregate anywhere in this file.
"""

from __future__ import annotations

import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

from .stats import MIN_FOR_TREND, MIN_TO_READ, Proportion, describe_change, median, quartiles

logger = get_logger(__name__)


async def _business_ids(db: AsyncSession, user_id: uuid.UUID) -> list[uuid.UUID]:
    from app.domains.businesses.models import Business

    result = await db.execute(select(Business.id).where(Business.user_id == user_id))
    return [row[0] for row in result.all()]


async def get_insights(db: AsyncSession, user, days: int = 30) -> dict[str, Any]:
    """The account's real numbers, each with its reading and its caveat."""
    from app.domains.channels.models import (
        ChannelConnection, Conversation, Message, MessageDirection,
    )

    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    business_ids = await _business_ids(db, user.id)

    empty: dict[str, Any] = {
        "period_days": days,
        "has_data": False,
        "headline": "Todavía no hay datos propios para analizar.",
        "readings": [],
        "series": [],
        "by_platform": [],
        "peak_hours": [],
        "methodology": _methodology(),
        "generated_at": now.isoformat(),
    }
    if not business_ids:
        empty["headline"] = (
            "Todavía no creaste tu negocio, así que no hay ninguna conversación ni venta tuya "
            "que analizar."
        )
        return empty

    # ── Conversations in the window, with their channel platform ──
    conv_rows = await db.execute(
        select(Conversation.id, Conversation.created_at, ChannelConnection.platform)
        .outerjoin(ChannelConnection, Conversation.channel_connection_id == ChannelConnection.id)
        .where(
            Conversation.business_id.in_(business_ids),
            Conversation.created_at >= since,
        )
    )
    conversations = conv_rows.all()
    conv_ids = [row[0] for row in conversations]

    if not conv_ids:
        empty["headline"] = (
            f"No entraron conversaciones en los últimos {days} días, así que no hay nada que "
            "medir todavía. En cuanto llegue el primer mensaje a un canal conectado, aparece acá."
        )
        return empty

    # ── Every message of those conversations (one query, then grouped) ──
    msg_rows = await db.execute(
        select(
            Message.conversation_id, Message.direction, Message.created_at, Message.extra_data
        )
        .where(Message.conversation_id.in_(conv_ids))
        .order_by(Message.created_at.asc())
    )
    messages = msg_rows.all()

    first_inbound: dict[uuid.UUID, datetime] = {}
    first_reply: dict[uuid.UUID, datetime] = {}
    ai_replied: set[uuid.UUID] = set()
    inbound_hours: Counter[int] = Counter()
    inbound_total = 0

    for conv_id, direction, created_at, extra in messages:
        is_inbound = direction == MessageDirection.INBOUND
        if is_inbound:
            inbound_total += 1
            inbound_hours[created_at.hour] += 1
            first_inbound.setdefault(conv_id, created_at)
        else:
            # Only a reply that came AFTER a customer wrote counts as a response.
            if conv_id in first_inbound and conv_id not in first_reply:
                first_reply[conv_id] = created_at
            if isinstance(extra, dict) and extra.get("generated_by") == "ai":
                ai_replied.add(conv_id)

    asked = set(first_inbound)
    answered = set(first_reply)

    latencies_min = [
        (first_reply[c] - first_inbound[c]).total_seconds() / 60
        for c in answered
        if first_reply[c] >= first_inbound[c]
    ]

    response = Proportion(len(answered), len(asked))
    ai_share = Proportion(len(ai_replied & answered), len(answered))

    readings: list[dict[str, Any]] = [
        {
            "key": "response_rate",
            "title": "Consultas que recibieron respuesta",
            "value": response.percent,
            "unit": "%",
            "confidence": response.confidence,
            "reading": response.reading("consultas"),
            "why_it_matters": (
                "Es la métrica que más plata mueve: cada consulta sin responder es una venta que "
                "se fue a otro lado sin dejar rastro."
            ),
        },
        {
            "key": "ai_share",
            "title": "Respuestas que generó la IA",
            "value": ai_share.percent,
            "unit": "%",
            "confidence": ai_share.confidence,
            "reading": ai_share.reading("respuestas"),
            "why_it_matters": (
                "Mide cuánto del trabajo se está haciendo solo. No es una meta en sí: lo que "
                "importa es que suba sin que baje la tasa de respuesta ni las ventas."
            ),
        },
    ]

    med = median(latencies_min)
    if med is not None:
        q1, q3 = quartiles(latencies_min)
        spread = (
            f" La mitad del medio de los casos cae entre {round(q1)} y {round(q3)} minutos."
            if q1 is not None and q3 is not None else ""
        )
        readings.append({
            "key": "first_response_minutes",
            "title": "Tiempo hasta la primera respuesta (mediana)",
            "value": round(med, 1),
            "unit": "min",
            "confidence": "solid" if len(latencies_min) >= MIN_FOR_TREND
                          else "preliminary" if len(latencies_min) >= MIN_TO_READ else "insufficient",
            "reading": (
                f"La mitad de tus clientes esperó {round(med)} minutos o menos "
                f"(n={len(latencies_min)}).{spread} Se usa la mediana y no el promedio: una sola "
                "consulta contestada dos días después distorsiona un promedio y no describe a nadie."
            ),
            "why_it_matters": (
                "La probabilidad de cerrar cae fuerte con los minutos: responder rápido suele "
                "rendir más que cualquier cambio de precio."
            ),
        })

    # ── Volume: last 7 days vs the 7 before, on real created_at ──
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    this_week = sum(1 for _, created, _ in conversations if created >= week_ago)
    last_week = sum(1 for _, created, _ in conversations if two_weeks_ago <= created < week_ago)
    change = describe_change(this_week, last_week, "conversaciones")
    readings.append({
        "key": "weekly_volume",
        "title": "Conversaciones esta semana",
        "value": this_week,
        "unit": "",
        "confidence": "solid" if this_week + last_week >= MIN_FOR_TREND
                      else "preliminary" if this_week + last_week >= MIN_TO_READ else "insufficient",
        "reading": change["reading"],
        "direction": change["direction"],
        "why_it_matters": (
            "El volumen es lo primero que hay que mirar: una conversión que sube mientras el "
            "volumen se derrumba casi siempre es un espejismo."
        ),
    })

    # ── Daily series (real counts, zero-filled so gaps are visible as gaps) ──
    by_day: Counter[str] = Counter()
    for _, created, _ in conversations:
        by_day[created.date().isoformat()] += 1
    series = []
    for offset in range(days - 1, -1, -1):
        day = (now - timedelta(days=offset)).date().isoformat()
        series.append({"date": day, "conversations": by_day.get(day, 0)})

    # ── Per platform ──
    platform_conv: Counter[str] = Counter()
    platform_answered: Counter[str] = Counter()
    for conv_id, _, platform in conversations:
        name = platform.value if hasattr(platform, "value") else (platform or "sin_canal")
        if conv_id in asked:
            platform_conv[name] += 1
            if conv_id in answered:
                platform_answered[name] += 1
    by_platform = []
    for name, total in platform_conv.most_common():
        prop = Proportion(platform_answered.get(name, 0), total)
        by_platform.append({
            "platform": name,
            "conversations": total,
            "answered": platform_answered.get(name, 0),
            "response_rate": prop.percent,
            "confidence": prop.confidence,
            "reading": prop.reading("consultas"),
        })

    peak_hours = [
        {"hour": hour, "inbound": count}
        for hour, count in sorted(inbound_hours.items())
    ]

    headline = _headline(response, med, this_week, last_week, len(asked))

    return {
        "period_days": days,
        "has_data": True,
        "headline": headline,
        "totals": {
            "conversations": len(conversations),
            "with_customer_message": len(asked),
            "answered": len(answered),
            "ai_answered": len(ai_replied & answered),
            "inbound_messages": inbound_total,
        },
        "readings": readings,
        "series": series,
        "by_platform": by_platform,
        "peak_hours": peak_hours,
        "methodology": _methodology(),
        "generated_at": now.isoformat(),
    }


def _headline(
    response: Proportion,
    median_minutes: Optional[float],
    this_week: int,
    last_week: int,
    asked: int,
) -> str:
    """The one sentence an analyst would lead with — chosen by which real number
    is furthest from where it should be, never a fixed template."""
    if asked < MIN_TO_READ:
        return (
            f"Solo {asked} consulta(s) en el período: alcanza para ver que el sistema funciona, "
            "no para sacar conclusiones. Lo primero es traer volumen, no optimizar porcentajes."
        )
    if response.percent < 70:
        low, high = response.wilson_interval()
        return (
            f"Estás dejando sin responder cerca de {round(100 - response.percent)}% de las consultas "
            f"(la tasa de respuesta está entre {low}% y {high}%). Es el agujero más caro que "
            "tenés hoy y el más fácil de tapar."
        )
    if median_minutes is not None and median_minutes > 60:
        return (
            f"Respondés casi todo, pero tarde: la mitad de los clientes espera más de "
            f"{round(median_minutes)} minutos. Acortar ese tiempo suele mover más la aguja que "
            "cualquier cambio de oferta."
        )
    if last_week > 0 and this_week < last_week * 0.7:
        return (
            f"La atención está bien ({response.percent}% respondido), pero el volumen cayó de "
            f"{last_week} a {this_week} conversaciones. El problema hoy está antes: en cuánta "
            "gente te escribe."
        )
    return (
        f"Respondés {response.percent}% de las consultas y el volumen se sostiene "
        f"({this_week} esta semana). Con esta base ya tiene sentido optimizar conversión y ticket."
    )


def _methodology() -> list[str]:
    return [
        "Todo se cuenta sobre las filas reales de tu cuenta: conversaciones, mensajes y órdenes "
        "de tus negocios, nunca datos de la plataforma ni de otras cuentas.",
        "Una consulta cuenta como respondida sólo si hay un mensaje saliente posterior al mensaje "
        "del cliente en esa misma conversación.",
        "Los porcentajes vienen con intervalo de confianza de Wilson al 95%: con pocos casos, el "
        "porcentaje real puede estar bastante lejos del que se ve.",
        "Los tiempos se informan con mediana y cuartiles, no con promedio, para que un caso "
        "extremo no defina el número.",
        f"Con menos de {MIN_TO_READ} casos no se interpreta nada; con menos de {MIN_FOR_TREND} "
        "la lectura se marca como preliminar.",
    ]
