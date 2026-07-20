"""Auto-Responder Pilot Agent Service"""

import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func, and_

from app.core.logger import get_logger
from app.domains.agents.auto_responder.models import AutoResponderRule, AutoResponseLog
from app.domains.channels.models import Conversation, Message
from app.domains.memory.service import MemoryEngine
from app.domains.agents.ai_reply import generate_raw_ai_response

logger = get_logger(__name__)

BUY_SIGNALS = [
    "comprar", "compro", "adquirir", "quiero", "precio", "cotización",
    "cotizacion", "presupuesto", "pagar", "tarjeta", "transferencia",
    "factura", "confirmo", "dale", "lo quiero", "me interesa",
]


async def check_and_respond(db: AsyncSession, business_id: uuid.UUID) -> List[Dict[str, Any]]:
    """
    Celery task logic that checks for conversations matching trigger rules
    and sends auto-responses.
    """
    results: List[Dict[str, Any]] = []

    # Load active rules for business
    rules_result = await db.execute(
        select(AutoResponderRule)
        .where(
            AutoResponderRule.business_id == business_id,
            AutoResponderRule.is_active == True,
        )
        .order_by(AutoResponderRule.priority.desc())
    )
    rules = rules_result.scalars().all()
    if not rules:
        return results

    now = datetime.now(timezone.utc)

    for rule in rules:
        matched_conversations = await _find_matching_conversations(db, business_id, rule, now)
        for conv in matched_conversations:
            # Skip if already auto-responded recently
            recent_log = await db.execute(
                select(AutoResponseLog)
                .where(
                    AutoResponseLog.conversation_id == conv.id,
                    AutoResponseLog.rule_id == rule.id,
                    AutoResponseLog.created_at >= now - timedelta(hours=1),
                )
            )
            if recent_log.scalar_one_or_none():
                continue

            # Load customer profile from memory
            memory_engine = MemoryEngine(db)
            customer_memories = []
            try:
                customer_id = conv.extra_data.get("customer_id") if conv.extra_data else None
                if customer_id:
                    profile = await memory_engine.get_customer_profile_summary(uuid.UUID(customer_id))
                    customer_memories = [profile] if profile else []
            except Exception as e:
                logger.warning(f"Memory load failed for conversation {conv.id}: {e}")

            # Check for buy-ready signals
            last_msg_result = await db.execute(
                select(Message)
                .where(Message.conversation_id == conv.id)
                .order_by(desc(Message.created_at))
                .limit(1)
            )
            last_msg = last_msg_result.scalar_one_or_none()
            has_buy_signal = False
            if last_msg and last_msg.content:
                content_lower = last_msg.content.lower()
                has_buy_signal = any(sig in content_lower for sig in BUY_SIGNALS)

            # Generate personalized response
            system_prompt = (
                "Eres un asistente de ventas automático. Genera una respuesta personalizada "
                "usando la plantilla de la regla y el contexto del cliente.\n\n"
                f"Plantilla base:\n{rule.response_template}\n\n"
            )
            if customer_memories:
                system_prompt += f"Perfil del cliente:\n{customer_memories[0]}\n\n"
            if has_buy_signal:
                system_prompt += (
                    "IMPORTANTE: El cliente muestra señales de compra. "
                    "Prioriza cerrar la venta o agendar una llamada.\n"
                )

            response_text = await generate_raw_ai_response(
                db=db,
                business_id=business_id,
                system_prompt=system_prompt,
                user_prompt=(
                    f"Último mensaje del cliente: {last_msg.content if last_msg else 'N/A'}\n\n"
                    "Genera la respuesta automática:"
                ),
                max_tokens=600,
                temperature=0.6,
            )
            if not response_text:
                response_text = rule.response_template

            # Log response
            log = AutoResponseLog(
                rule_id=rule.id,
                conversation_id=conv.id,
                trigger_fired=rule.trigger_type,
                response_sent=response_text,
                outcome="converted" if has_buy_signal else None,
            )
            db.add(log)

            results.append({
                "conversation_id": conv.id,
                "rule_id": rule.id,
                "trigger_type": rule.trigger_type,
                "response_sent": response_text,
                "has_buy_signal": has_buy_signal,
            })

    await db.commit()
    return results


async def _find_matching_conversations(
    db: AsyncSession,
    business_id: uuid.UUID,
    rule: AutoResponderRule,
    now: datetime,
) -> List[Conversation]:
    """Find conversations matching a rule's trigger conditions."""
    stmt = select(Conversation).where(
        Conversation.business_id == business_id,
        Conversation.is_active == True,
    )

    if rule.trigger_type == "inactivity":
        hours = rule.trigger_config.get("hours", 2)
        cutoff = now - timedelta(hours=hours)
        # Conversations with no message since cutoff
        subq = (
            select(Message.conversation_id)
            .where(Message.created_at >= cutoff)
            .subquery()
        )
        stmt = stmt.where(~Conversation.id.in_(subq))
    elif rule.trigger_type == "keyword":
        keywords = rule.trigger_config.get("keywords", [])
        if keywords:
            # Find conversations with recent messages containing keywords
            keyword_patterns = [f"%{k}%" for k in keywords]
            # Simplified: match any of the keywords in recent messages
            # For production, use full-text search or a more robust approach
            msg_stmt = select(Message.conversation_id).where(
                Message.content.ilike(f"%{keywords[0]}%")
            )
            for kw in keywords[1:]:
                msg_stmt = msg_stmt.union(
                    select(Message.conversation_id).where(Message.content.ilike(f"%{kw}%"))
                )
            subq = msg_stmt.subquery()
            stmt = stmt.where(Conversation.id.in_(subq))
    elif rule.trigger_type == "time_of_day":
        # Time-based: after hours
        tz_name = rule.trigger_config.get("timezone", "UTC")
        try:
            import zoneinfo
            tz = zoneinfo.ZoneInfo(tz_name)
        except Exception:
            tz = timezone.utc
        local_now = now.astimezone(tz)
        start_str = rule.trigger_config.get("start", "18:00")
        end_str = rule.trigger_config.get("end", "08:00")
        start_h, start_m = map(int, start_str.split(":"))
        end_h, end_m = map(int, end_str.split(":"))
        start_min = start_h * 60 + start_m
        end_min = end_h * 60 + end_m
        current_min = local_now.hour * 60 + local_now.minute
        if start_min <= end_min:
            in_range = start_min <= current_min <= end_min
        else:
            in_range = current_min >= start_min or current_min <= end_min
        if not in_range:
            return []
    elif rule.trigger_type == "day_of_week":
        days = rule.trigger_config.get("days", [])
        if not days:
            return []
        current_day = now.strftime("%A").lower()
        if current_day not in [d.lower() for d in days]:
            return []

    result = await db.execute(stmt)
    return result.scalars().all()


async def create_rule(
    db: AsyncSession,
    business_id: uuid.UUID,
    data: Dict[str, Any],
) -> AutoResponderRule:
    rule = AutoResponderRule(business_id=business_id, **data)
    db.add(rule)
    await db.commit()
    await db.refresh(rule)
    return rule


async def list_rules(
    db: AsyncSession,
    business_id: uuid.UUID,
    active_only: bool = True,
) -> List[AutoResponderRule]:
    stmt = select(AutoResponderRule).where(AutoResponderRule.business_id == business_id)
    if active_only:
        stmt = stmt.where(AutoResponderRule.is_active == True)
    stmt = stmt.order_by(desc(AutoResponderRule.priority), AutoResponderRule.created_at)
    result = await db.execute(stmt)
    return result.scalars().all()


async def get_rule(db: AsyncSession, rule_id: uuid.UUID) -> Optional[AutoResponderRule]:
    result = await db.execute(
        select(AutoResponderRule).where(AutoResponderRule.id == rule_id)
    )
    return result.scalar_one_or_none()


async def update_rule(
    db: AsyncSession,
    rule_id: uuid.UUID,
    data: Dict[str, Any],
) -> AutoResponderRule:
    rule = await get_rule(db, rule_id)
    if not rule:
        raise ValueError("Rule not found")
    for key, value in data.items():
        if hasattr(rule, key) and value is not None:
            setattr(rule, key, value)
    await db.commit()
    await db.refresh(rule)
    return rule


async def delete_rule(db: AsyncSession, rule_id: uuid.UUID) -> bool:
    rule = await get_rule(db, rule_id)
    if not rule:
        return False
    await db.delete(rule)
    await db.commit()
    return True


async def get_response_stats(
    db: AsyncSession,
    business_id: uuid.UUID,
    days: int = 7,
) -> Dict[str, Any]:
    """Return auto-response statistics for a business."""
    since = datetime.now(timezone.utc) - timedelta(days=days)

    total_sent_result = await db.execute(
        select(func.count(AutoResponseLog.id))
        .join(AutoResponderRule)
        .where(
            AutoResponderRule.business_id == business_id,
            AutoResponseLog.created_at >= since,
        )
    )
    total_sent = total_sent_result.scalar() or 0

    total_replied_result = await db.execute(
        select(func.count(AutoResponseLog.id))
        .join(AutoResponderRule)
        .where(
            AutoResponderRule.business_id == business_id,
            AutoResponseLog.created_at >= since,
            AutoResponseLog.customer_replied == True,
        )
    )
    total_replied = total_replied_result.scalar() or 0

    converted_result = await db.execute(
        select(func.count(AutoResponseLog.id))
        .join(AutoResponderRule)
        .where(
            AutoResponderRule.business_id == business_id,
            AutoResponseLog.created_at >= since,
            AutoResponseLog.outcome == "converted",
        )
    )
    converted = converted_result.scalar() or 0

    conversion_rate = (converted / total_sent * 100) if total_sent > 0 else 0.0

    # Stats by rule
    by_rule_result = await db.execute(
        select(
            AutoResponderRule.id,
            AutoResponderRule.rule_name,
            func.count(AutoResponseLog.id).label("sent"),
        )
        .join(AutoResponseLog, AutoResponseLog.rule_id == AutoResponderRule.id)
        .where(
            AutoResponderRule.business_id == business_id,
            AutoResponseLog.created_at >= since,
        )
        .group_by(AutoResponderRule.id, AutoResponderRule.rule_name)
    )
    by_rule = [
        {"rule_id": r_id, "rule_name": r_name, "sent": sent}
        for r_id, r_name, sent in by_rule_result.all()
    ]

    return {
        "business_id": business_id,
        "total_sent": total_sent,
        "total_replied": total_replied,
        "conversion_rate": round(conversion_rate, 2),
        "by_rule": by_rule,
        "period_days": days,
    }


async def list_logs(
    db: AsyncSession,
    business_id: uuid.UUID,
    limit: int = 100,
    offset: int = 0,
) -> List[AutoResponseLog]:
    result = await db.execute(
        select(AutoResponseLog)
        .join(AutoResponderRule)
        .where(AutoResponderRule.business_id == business_id)
        .order_by(desc(AutoResponseLog.created_at))
        .limit(limit)
        .offset(offset)
    )
    return result.scalars().all()
