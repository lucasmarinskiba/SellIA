from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.users.schemas import UserResponse

router = APIRouter()


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)):
    return current_user


class UpdateMeRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=120)


@router.patch("/me")
async def update_current_user(
    data: UpdateMeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update the signed-in user's own profile.

    There was no way to change your own name at all: the Configuración screen
    showed an editable field pre-filled with a hardcoded "Juan Pérez" and a
    "Guardar cambios" button wired to nothing, so the edit was thrown away on
    every reload. Only full_name is editable here -- email is an identity/login
    field and changing it needs a verification flow that does not exist yet.
    """
    name = data.full_name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")

    current_user.full_name = name
    await db.commit()
    await db.refresh(current_user)
    return {"id": str(current_user.id), "full_name": current_user.full_name, "email": current_user.email}
