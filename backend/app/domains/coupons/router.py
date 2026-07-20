"""
Coupon Router
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.coupons import service as coupon_service

router = APIRouter(prefix="/coupons", tags=["coupons"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post("/validate")
async def validate_coupon(
    data: dict,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Validate a coupon code."""
    code = data.get("code", "")
    amount = data.get("amount", 0)
    plan_id = data.get("plan_id")
    result = await coupon_service.validate_coupon(db, code, current_user.id, plan_id, amount)
    return result
