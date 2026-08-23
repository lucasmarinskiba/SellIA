"""User signup/registration endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Body
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from app.core.database import get_db
import hashlib
import base64
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])


class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str


@router.post("/signup")
async def signup(
    req: SignupRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register new user account - direct SQL insert."""
    try:
        # Check if email exists
        result = await db.execute(text("SELECT id FROM users WHERE email = :email"), {"email": req.email})
        if result.scalar():
            raise HTTPException(status_code=400, detail="Email already registered")

        # Hash password
        password_hash = hashlib.sha256(req.password.encode()).hexdigest()
        user_id = str(uuid.uuid4())

        # Insert user directly via SQL
        await db.execute(
            text("""
                INSERT INTO users (id, email, hashed_password, full_name, is_active, email_verified,
                    failed_login_attempts, is_superuser, is_2fa_enabled, country_code, preferred_currency,
                    timezone, billing_address, payment_methods, created_at, updated_at)
                VALUES (:id, :email, :hash, :full_name, true, false, 0, false, false, 'AR', 'ARS',
                    'America/Argentina/Buenos_Aires', '{}', '[]', NOW(), NOW())
            """),
            {
                "id": user_id,
                "email": req.email,
                "hash": password_hash,
                "full_name": req.full_name,
            }
        )
        await db.commit()

        # Generate token
        token_data = f"{user_id}:{req.email}"
        access_token = base64.b64encode(token_data.encode()).decode()

        return {
            "user_id": user_id,
            "email": req.email,
            "full_name": req.full_name,
            "access_token": access_token,
            "message": "Account created successfully",
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Signup failed: {str(e)}")


@router.post("/signin")
async def signin(
    email: str = Body(...),
    password: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Sign in to user account."""
    # Hash password
    password_hash = hashlib.sha256(password.encode()).hexdigest()

    # Query user
    result = await db.execute(
        text("SELECT id, email, full_name FROM users WHERE email = :email AND hashed_password = :hash"),
        {"email": email, "hash": password_hash}
    )
    user_row = result.first()

    if not user_row:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user_id, user_email, full_name = user_row

    # Generate token
    token_data = f"{user_id}:{user_email}"
    access_token = base64.b64encode(token_data.encode()).decode()

    return {
        "user_id": str(user_id),
        "email": user_email,
        "full_name": full_name,
        "access_token": access_token,
    }


@router.get("/me")
async def get_current_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get current user profile."""
    result = await db.execute(text("SELECT id, email, full_name FROM users WHERE id = :id"), {"id": user_id})

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user.id,
        "email": user.email,
        "seller_name": user.seller_name,
        "business_name": user.business_name,
    }
