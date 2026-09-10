"""Authority service: measure, store, explain, and turn into work.

Everything is assembled from sources that already only contain the account's own
rows (web_presence, conversations, reviews, verification flags). No pillar can
be raised by anything other than the user actually doing something real, which
is the only way the trend line means anything.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import get_logger

from . import pillars as pillar_calc
from . import psychology
from .models import ActionMode, ActionStatus, AuthorityAction, AuthoritySnapshot

logger = get_logger(__name__)

#: Two snapshots closer than this are the same measurement for charting
#: purposes -- recomputing the page five times in a minute must not draw five
#: points and pretend they are history.
MIN_SNAPSHOT_GAP = timedelta(hours=6)


async def _safe_rollback(db: AsyncSession) -> None:
    """Undo a failed statement so the session stays usable.

    Postgres aborts the whole transaction on the first failing statement:
    every later query then dies with "current transaction is aborted". So an
    optional lookup that fails must roll back, or it takes the entire request
    down with it -- which is exactly what a missing table did here, turning a
    silent pre-existing 500 in one endpoint into a 500 in this one.
    """
    try:
        await db.rollback()
    except Exception:  # noqa: BLE001
        pass


async def _gather_context(db: AsyncSession, user) -> dict[str, Any]:
    """The account's real business identity, for grounding the advice."""
    ctx: dict[str, Any] = {}
    try:
        from app.domains.businesses.models import Business

        result = await db.execute(
            select(Business.id, Business.name).where(Business.user_id == user.id).limit(1)
        )
        row = result.first()
        if row:
            ctx["business_id"] = row[0]
            ctx["business_name"] = row[1]
    except Exception as e:  # noqa: BLE001
        logger.warning("authority: business lookup failed: %s", str(e)[:200])
        await _safe_rollback(db)

    try:
        from app.domains.business_context.models import BusinessContext

        result = await db.execute(
            select(BusinessContext).where(BusinessContext.user_id == user.id).limit(1)
        )
        context = result.scalar_one_or_none()
        if context is not None:
            ctx.update({
                "industry": context.industry,
                "business_type": context.business_type.value if context.business_type else None,
                "target_audience": context.target_audience,
                "value_proposition": context.value_proposition,
                "city": context.city,
            })
    except Exception as e:  # noqa: BLE001
        logger.warning("authority: context lookup failed: %s", str(e)[:200])
        await _safe_rollback(db)

    return ctx


async def compute_pillars(db: AsyncSession, user) -> tuple[dict[str, Any], dict[str, Any]]:
    """Run every pillar against this account's real data. Returns (pillars, context)."""
    from app.domains.ai_activity import service as ai_activity_service
    from app.domains.data_science import service as ds_service
    from app.domains.web_presence import service as wp_service

    context = await _gather_context(db, user)

    authority_report = await wp_service.authority_report(db, user.id)
    seo_report = await wp_service.seo_report(db, user.id)
    snapshot = await ai_activity_service.get_business_snapshot(db, user)

    # Median first-response time comes from the same analyst engine Analytics
    # uses, so both screens can never disagree about it.
    median_minutes: Optional[float] = None
    try:
        insights = await ds_service.get_insights(db, user, days=90)
        for reading in insights.get("readings", []):
            if reading.get("key") == "first_response_minutes":
                median_minutes = reading.get("value")
                break
    except Exception as e:  # noqa: BLE001
        logger.warning("authority: insights lookup failed: %s", str(e)[:200])
        await _safe_rollback(db)

    trust: dict[str, Any] | None = None
    business_id = context.get("business_id")
    if business_id:
        try:
            from app.api.v1.authority_building import calculate_trust_score

            trust = await calculate_trust_score(str(business_id), db)
        except Exception as e:  # noqa: BLE001
            logger.warning("authority: trust score failed: %s", str(e)[:200])
            await _safe_rollback(db)

    computed = {
        "identidad": pillar_calc.identidad(authority_report, context),
        "red": pillar_calc.red(authority_report),
        "prueba_social": pillar_calc.prueba_social(trust),
        "respuesta": pillar_calc.respuesta(snapshot.get("conversations", {}), median_minutes),
        "contenido": pillar_calc.contenido(seo_report),
        "verificacion": pillar_calc.verificacion(
            snapshot.get("verification", {}), len(snapshot.get("channels", []))
        ),
    }
    return computed, context


async def capture_snapshot(db: AsyncSession, user, force: bool = False) -> dict[str, Any]:
    """Measure now and store it, unless the last measurement is very recent.

    Returns plain values, never the ORM object: commit() expires every loaded
    instance, so reading `snapshot.total_score` after the later commit in
    sync_actions would trigger a lazy reload -- synchronous IO inside async,
    which SQLAlchemy refuses with MissingGreenlet.
    """
    computed, context = await compute_pillars(db, user)
    total = pillar_calc.total_score(computed)
    signals = pillar_calc.flatten_signals(computed)
    now = datetime.now(timezone.utc)

    last = await _latest_snapshot(db, user.id)
    last_captured_at = last.captured_at if last is not None else None

    if last is not None and not force and (now - last_captured_at) < MIN_SNAPSHOT_GAP:
        # Refresh the existing point instead of stacking a new one.
        last.total_score = total
        last.pillars = computed
        last.signals = signals
        last.captured_at = now
        await db.commit()
    else:
        db.add(AuthoritySnapshot(
            user_id=user.id,
            business_id=context.get("business_id"),
            captured_at=now,
            total_score=total,
            pillars=computed,
            signals=signals,
        ))
        await db.commit()

    await sync_actions(db, user, computed, context)
    return {"total_score": total, "captured_at": now, "pillars": computed}


async def _latest_snapshot(db: AsyncSession, user_id: uuid.UUID) -> Optional[AuthoritySnapshot]:
    result = await db.execute(
        select(AuthoritySnapshot)
        .where(AuthoritySnapshot.user_id == user_id)
        .order_by(AuthoritySnapshot.captured_at.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def sync_actions(
    db: AsyncSession, user, computed: dict[str, Any], context: dict[str, Any]
) -> list[AuthorityAction]:
    """Turn the agents' findings into stored work items.

    An action the user already marked done or dismissed is left alone: the point
    of storing them is that the user's decisions survive a recompute.
    """
    recommendations = psychology.run_agents(computed, context)
    by_key = {r.action_key: r for r in recommendations}

    result = await db.execute(
        select(AuthorityAction).where(AuthorityAction.user_id == user.id)
    )
    existing = {a.action_key: a for a in result.scalars().all()}

    for key, rec in by_key.items():
        action = existing.get(key)
        if action is None:
            db.add(AuthorityAction(
                user_id=user.id,
                business_id=context.get("business_id"),
                action_key=rec.action_key,
                pillar=rec.pillar,
                agent=rec.agent,
                principle=rec.principle,
                title=rec.title,
                rationale=rec.rationale,
                script=rec.script,
                channel=rec.channel,
                mode=rec.mode,
                impact_points=rec.impact_points,
            ))
        elif action.status == ActionStatus.SUGGESTED:
            # Keep the wording current with the numbers, but never resurrect a
            # decision the user already made.
            action.title = rec.title
            action.rationale = rec.rationale
            action.impact_points = rec.impact_points
            if not action.script:
                action.script = rec.script

    # A recommendation that no longer applies (the gap was closed) is marked
    # done rather than deleted, so the user sees what they achieved.
    for key, action in existing.items():
        if key not in by_key and action.status in (ActionStatus.SUGGESTED, ActionStatus.IN_PROGRESS):
            action.status = ActionStatus.DONE
            action.completed_at = datetime.now(timezone.utc)

    await db.commit()
    return await list_actions(db, user.id)


async def list_actions(db: AsyncSession, user_id: uuid.UUID) -> list[AuthorityAction]:
    result = await db.execute(
        select(AuthorityAction)
        .where(AuthorityAction.user_id == user_id)
        .order_by(AuthorityAction.status.asc(), AuthorityAction.impact_points.desc())
    )
    return list(result.scalars().all())


def serialize_action(action: AuthorityAction) -> dict[str, Any]:
    return {
        "id": str(action.id),
        "action_key": action.action_key,
        "pillar": action.pillar,
        "agent": action.agent,
        "principle": action.principle,
        "title": action.title,
        "rationale": action.rationale,
        "script": action.script,
        "channel": action.channel,
        "mode": action.mode.value if isinstance(action.mode, ActionMode) else str(action.mode),
        "status": action.status.value if isinstance(action.status, ActionStatus) else str(action.status),
        "impact_points": action.impact_points,
        "completed_at": action.completed_at.isoformat() if action.completed_at else None,
    }


async def set_action_status(
    db: AsyncSession, user_id: uuid.UUID, action_id: uuid.UUID, status: ActionStatus
) -> Optional[AuthorityAction]:
    result = await db.execute(
        select(AuthorityAction).where(
            AuthorityAction.id == action_id, AuthorityAction.user_id == user_id
        )
    )
    action = result.scalar_one_or_none()
    if action is None:
        return None
    action.status = status
    action.completed_at = datetime.now(timezone.utc) if status == ActionStatus.DONE else None
    await db.commit()
    await db.refresh(action)
    return action


async def get_trend(db: AsyncSession, user_id: uuid.UUID, limit: int = 60) -> list[dict[str, Any]]:
    result = await db.execute(
        select(AuthoritySnapshot)
        .where(AuthoritySnapshot.user_id == user_id)
        .order_by(AuthoritySnapshot.captured_at.asc())
        .limit(limit)
    )
    return [
        {
            "captured_at": s.captured_at.isoformat(),
            "date": s.captured_at.date().isoformat(),
            "total_score": s.total_score,
            "pillars": {k: v.get("score") for k, v in (s.pillars or {}).items()},
        }
        for s in result.scalars().all()
    ]


def analyze_trend(trend: list[dict[str, Any]], current: dict[str, Any]) -> dict[str, Any]:
    """The chart analyst.

    Reads the series the way someone who knows what a small sample is would:
    two points are a difference, not a trend, and it says so.
    """
    weakest = min(
        current.items(), key=lambda kv: kv[1].get("score", 0)
    ) if current else None
    strongest = max(
        current.items(), key=lambda kv: kv[1].get("score", 0)
    ) if current else None

    base: dict[str, Any] = {
        "direction": "unknown",
        "points": len(trend),
        "strongest_pillar": strongest[0] if strongest else None,
        "weakest_pillar": weakest[0] if weakest else None,
        "movements": [],
    }

    if len(trend) < 2:
        base["headline"] = (
            "Ésta es tu primera medición: es el punto de partida, todavía no hay tendencia. "
            "Volvé a medir después de aplicar algún cambio y el gráfico va a mostrar si funcionó."
        )
        base["detail"] = (
            f"Tu pilar más flojo hoy es «{pillar_calc.PILLARS[weakest[0]][0]}» "
            f"({weakest[1]['score']} de 100). Ahí es donde cada hora de trabajo rinde más."
            if weakest else ""
        )
        return base

    first, last = trend[0], trend[-1]
    delta = round(last["total_score"] - first["total_score"], 1)
    base["delta"] = delta
    base["direction"] = "up" if delta > 0 else "down" if delta < 0 else "flat"

    # Which pillar actually moved, comparing the same two snapshots.
    movements = []
    for key, (label, _) in pillar_calc.PILLARS.items():
        before = (first.get("pillars") or {}).get(key)
        after = (last.get("pillars") or {}).get(key)
        if before is None or after is None:
            continue
        change = round(after - before, 1)
        if abs(change) >= 0.5:
            movements.append({"pillar": key, "label": label, "change": change})
    movements.sort(key=lambda m: -abs(m["change"]))
    base["movements"] = movements[:4]

    if len(trend) == 2:
        base["headline"] = (
            f"Entre tus dos mediciones la autoridad {'subió' if delta > 0 else 'bajó' if delta < 0 else 'quedó igual'}"
            f" {abs(delta)} puntos. Son dos puntos: es un cambio, todavía no una tendencia."
        )
    else:
        verb = "viene subiendo" if delta > 0 else "viene bajando" if delta < 0 else "está estancada"
        base["headline"] = (
            f"Tu autoridad {verb}: {abs(delta)} puntos entre el {first['date']} y el {last['date']}, "
            f"sobre {len(trend)} mediciones."
        )

    if movements:
        top = movements[0]
        moved = "impulsada" if top["change"] > 0 else "arrastrada"
        base["detail"] = (
            f"El movimiento está {moved} sobre todo por «{top['label']}» "
            f"({'+' if top['change'] > 0 else ''}{top['change']} puntos)."
        )
    else:
        base["detail"] = (
            "Ningún pilar se movió de forma apreciable: lo que cambió el número es ruido, no trabajo."
        )

    if weakest:
        base["next_focus"] = (
            f"Para que la próxima medición suba, el mayor margen está en "
            f"«{pillar_calc.PILLARS[weakest[0]][0]}» ({weakest[1]['score']} de 100)."
        )

    return base


async def get_dashboard(db: AsyncSession, user) -> dict[str, Any]:
    """Everything the Authority screen needs, in one call."""
    snapshot = await capture_snapshot(db, user)
    trend = await get_trend(db, user.id)
    actions = await list_actions(db, user.id)
    computed = snapshot["pillars"]

    return {
        "total_score": snapshot["total_score"],
        "captured_at": snapshot["captured_at"].isoformat(),
        "pillars": [
            {
                "key": key,
                "label": label,
                "weight": weight,
                "score": computed.get(key, {}).get("score", 0.0),
                "inputs": computed.get(key, {}).get("inputs", {}),
                "missing": computed.get(key, {}).get("missing", []),
            }
            for key, (label, weight) in pillar_calc.PILLARS.items()
        ],
        "trend": trend,
        "analysis": analyze_trend(trend, computed),
        "actions": [serialize_action(a) for a in actions],
        "agents": [a.as_dict() for a in psychology.AGENTS],
    }


async def personalize_script(
    db: AsyncSession, user, action: AuthorityAction
) -> tuple[str, str]:
    """Rewrite an action's script in the account's own voice using the real LLM.

    Returns (script, source) where source is 'ia' or 'plantilla' -- the UI says
    which one it is, because a template dressed as AI output is the same kind of
    lie as an invented metric.
    """
    context = await _gather_context(db, user)
    business_id = context.get("business_id")
    if not business_id or not action.script:
        return action.script or "", "plantilla"

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        from app.domains.agents.llm_provider import generate_with_fallback

        system = SystemMessage(content=(
            "Sos un especialista en comunicación de marca para pymes de Latinoamérica. "
            "Reescribís un mensaje para que suene humano, concreto y en la voz del negocio. "
            "Reglas estrictas: no inventes datos, precios, plazos ni estadísticas; no prometas "
            "resultados; no uses urgencia falsa; mantené los marcadores entre llaves tal como "
            "están; escribí en español rioplatense, tuteando, en menos de 120 palabras."
        ))
        human = HumanMessage(content=(
            f"Negocio: {context.get('business_name') or 'sin nombre'}\n"
            f"Rubro: {context.get('industry') or context.get('business_type') or 'no declarado'}\n"
            f"Público: {context.get('target_audience') or 'no declarado'}\n"
            f"Propuesta de valor: {context.get('value_proposition') or 'no declarada'}\n"
            f"Canal: {action.channel or 'general'}\n"
            f"Objetivo del mensaje: {action.title}\n\n"
            f"Mensaje base a reescribir:\n{action.script}"
        ))

        response = await generate_with_fallback(
            db=db,
            business_id=business_id,
            messages=[system, human],
            max_tokens=500,
            temperature=0.7,
        )
        if response and response.content.strip():
            return response.content.strip(), "ia"
    except Exception as e:  # noqa: BLE001
        logger.warning("authority: personalize_script failed: %s", str(e)[:200])

    return action.script, "plantilla"
