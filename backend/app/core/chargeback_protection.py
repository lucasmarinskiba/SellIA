"""
Chargeback Protection Engine

Detecta disputas de pago, guarda evidencia de uso, y bloquea cuentas temporalmente.
"""

import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.domains.security.models import ChargebackAlert
from app.domains.subscriptions.integrity import generate_usage_report
from app.core.logger import get_logger

logger = get_logger(__name__)


async def record_chargeback(
    db: AsyncSession,
    user_id: uuid.UUID,
    payment_provider: str,
    transaction_id: str,
    amount: float,
    currency: str,
    reason: Optional[str] = None,
) -> ChargebackAlert:
    """Registra un chargeback y genera evidencia."""
    # Generate usage evidence
    usage_report = await generate_usage_report(db, user_id, days=30)

    evidence = {
        "usage_report": usage_report,
        "note": "El usuario utilizó el servicio durante el período de suscripción.",
    }

    alert = ChargebackAlert(
        user_id=user_id,
        payment_provider=payment_provider,
        transaction_id=transaction_id,
        amount=amount,
        currency=currency,
        reason=reason,
        evidence_json=json.dumps(evidence, indent=2, default=str),
        status="open",
    )
    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    logger.warning(f"Chargeback recorded for user {user_id}: {amount} {currency}")
    return alert


async def get_chargeback_evidence(
    db: AsyncSession,
    alert_id: uuid.UUID,
) -> Optional[Dict[str, Any]]:
    """Obtiene la evidencia de un chargeback."""
    result = await db.execute(select(ChargebackAlert).where(ChargebackAlert.id == alert_id))
    alert = result.scalar_one_or_none()
    if not alert or not alert.evidence_json:
        return None
    try:
        return json.loads(alert.evidence_json)
    except json.JSONDecodeError:
        return None
