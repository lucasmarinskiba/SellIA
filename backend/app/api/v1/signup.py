"""User signup/signin endpoints with secure password validation (2FA enrolment lives in auth.py)."""

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.config import get_settings
from app.domains.users.models import User
from datetime import timedelta
import hashlib
import uuid
import re
import bcrypt
import pyotp

router = APIRouter(prefix="/auth", tags=["auth"])


# Same shape the signup form checks client-side. Deliberately not EmailStr: email-validator
# rejects special-use domains such as .local, which the test environments (CI, Playwright
# E2E) sign up with.
_EMAIL_SHAPE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str

    @field_validator("email")
    @classmethod
    def validate_email_shape(cls, v: str) -> str:
        """Reject values that are not an address: whitespace (which also covers CR/LF
        header injection into the verification email), a missing or doubled @, or no
        dot in the domain. Before this, any string was stored as the account's email."""
        if len(v) > 254 or not _EMAIL_SHAPE.match(v) or any(ord(ch) < 32 for ch in v):
            raise ValueError("Invalid email address")
        return v

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Require: 8+ chars, uppercase, lowercase, digit, special char (@+-!#$%)."""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain digit")
        if not re.search(r"[@+\-!#$%]", v):
            raise ValueError("Password must contain special char (@+-!#$%)")
        return v


@router.post("/signup")
async def signup(
    req: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register new user account with strong password requirements."""
    try:
        result = await db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": req.email})
        if result.scalar():
            raise HTTPException(status_code=400, detail="Email already registered")

        user_id = str(uuid.uuid4())
        password_hash = bcrypt.hashpw(req.password.encode(), bcrypt.gensalt(12)).decode()

        # Every NOT NULL users column must be listed here: raw SQL bypasses the ORM's
        # Python-side defaults, and a fresh database (create_all) has no DB-level
        # default for them. Existing databases only got away with omitting
        # email_otp_enabled because the startup ALTERs in sellbot.py add it with a DEFAULT.
        await db.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, full_name, is_active, email_verified,
                    failed_login_attempts, is_superuser, is_2fa_enabled, email_otp_enabled, country_code, preferred_currency,
                    timezone, billing_address, payment_methods, created_at, updated_at)
                VALUES (:id, :email, :hash, :full_name, true, false, 0, false, false, false, 'AR', 'ARS',
                    'America/Argentina/Buenos_Aires', '{}', '[]', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """),
            {"id": user_id, "email": req.email, "hash": password_hash, "full_name": req.full_name}
        )
        await db.commit()

        from app.core.security import create_access_token
        access_token = create_access_token({"sub": user_id})

        # This route duplicates /auth/register's account creation but used to
        # never send a verification email -- accounts made here had
        # email_verified=false forever, and /auth/login (the flow the
        # dashboard actually uses) refuses to issue a session until it's
        # true, with no email ever sent to fix it. Same email as
        # /auth/register sends, so both signup paths behave the same way.
        try:
            from app.api.v1.auth import _send_verification_email
            settings = get_settings()
            verify_token = create_access_token(
                data={"sub": user_id, "scope": "email_verify"},
                expires_delta=timedelta(hours=24),
            )
            verify_url = f"{settings.FRONTEND_URL or 'http://localhost:3000'}/verify-email?token={verify_token}"
            await _send_verification_email(req.email, req.full_name, verify_url)
        except Exception:
            pass

        return {
            "user_id": user_id,
            "email": req.email,
            "full_name": req.full_name,
            "access_token": access_token,
            "requires_2fa_setup": True,
            "message": "Account created. Set up 2FA for security.",
        }
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


class SigninRequest(BaseModel):
    email: str
    password: str
    totp_code: str = None


@router.post("/signin")
async def signin(
    req: SigninRequest,
    db: AsyncSession = Depends(get_db),
):
    """Sign in with password + optional 2FA."""
    try:
        result = await db.execute(
            text("SELECT id, email, full_name, hashed_password, is_2fa_enabled FROM users WHERE email = :email"),
            {"email": req.email}
        )
        user_row = result.first()

        if not user_row:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user_id, user_email, full_name, hashed_password, is_2fa_enabled = user_row

        if not bcrypt.checkpw(req.password.encode(), hashed_password.encode()):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if is_2fa_enabled:
            if not req.totp_code:
                return {"requires_2fa": True, "user_id": str(user_id), "message": "2FA code required"}

            # users.totp_secret is an EncryptedString column: a raw SELECT of it returns
            # the ciphertext (pyotp then fails with "Non-base32 digit found" -> 500, so
            # nobody with 2FA on could ever sign in). Read it through the typed column so
            # it comes back decrypted, the same way auth.py's 2FA handlers see it.
            totp_secret = (
                await db.execute(select(User.totp_secret).where(User.id == user_id))
            ).scalar_one_or_none()
            if not totp_secret or not pyotp.TOTP(totp_secret).verify(req.totp_code, valid_window=1):
                raise HTTPException(status_code=401, detail="Invalid 2FA code")

        from app.core.security import create_access_token
        access_token = create_access_token({"sub": str(user_id)})

        return {
            "user_id": str(user_id),
            "email": user_email,
            "full_name": full_name,
            "access_token": access_token,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Signin failed: {str(e)}")


# 2FA enrolment is NOT served from here. It used to be (/2fa/enable, /2fa/verify and
# /2fa/disable with a client-supplied user_id and secret, no session), but the
# authenticated flow in auth.py (/2fa/setup, /2fa/verify, /2fa/disable) owns those
# paths -- see the note at the end of auth.py for why this one must not come back.


@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get the AUTHENTICATED caller's own profile.

    Was previously `get_current_user(user_id: str)` -- a bare, unauthenticated
    query param, letting anyone fetch any other user's email/full_name just by
    guessing/enumerating a UUID (a real IDOR). Now resolves identity from the
    caller's own Bearer token/cookie via the shared get_current_user dependency
    (shadowing the import name below on purpose, same pattern used elsewhere
    in this file), same as every other authenticated endpoint in this app.
    """
    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
    }
