"""
Coupon Service
"""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.domains.coupons.models import Coupon, CouponUsage


async def validate_coupon(db: AsyncSession, code: str, user_id: uuid.UUID, plan_id: Optional[str] = None, amount: float = 0) -> dict:
    result = await db.execute(select(Coupon).where(Coupon.code == code.upper()))
    coupon = result.scalar_one_or_none()

    if not coupon:
        return {"valid": False, "reason": "Cupón no encontrado"}

    if not coupon.is_active:
        return {"valid": False, "reason": "Cupón inactivo"}

    now = datetime.now(timezone.utc)
    if coupon.starts_at and coupon.starts_at > now:
        return {"valid": False, "reason": "Cupón aún no válido"}
    if coupon.expires_at and coupon.expires_at < now:
        return {"valid": False, "reason": "Cupón expirado"}

    if coupon.max_uses and coupon.current_uses >= coupon.max_uses:
        return {"valid": False, "reason": "Cupón agotado"}

    if coupon.min_purchase_amount and amount < float(coupon.min_purchase_amount):
        return {"valid": False, "reason": f"Mínimo de compra: ${coupon.min_purchase_amount}"}

    # Check per-user limit
    user_uses = await db.execute(
        select(func.count(CouponUsage.id)).where(
            CouponUsage.coupon_id == coupon.id,
            CouponUsage.user_id == user_id,
        )
    )
    if user_uses.scalar() >= coupon.max_uses_per_user:
        return {"valid": False, "reason": "Ya usaste este cupón"}

    # Calculate discount
    discount = 0
    if coupon.discount_type == "percentage":
        discount = amount * (float(coupon.discount_value) / 100)
        if coupon.max_discount_amount:
            discount = min(discount, float(coupon.max_discount_amount))
    else:
        discount = float(coupon.discount_value)

    return {
        "valid": True,
        "coupon_id": coupon.id,
        "discount": round(discount, 2),
        "final_amount": round(max(amount - discount, 0), 2),
        "discount_type": coupon.discount_type,
        "discount_value": float(coupon.discount_value),
    }


async def apply_coupon(db: AsyncSession, coupon_id: uuid.UUID, user_id: uuid.UUID, original_amount: float, discount: float) -> CouponUsage:
    usage = CouponUsage(
        coupon_id=coupon_id,
        user_id=user_id,
        discount_applied=discount,
        original_amount=original_amount,
        final_amount=original_amount - discount,
    )
    db.add(usage)

    # Update coupon uses
    result = await db.execute(select(Coupon).where(Coupon.id == coupon_id))
    coupon = result.scalar_one()
    coupon.current_uses += 1

    await db.commit()
    await db.refresh(usage)
    return usage
