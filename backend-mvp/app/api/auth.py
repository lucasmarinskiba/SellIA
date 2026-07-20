"""Auth · signup + login + refresh."""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select

from app.core.ratelimit import rate_limit
from app.core.security import (
    CurrentUser,
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db.models import Tenant, User, UserRole
from app.db.session import get_session


router = APIRouter()


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=2, max_length=120)
    tenant_name: str = Field(min_length=2, max_length=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    tenant_id: str
    role: str


class MeResponse(BaseModel):
    user_id: str
    tenant_id: str
    role: str


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(
    payload: SignupRequest,
    _rl: None = Depends(rate_limit("signup", limit=3, window_s=3600)),
) -> TokenResponse:
    """Create new tenant + owner user. Returns JWT."""
    async with get_session() as db:
        # Check email uniqueness
        existing = await db.execute(select(User).where(User.email == payload.email))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email already registered")

        tenant = Tenant(name=payload.tenant_name)
        db.add(tenant)
        await db.flush()

        user = User(
            tenant_id=tenant.id,
            email=payload.email,
            name=payload.name,
            password_hash=hash_password(payload.password),
            role=UserRole.OWNER,
        )
        db.add(user)
        await db.flush()

        token = create_access_token(str(user.id), str(tenant.id), user.role.value)

    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        tenant_id=str(tenant.id),
        role=user.role.value,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    _rl: None = Depends(rate_limit("login", limit=5, window_s=60)),
) -> TokenResponse:
    """Email + password login."""
    async with get_session() as db:
        result = await db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not user.is_active:
            raise HTTPException(status_code=403, detail="Account suspended")

        token = create_access_token(str(user.id), str(user.tenant_id), user.role.value)

    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        tenant_id=str(user.tenant_id),
        role=user.role.value,
    )


@router.get("/me", response_model=MeResponse)
async def me(current: CurrentUser = Depends(get_current_user)) -> MeResponse:
    """Return current authenticated user."""
    return MeResponse(user_id=current.user_id, tenant_id=current.tenant_id, role=current.role)
