"""Qué hacer ahora: actions computed from this account's own data.

This replaces a set of screens that could not help anybody. "Misiones",
"Leaderboard", "Radar", "Ambassador", "Marketplace" and "Battlecards" all called
routers that do not exist in this deployment — every one of them answered 404,
so the pages loaded, asked, and showed nothing. And even working, a leaderboard
ranking a ceramics seller against strangers, a badge to collect, or an add-on
store would not have sold one more mug.

What a seller can actually use is the answer to three questions, and all three
are computable from rows that already exist:

* What should I do right now, and why — with the number that justifies it.
* What of MINE is working: which product, which customer, which channel, which day.
* Which conversation do I answer first.

Every action here carries its evidence. Nothing claims a percentage lift: the
effect of answering a waiting buyer is not measurable in advance, so the action
states the fact ("3 consultas esperan desde hace más de 4 horas") and leaves the
conclusion to the person who owns the business.
"""

from __future__ import annotations

import uuid
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

logger = get_logger(__name__)

#: Hours after which a buyer waiting for an answer is a problem, not a pending task.
STALE_REPLY_HOURS = 4
#: Days after which an unpaid order is unlikely to pay itself.
UNPAID_DAYS = 2
#: Days after which a paid order that never shipped is a complaint waiting to happen.
UNSHIPPED_DAYS = 2
#: Days without buying that make a past customer worth contacting again.
DORMANT_DAYS = 45


@dataclass
class Action:
    """One thing to do, with the evidence that justifies it."""

    key: str
    title: str
    #: The fact, with its numbers. Never a prediction.
    evidence: str
    #: Why it matters for the money, stated plainly.
    why: str
    #: high = money or a customer is at stake right now.
    urgency: str
    where: str
    #: The count this action is about, for sorting and for the UI badge.
    size: int = 0
    extra: dict[str, Any] = field(default_factory=dict)


URGENCY_ORDER = {"alta": 0, "media": 1, "baja": 2}


@dataclass
class Ctx:
    """What every check needs. Passed explicitly: a module-level variable here
    would be shared by concurrent requests and leak one account's id into
    another's check."""

    db: AsyncSession
    user_id: uuid.UUID
    business_ids: list[uuid.UUID]
    now: datetime


def _aware(value: Optional[datetime]) -> Optional[datetime]:
    if value is None:
        return None
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


async def _business_ids(db: AsyncSession, user_id: uuid.UUID) -> list[uuid.UUID]:
    from app.domains.businesses.models import Business

    result = await db.execute(select(Business.id).where(Business.user_id == user_id))
    return [row[0] for row in result.all()]


async def compute_actions(db: AsyncSession, user: Any) -> dict[str, Any]:
    """The prioritised list of what to do, each item with its numbers."""
    now = datetime.now(timezone.utc)
    business_ids = await _business_ids(db, user.id)
    if not business_ids:
        return {
            "actions": [
                Action(
                    key="create_business",
                    title="Creá tu negocio",
                    evidence="Todavía no hay ningún negocio en la cuenta.",
                    why="Sin un negocio no hay dónde guardar tus ventas, canales ni conversaciones.",
                    urgency="alta",
                    where="/dashboard/negocios",
                ).__dict__
            ],
            "generated_at": now.isoformat(),
            "checked": [],
        }

    actions: list[Action] = []
    checked: list[str] = []

    ctx = Ctx(db=db, user_id=user.id, business_ids=business_ids, now=now)
    for builder in (
        _waiting_conversations,
        _bot_off_where_traffic_is,
        _unpaid_orders,
        _unshipped_orders,
        _customers_without_contact,
        _dormant_customers,
        _incomplete_profile,
        _ai_not_configured,
        _channel_gaps,
        _reach_opportunity,
    ):
        try:
            found = await builder(ctx)
            checked.append(builder.__name__.lstrip("_"))
            actions.extend(found)
        except Exception as e:  # noqa: BLE001
            # One unavailable source must not take the whole list down, and the
            # response says which check could not run rather than implying
            # everything is fine.
            logger.warning("next_steps: %s failed: %s", builder.__name__, str(e)[:200])
            try:
                await db.rollback()
            except Exception:  # noqa: BLE001
                pass

    actions.sort(key=lambda a: (URGENCY_ORDER.get(a.urgency, 3), -a.size))
    return {
        "actions": [action.__dict__ for action in actions],
        "checked": checked,
        "not_checked": [
            name for name in (
                "waiting_conversations", "bot_off_where_traffic_is", "unpaid_orders",
                "unshipped_orders", "customers_without_contact", "dormant_customers",
                "incomplete_profile", "ai_not_configured", "channel_gaps",
                "reach_opportunity",
            ) if name not in checked
        ],
        "generated_at": now.isoformat(),
    }


async def _waiting_conversations(ctx: "Ctx") -> list[Action]:
    """Buyers whose last message got no answer."""
    db, business_ids, now = ctx.db, ctx.business_ids, ctx.now
    from app.domains.channels.models import (
        ChannelConnection, Conversation, Message, MessageDirection,
    )

    convs = await db.execute(
        select(Conversation.id, ChannelConnection.platform)
        .join(ChannelConnection, Conversation.channel_connection_id == ChannelConnection.id)
        .where(Conversation.business_id.in_(business_ids), Conversation.is_active.is_(True))
    )
    platform_of = {
        row[0]: (row[1].value if hasattr(row[1], "value") else str(row[1]))
        for row in convs.all()
    }
    if not platform_of:
        return []

    messages = await db.execute(
        select(Message.conversation_id, Message.direction, Message.created_at)
        .where(Message.conversation_id.in_(list(platform_of)))
        .order_by(Message.created_at.asc())
    )
    last: dict[Any, tuple[Any, datetime]] = {}
    for conv_id, direction, created in messages.all():
        last[conv_id] = (direction, _aware(created))

    waiting = [
        (conv_id, created)
        for conv_id, (direction, created) in last.items()
        if direction == MessageDirection.INBOUND and created
    ]
    if not waiting:
        return []

    stale = [(c, t) for c, t in waiting if (now - t) >= timedelta(hours=STALE_REPLY_HOURS)]
    oldest = min((t for _, t in waiting), default=None)
    hours = round((now - oldest).total_seconds() / 3600, 1) if oldest else 0
    by_platform = Counter(platform_of[c] for c, _ in waiting)

    return [
        Action(
            key="waiting_conversations",
            title=f"Respondé {len(waiting)} consulta(s) que están esperando",
            evidence=(
                f"{len(waiting)} conversación(es) cuyo último mensaje es del comprador. "
                f"{len(stale)} lleva(n) más de {STALE_REPLY_HOURS} horas sin respuesta; "
                f"la más vieja espera hace {hours} horas. "
                + " · ".join(f"{platform}: {count}" for platform, count in by_platform.most_common())
            ),
            why=(
                "Una consulta sin responder es una venta que se va a otro lado sin dejar rastro. "
                "Es lo único de esta lista que pierde plata mientras lo leés."
            ),
            urgency="alta" if stale else "media",
            where="/dashboard/conversaciones",
            size=len(waiting),
            extra={"stale": len(stale), "oldest_hours": hours},
        )
    ]


async def _bot_off_where_traffic_is(ctx: "Ctx") -> list[Action]:
    """Platforms that receive questions while their bot is switched off."""
    db, business_ids = ctx.db, ctx.business_ids
    from app.domains.channels.models import (
        ChannelConnection, Conversation, Message, MessageDirection,
    )
    from app.domains.chatbots.models import PlatformBot

    convs = await db.execute(
        select(Conversation.id, ChannelConnection.platform)
        .join(ChannelConnection, Conversation.channel_connection_id == ChannelConnection.id)
        .where(Conversation.business_id.in_(business_ids))
    )
    platform_of = {
        row[0]: (row[1].value if hasattr(row[1], "value") else str(row[1]))
        for row in convs.all()
    }
    if not platform_of:
        return []

    inbound = await db.execute(
        select(Message.conversation_id)
        .where(
            Message.conversation_id.in_(list(platform_of)),
            Message.direction == MessageDirection.INBOUND,
        )
    )
    traffic: Counter[str] = Counter()
    for (conv_id,) in inbound.all():
        traffic[platform_of[conv_id]] += 1
    if not traffic:
        return []

    bots = await db.execute(
        select(PlatformBot.platform, PlatformBot.enabled).where(
            PlatformBot.business_id.in_(business_ids)
        )
    )
    enabled = {row[0]: bool(row[1]) for row in bots.all()}

    actions = []
    for platform, count in traffic.most_common(3):
        if enabled.get(platform) is True:
            continue
        configured = platform in enabled
        actions.append(
            Action(
                key=f"bot_off_{platform}",
                title=f"Encendé el bot de {platform}",
                evidence=(
                    f"{platform} recibió {count} mensaje(s) de compradores y su bot está "
                    + ("apagado." if configured else "sin configurar.")
                ),
                why=(
                    "El bot contesta en el momento en que el comprador pregunta, que es cuando "
                    "está decidiendo. Podés ponerle horario y palabras que lo hagan pasarte la "
                    "conversación."
                ),
                urgency="media",
                where="/dashboard/conversaciones",
                size=count,
                extra={"platform": platform, "configured": configured},
            )
        )
    return actions


async def _unpaid_orders(ctx: "Ctx") -> list[Action]:
    """Orders that were closed but never paid."""
    db, business_ids, now = ctx.db, ctx.business_ids, ctx.now
    from app.domains.orders.models import Order, OrderStatus

    result = await db.execute(
        select(Order.id, Order.total_amount, Order.currency, Order.created_at, Order.order_number)
        .where(
            Order.business_id.in_(business_ids),
            Order.is_active.is_(True),
            Order.status == OrderStatus.PENDING,
        )
    )
    rows = [r for r in result.all() if _aware(r[3]) and (now - _aware(r[3])) >= timedelta(days=UNPAID_DAYS)]
    if not rows:
        return []

    by_currency: dict[str, float] = defaultdict(float)
    for _id, amount, currency, _created, _number in rows:
        by_currency[currency or "?"] += float(amount or 0)
    amounts = " · ".join(
        f"{round(total)} {currency}" for currency, total in sorted(by_currency.items(), key=lambda kv: -kv[1])
    )
    oldest = min(_aware(r[3]) for r in rows)
    days = (now - oldest).days

    return [
        Action(
            key="unpaid_orders",
            title=f"Cobrá {len(rows)} orden(es) pendiente(s)",
            evidence=(
                f"{len(rows)} orden(es) siguen en pendiente hace más de {UNPAID_DAYS} días, "
                f"por {amounts}. La más vieja lleva {days} días."
            ),
            why=(
                "Ya dijeron que sí: recuperar una de estas cuesta un mensaje, mucho menos que "
                "conseguir un cliente nuevo. Las monedas se muestran separadas porque no se suman."
            ),
            urgency="alta",
            where="/dashboard/ordenes",
            size=len(rows),
            extra={"by_currency": dict(by_currency), "oldest_days": days},
        )
    ]


async def _unshipped_orders(ctx: "Ctx") -> list[Action]:
    """Paid orders that never moved."""
    db, business_ids, now = ctx.db, ctx.business_ids, ctx.now
    from app.domains.orders.models import Order, OrderStatus

    result = await db.execute(
        select(Order.id, Order.paid_at, Order.created_at, Order.order_number)
        .where(
            Order.business_id.in_(business_ids),
            Order.is_active.is_(True),
            Order.status == OrderStatus.PAID,
        )
    )
    rows = []
    for _id, paid_at, created_at, number in result.all():
        since = _aware(paid_at) or _aware(created_at)
        if since and (now - since) >= timedelta(days=UNSHIPPED_DAYS):
            rows.append((number, since))
    if not rows:
        return []

    oldest = min(since for _, since in rows)
    days = (now - oldest).days
    return [
        Action(
            key="unshipped_orders",
            title=f"Despachá {len(rows)} orden(es) ya pagada(s)",
            evidence=(
                f"{len(rows)} orden(es) están pagadas y sin enviar hace más de {UNSHIPPED_DAYS} "
                f"días. La más vieja lleva {days} días cobrada."
            ),
            why=(
                "Ya cobraste: acá no se gana plata, se pierde reputación. Es de donde salen los "
                "reclamos y las malas reseñas."
            ),
            urgency="alta",
            where="/dashboard/ordenes",
            size=len(rows),
            extra={"oldest_days": days},
        )
    ]


async def _customers_without_contact(ctx: "Ctx") -> list[Action]:
    """Sales you cannot follow up, because nobody recorded who bought."""
    db, business_ids = ctx.db, ctx.business_ids
    from app.domains.orders.models import Order

    result = await db.execute(
        select(Order.customer_email, Order.customer_phone)
        .where(Order.business_id.in_(business_ids), Order.is_active.is_(True))
    )
    rows = result.all()
    if not rows:
        return []
    missing = sum(
        1 for email, phone in rows
        if not (email or "").strip() and not (phone or "").strip()
    )
    if missing == 0 or missing < max(2, len(rows) * 0.2):
        return []

    return [
        Action(
            key="customers_without_contact",
            title=f"Completá el contacto de {missing} orden(es)",
            evidence=f"{missing} de {len(rows)} órdenes no tienen email ni teléfono del comprador.",
            why=(
                "Sin email ni teléfono no se puede saber si un cliente volvió, ni volver a "
                "venderle. Es lo que hace posible medir recompra, que es lo que decide si creces "
                "o reponés clientes todo el tiempo."
            ),
            urgency="media",
            where="/dashboard/ordenes",
            size=missing,
        )
    ]


async def _dormant_customers(ctx: "Ctx") -> list[Action]:
    """Customers who bought once and have not come back."""
    db, business_ids, now = ctx.db, ctx.business_ids, ctx.now
    from app.domains.orders.models import Order, PaymentStatus

    result = await db.execute(
        select(Order.customer_email, Order.customer_phone, Order.created_at, Order.total_amount, Order.currency)
        .where(
            Order.business_id.in_(business_ids),
            Order.is_active.is_(True),
            Order.payment_status == PaymentStatus.COMPLETED,
        )
    )
    last_seen: dict[str, datetime] = {}
    spent: dict[str, float] = defaultdict(float)
    currency_of: dict[str, str] = {}
    for email, phone, created, amount, currency in result.all():
        key = (email or "").strip().lower() or (phone or "").strip()
        if not key:
            continue
        created = _aware(created)
        if not created:
            continue
        if key not in last_seen or created > last_seen[key]:
            last_seen[key] = created
        spent[key] += float(amount or 0)
        currency_of[key] = currency or "?"

    dormant = [
        key for key, seen in last_seen.items()
        if (now - seen) >= timedelta(days=DORMANT_DAYS)
    ]
    if not dormant:
        return []

    by_currency: dict[str, float] = defaultdict(float)
    for key in dormant:
        by_currency[currency_of[key]] += spent[key]
    amounts = " · ".join(f"{round(total)} {currency}" for currency, total in by_currency.items())
    oldest_days = max((now - last_seen[key]).days for key in dormant)

    return [
        Action(
            key="dormant_customers",
            title=f"Volvé a escribirle a {len(dormant)} cliente(s) que no vuelven",
            evidence=(
                f"{len(dormant)} cliente(s) con compra pagada no compran desde hace más de "
                f"{DORMANT_DAYS} días (el más antiguo, {oldest_days} días). Ya te dejaron {amounts}."
            ),
            why=(
                "Venderle de nuevo a quien ya te compró cuesta mucho menos que conseguir un "
                "cliente nuevo, y estos ya saben cómo es tu producto."
            ),
            urgency="media",
            where="/dashboard/clientes",
            size=len(dormant),
            extra={"by_currency": dict(by_currency)},
        )
    ]


async def _incomplete_profile(ctx: "Ctx") -> list[Action]:
    """Configuration the AI needs and does not have."""
    from app.domains.preferences import service as preferences

    profile = await preferences.load_profile(ctx.db, ctx.user_id, ctx.business_ids[0])
    if not profile:
        return []
    missing = profile.get("completeness", {}).get("missing") or []
    if not missing:
        return []
    labels = ", ".join(item["label"] for item in missing[:5])
    return [
        Action(
            key="incomplete_profile",
            title="Completá lo que la IA necesita saber de tu negocio",
            evidence=(
                f"Faltan {len(missing)} dato(s) que cambian cómo vende la IA: {labels}."
            ),
            why=(
                "El bot ya está respondiendo; sin estos datos responde sin saber tu nicho, a quién "
                "le vendés ni en qué idiomas, y suena como cualquiera."
            ),
            urgency="media" if len(missing) < 5 else "alta",
            where="/dashboard/configuracion",
            size=len(missing),
        )
    ]


async def _ai_not_configured(ctx: "Ctx") -> list[Action]:
    """No AI provider key means every "AI" answer is a template."""
    from app.domains.integrations import registry

    status = registry.status()
    ai_group = [
        item for item in status.get("integrations", [])
        if item.get("category") in ("ai", "llm") or item.get("key", "").lower() in ("anthropic", "openai", "groq")
    ]
    if not ai_group:
        return []
    configured = [item for item in ai_group if item.get("configured")]
    if configured:
        return []
    names = ", ".join(item.get("label", item.get("key", "")) for item in ai_group[:4])
    return [
        Action(
            key="ai_not_configured",
            title="Configurá una clave de IA",
            evidence=f"Ninguno de los proveedores de IA está configurado ({names}).",
            why=(
                "Sin clave, el bot no puede generar respuestas: contesta con plantillas o no "
                "contesta. Todo lo que dependa de IA queda apagado hasta que haya una."
            ),
            urgency="alta",
            where="/dashboard/configuracion",
            size=len(ai_group),
        )
    ]


# ── Recovered from the page this engine replaced ───────────────────────────
# The old "Misiones" screen was not entirely dead: alongside the /missions calls
# that 404, it read /business-context/channel-gaps, /reach-analysis and
# /recommended-playbooks, and those three ARE live and return real analysis
# (critical channels missing, whether the business could sell beyond its current
# reach, and which playbooks fit its type). Replacing the page dropped them, so
# they come back here — prioritised alongside everything else instead of sitting
# in a separate tab.


async def _channel_gaps(ctx: "Ctx") -> list[Action]:
    """Channels this kind of business needs and does not have connected."""
    from app.domains.business_context.service import BusinessContextService

    service = BusinessContextService(ctx.db)
    context = await service.get_or_create_context(ctx.user_id, ctx.business_ids[0])
    gaps = await service.analyze_channel_gaps(ctx.user_id, context.id)

    critical = [gap for gap in gaps if not gap.is_configured and gap.priority == "critical"]
    if not critical:
        return []

    names = ", ".join(gap.channel for gap in critical)
    playbooks = [gap.recommended_playbook for gap in critical if gap.recommended_playbook]
    return [
        Action(
            key="channel_gaps",
            title=f"Te faltan {len(critical)} canal(es) que tu rubro necesita",
            evidence=(
                f"Sin conectar: {names}. "
                + " · ".join(f"{gap.channel}: {gap.impact_estimate}" for gap in critical[:3])
            ),
            why=(
                "Son los canales donde tus compradores ya están buscando lo que vendés. "
                "Un canal que no existe no recibe consultas, y esto no se arregla vendiendo mejor "
                "en los que ya tenés."
            ),
            urgency="media",
            where="/dashboard/canales",
            size=len(critical),
            extra={
                "channels": [gap.channel for gap in critical],
                "playbooks": playbooks,
                "difficulty": {gap.channel: gap.setup_difficulty for gap in critical},
            },
        )
    ]


async def _reach_opportunity(ctx: "Ctx") -> list[Action]:
    """When the business could sell beyond where it sells today."""
    from app.domains.business_context.service import BusinessContextService

    service = BusinessContextService(ctx.db)
    context = await service.get_or_create_context(ctx.user_id, ctx.business_ids[0])
    reach = await service.analyze_reach(ctx.user_id, context.id)

    current = getattr(reach, "current_reach", None)
    recommended = getattr(reach, "recommended_reach", None)
    if not current or not recommended or current == recommended:
        return []

    labels = {
        "local": "tu ciudad",
        "regional": "tu provincia o región",
        "national": "todo el país",
        "cross_border": "los países vecinos",
        "global": "el mundo",
    }
    shipping = list(getattr(reach, "shipping_recommendations", []) or [])
    platforms = list(getattr(reach, "platform_recommendations", []) or [])
    pieces = []
    if platforms:
        pieces.append("Plataformas que llegan ahí: " + ", ".join(platforms[:4]) + ".")
    if shipping:
        pieces.append("Envíos: " + ", ".join(shipping[:3]) + ".")

    return [
        Action(
            key="reach_opportunity",
            title=f"Podrías vender en {labels.get(recommended, recommended)}",
            evidence=(
                f"Hoy vendés en {labels.get(current, current)} y tu tipo de negocio puede llegar a "
                f"{labels.get(recommended, recommended)}. " + " ".join(pieces)
            ),
            why=(
                "Es la única acción de esta lista que agranda el mercado en vez de exprimir el "
                "que ya tenés. No promete ventas: dice que el techo actual es una decisión, no un límite."
            ),
            # Lower than anything with money or a customer waiting: expanding is
            # never more urgent than answering someone who is already buying.
            urgency="baja",
            where="/dashboard/configuracion",
            size=1,
            extra={
                "current_reach": current,
                "recommended_reach": recommended,
                "platforms": platforms,
                "shipping": shipping,
            },
        )
    ]
