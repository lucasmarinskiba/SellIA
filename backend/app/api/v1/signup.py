"""User signup/registration endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.domains.users.models import User
import hashlib

router = APIRouter(prefix="/auth", tags=["auth"])


def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


@router.post("/signup")
async def signup(
    email: str = Body(...),
    password: str = Body(...),
    full_name: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Register new user account."""
    # Check if email exists
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    if result.scalars().first():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # Generate access token
    from app.core.security import create_access_token
    access_token = create_access_token(user_id=str(user.id))

    return {
        "user_id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "access_token": access_token,
        "message": "Account created successfully",
    }


@router.post("/signin")
async def signin(
    email: str = Body(...),
    password: str = Body(...),
    db: AsyncSession = Depends(get_db),
):
    """Sign in to seller account."""
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user or user.password_hash != hash_password(password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return {
        "user_id": user.id,
        "email": user.email,
        "seller_name": user.seller_name,
        "business_name": user.business_name,
        "token": f"token_{user.id}",  # Demo token
    }


@router.get("/me")
async def get_current_user(user_id: str, db: AsyncSession = Depends(get_db)):
    """Get current user profile."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user.id,
        "email": user.email,
        "seller_name": user.seller_name,
        "business_name": user.business_name,
    }
