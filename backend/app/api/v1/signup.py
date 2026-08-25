"""User signup/registration endpoints with secure password validation and 2FA."""

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import get_db
import hashlib
import base64
import uuid
import re
import bcrypt
import pyotp
import qrcode
from io import BytesIO

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str

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

        await db.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, full_name, is_active, email_verified,
                    failed_login_attempts, is_superuser, is_2fa_enabled, country_code, preferred_currency,
                    timezone, billing_address, payment_methods, created_at, updated_at)
                VALUES (:id, :email, :hash, :full_name, true, false, 0, false, false, 'AR', 'ARS',
                    'America/Argentina/Buenos_Aires', '{}', '[]', NOW(), NOW())
            """),
            {"id": user_id, "email": req.email, "hash": password_hash, "full_name": req.full_name}
        )
        await db.commit()

        from app.core.security import create_access_token
        access_token = create_access_token({"sub": user_id})

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
            text("SELECT id, email, full_name, hashed_password, is_2fa_enabled, totp_secret FROM users WHERE email = :email"),
            {"email": req.email}
        )
        user_row = result.first()

        if not user_row:
            raise HTTPException(status_code=401, detail="Invalid email or password")

        user_id, user_email, full_name, hashed_password, is_2fa_enabled, totp_secret = user_row

        if not bcrypt.checkpw(req.password.encode(), hashed_password.encode()):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        if is_2fa_enabled:
            if not req.totp_code:
                return {"requires_2fa": True, "user_id": str(user_id), "message": "2FA code required"}

            totp = pyotp.TOTP(totp_secret)
            if not totp.verify(req.totp_code, valid_window=1):
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


@router.post("/2fa/enable")
async def enable_2fa(user_id: str = Body(...), db: AsyncSession = Depends(get_db)):
    """Generate 2FA secret and QR code."""
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret)
    provisioning_uri = totp.provisioning_uri(name=user_id, issuer_name="SellIA")

    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(provisioning_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    img_io = BytesIO()
    img.save(img_io, format="PNG")
    img_base64 = base64.b64encode(img_io.getvalue()).decode()

    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{img_base64}",
        "message": "Scan QR code with authenticator app",
    }


@router.post("/2fa/verify")
async def verify_2fa(
    user_id: str = Body(...),
    secret: str = Body(...),
    totp_code: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Verify 2FA code and enable 2FA for user."""
    totp = pyotp.TOTP(secret)
    if not totp.verify(totp_code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid 2FA code")

    await db.execute(
        text("UPDATE users SET is_2fa_enabled = true, totp_secret = :secret WHERE id = :id"),
        {"id": user_id, "secret": secret}
    )
    await db.commit()

    return {"message": "2FA enabled successfully"}


@router.post("/2fa/disable")
async def disable_2fa(
    user_id: str = Body(...),
    password: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Disable 2FA (requires password confirmation)."""
    result = await db.execute(
        text("SELECT hashed_password FROM users WHERE id = :id"),
        {"id": user_id}
    )
    user_row = result.first()

    if not user_row or not bcrypt.checkpw(password.encode(), user_row[0].encode()):
        raise HTTPException(status_code=401, detail="Invalid password")

    await db.execute(
        text("UPDATE users SET is_2fa_enabled = false, totp_secret = NULL WHERE id = :id"),
        {"id": user_id}
    )
    await db.commit()

    return {"message": "2FA disabled"}


@router.get("/me")
async def get_current_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get current user profile."""
    result = await db.execute(text("SELECT id, email, full_name FROM users WHERE id = :id"), {"id": user_id})
    user_row = result.first()

    if not user_row:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user_row[0],
        "email": user_row[1],
        "full_name": user_row[2],
    }
