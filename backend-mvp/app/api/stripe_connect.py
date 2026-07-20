"""Stripe Connect · multi-tenant marketplace payouts.

Each tenant gets an Express connected account · platform fee on payments.
"""
import logging

import stripe
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select

from app.core.config import settings
from app.core.security import CurrentUser, require_role
from app.db.models import Tenant
from app.db.session import get_session


logger = logging.getLogger(__name__)
router = APIRouter()

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


class OnboardRequest(BaseModel):
    return_url: HttpUrl
    refresh_url: HttpUrl


class OnboardResponse(BaseModel):
    onboarding_url: str
    account_id: str


class AccountStatusResponse(BaseModel):
    account_id: str | None
    charges_enabled: bool
    payouts_enabled: bool
    details_submitted: bool
    requirements_due: list[str]


@router.post("/onboard", response_model=OnboardResponse)
async def create_onboarding_link(
    payload: OnboardRequest,
    user: CurrentUser = Depends(require_role("owner", "admin")),
) -> OnboardResponse:
    """Create Stripe Express account + onboarding link · returns URL to redirect tenant."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    async with get_session(tenant_id=user.tenant_id) as db:
        result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
        tenant = result.scalar_one()

        # Reuse existing account if present, else create
        connect_id = (tenant.settings or {}).get("stripe_connect_id")
        if not connect_id:
            account = stripe.Account.create(
                type="express",
                country="AR",  # TODO: per-tenant country detection
                metadata={"tenant_id": user.tenant_id, "tenant_name": tenant.name},
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
            )
            connect_id = account.id
            tenant.settings = {**(tenant.settings or {}), "stripe_connect_id": connect_id}
            await db.flush()
            logger.info("stripe_connect_created", extra={"tenant_id": user.tenant_id, "acct": connect_id})

    link = stripe.AccountLink.create(
        account=connect_id,
        refresh_url=str(payload.refresh_url),
        return_url=str(payload.return_url),
        type="account_onboarding",
    )

    return OnboardResponse(onboarding_url=link.url, account_id=connect_id)


@router.get("/account", response_model=AccountStatusResponse)
async def get_account_status(
    user: CurrentUser = Depends(require_role("owner", "admin")),
) -> AccountStatusResponse:
    """Check Connect account state · charges enabled · pending requirements."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    async with get_session(tenant_id=user.tenant_id) as db:
        result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
        tenant = result.scalar_one()
        connect_id = (tenant.settings or {}).get("stripe_connect_id")

    if not connect_id:
        return AccountStatusResponse(
            account_id=None,
            charges_enabled=False,
            payouts_enabled=False,
            details_submitted=False,
            requirements_due=[],
        )

    acct = stripe.Account.retrieve(connect_id)
    return AccountStatusResponse(
        account_id=connect_id,
        charges_enabled=bool(acct.charges_enabled),
        payouts_enabled=bool(acct.payouts_enabled),
        details_submitted=bool(acct.details_submitted),
        requirements_due=acct.requirements.currently_due if acct.requirements else [],
    )


class LoginLinkResponse(BaseModel):
    url: str


@router.post("/login-link", response_model=LoginLinkResponse)
async def create_login_link(
    user: CurrentUser = Depends(require_role("owner", "admin")),
) -> LoginLinkResponse:
    """Generate one-time login link to tenant's Stripe Express dashboard."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    async with get_session(tenant_id=user.tenant_id) as db:
        result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
        tenant = result.scalar_one()
        connect_id = (tenant.settings or {}).get("stripe_connect_id")

    if not connect_id:
        raise HTTPException(status_code=400, detail="Connect account not created · onboard first")

    link = stripe.Account.create_login_link(connect_id)
    return LoginLinkResponse(url=link.url)


class ChargeRequest(BaseModel):
    amount_cents: int
    currency: str = "usd"
    description: str
    customer_email: str | None = None


@router.post("/charge")
async def create_charge(
    payload: ChargeRequest,
    user: CurrentUser = Depends(require_role("owner", "admin", "manager")),
):
    """Create payment on behalf of tenant · application_fee = 5%."""
    if not settings.STRIPE_SECRET_KEY:
        raise HTTPException(status_code=503, detail="Stripe not configured")

    async with get_session(tenant_id=user.tenant_id) as db:
        result = await db.execute(select(Tenant).where(Tenant.id == user.tenant_id))
        tenant = result.scalar_one()
        connect_id = (tenant.settings or {}).get("stripe_connect_id")

    if not connect_id:
        raise HTTPException(status_code=400, detail="Connect not onboarded")

    # 5% platform fee
    fee = max(int(payload.amount_cents * 0.05), 50)

    intent = stripe.PaymentIntent.create(
        amount=payload.amount_cents,
        currency=payload.currency,
        description=payload.description,
        receipt_email=payload.customer_email,
        application_fee_amount=fee,
        transfer_data={"destination": connect_id},
        metadata={"tenant_id": user.tenant_id},
    )

    return {"client_secret": intent.client_secret, "id": intent.id, "platform_fee_cents": fee}
