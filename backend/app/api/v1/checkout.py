"""Checkout & payment processing endpoints."""

from fastapi import APIRouter, HTTPException, Body, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
import os
import httpx

router = APIRouter(prefix="/checkout", tags=["payments"])

MERCADOPAGO_ACCESS_TOKEN = (os.getenv("MERCADOPAGO_ACCESS_TOKEN") or "").strip() or None
MERCADOPAGO_USER_ID = (os.getenv("MERCADOPAGO_USER_ID") or "").strip() or None
SUCCESS_URL = os.getenv("CHECKOUT_SUCCESS_URL", "https://sellia-brain.vercel.app/dashboard")
FAILURE_URL = os.getenv("CHECKOUT_FAILURE_URL", "https://sellia-brain.vercel.app/pricing")


class CheckoutRequest(BaseModel):
    plan: str  # free, pro, enterprise
    currency: str = "ARS"
    email: str = None


PLAN_PRICES = {
    "pro": {
        "ARS": 49 * 100,  # MercadoPago uses cents
        "USD": 50 * 100,
    },
    "enterprise": None,  # Custom pricing
}

PLAN_NAMES = {
    "free": "SellIA Free",
    "pro": "SellIA Pro - $49/mes",
    "enterprise": "SellIA Enterprise - Custom",
}


@router.post("/session")
async def create_checkout_session(
    req: CheckoutRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create MercadoPago checkout session."""

    if req.plan == "free":
        return {"redirect_url": "/signup"}

    if req.plan == "enterprise":
        return {"redirect_url": "mailto:ventas@sellia.io"}

    if req.plan not in PLAN_PRICES:
        raise HTTPException(status_code=400, detail="Invalid plan")

    price = PLAN_PRICES[req.plan].get(req.currency)
    if not price:
        raise HTTPException(status_code=400, detail="Unsupported currency")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.mercadopago.com/checkout/preferences",
                headers={
                    "Authorization": f"Bearer {MERCADOPAGO_ACCESS_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "payer": {
                        "email": req.email or "customer@example.com",
                    },
                    "items": [
                        {
                            "title": PLAN_NAMES[req.plan],
                            "quantity": 1,
                            "currency_id": req.currency,
                            "unit_price": price / 100,
                        }
                    ],
                    "back_urls": {
                        "success": SUCCESS_URL,
                        "failure": FAILURE_URL,
                        "pending": FAILURE_URL,
                    },
                    "auto_return": "approved",
                    "external_reference": f"plan_{req.plan}",
                    "notification_url": "https://sellia-production.up.railway.app/api/v1/webhooks/mercadopago",
                },
            )

            if response.status_code == 201:
                data = response.json()
                return {"checkout_url": data.get("init_point")}
            else:
                raise HTTPException(status_code=400, detail="Failed to create checkout")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checkout error: {str(e)}")


@router.get("/{preference_id}")
async def get_checkout_status(preference_id: str):
    """Get checkout preference status."""

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://api.mercadopago.com/checkout/preferences/{preference_id}",
                headers={
                    "Authorization": f"Bearer {MERCADOPAGO_ACCESS_TOKEN}",
                },
            )

            if response.status_code == 200:
                return response.json()
            else:
                raise HTTPException(status_code=404, detail="Preference not found")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
