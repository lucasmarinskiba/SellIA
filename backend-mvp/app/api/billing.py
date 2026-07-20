"""Billing · Stripe checkout sessions + portal."""
import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import CurrentUser, require_role


router = APIRouter()

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


PLAN_PRICES = {
    "starter": "price_starter_monthly",
    "pro": "price_pro_monthly",
    "scale": "price_scale_monthly",
}


class CheckoutRequest(BaseModel):
    plan: str  # starter | pro | scale
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    checkout_url: str


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    payload: CheckoutRequest,
    user: CurrentUser = Depends(require_role("owner", "admin")),
) -> CheckoutResponse:
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    price_id = PLAN_PRICES.get(payload.plan)
    if not price_id:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {payload.plan}")

    session = stripe.checkout.Session.create(
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=payload.success_url,
        cancel_url=payload.cancel_url,
        client_reference_id=user.tenant_id,
        metadata={"tenant_id": user.tenant_id, "plan": payload.plan},
        subscription_data={"metadata": {"tenant_id": user.tenant_id}},
    )

    return CheckoutResponse(checkout_url=session.url)


class PortalResponse(BaseModel):
    portal_url: str


@router.post("/portal", response_model=PortalResponse)
async def create_portal(
    return_url: str,
    user: CurrentUser = Depends(require_role("owner", "admin")),
) -> PortalResponse:
    """Stripe Customer Portal · self-service billing mgmt."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    # Lookup customer from tenant (would be stored after first checkout)
    # For now, placeholder
    session = stripe.billing_portal.Session.create(
        customer=f"cus_placeholder_{user.tenant_id[:8]}",
        return_url=return_url,
    )
    return PortalResponse(portal_url=session.url)
