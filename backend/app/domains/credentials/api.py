"""Credential API"""

import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from .service import CredentialService
from .models import AuthType

router = APIRouter(prefix="/credentials", tags=["Credentials"])


def get_service(db: AsyncSession = Depends(get_db)) -> CredentialService:
    return CredentialService(db)


@router.post("")
async def store_credential(
    data: dict,
    user: User = Depends(get_current_user),
    service: CredentialService = Depends(get_service),
):
    """Store or update credentials for a domain."""
    cred = await service.store(
        user_id=user.id,
        domain=data["domain"],
        platform_name=data.get("platform_name", data["domain"]),
        username=data.get("username"),
        password=data.get("password"),
        api_key=data.get("api_key"),
        api_secret=data.get("api_secret"),
        auth_type=AuthType(data.get("auth_type", "password")),
        business_id=data.get("business_id"),
    )
    return {"id": str(cred.id), "domain": cred.domain, "platform_name": cred.platform_name}


@router.get("")
async def list_credentials(
    user: User = Depends(get_current_user),
    service: CredentialService = Depends(get_service),
):
    """List all stored credentials for the user."""
    creds = await service.list_for_user(user.id)
    return [
        {
            "id": str(c.id),
            "domain": c.domain,
            "platform_name": c.platform_name,
            "auth_type": c.auth_type.value,
            "has_password": bool(c.encrypted_password),
            "has_api_key": bool(c.encrypted_api_key),
            "last_used_at": c.last_used_at.isoformat() if c.last_used_at else None,
        }
        for c in creds
    ]


@router.get("/{domain}")
async def get_credential(
    domain: str,
    user: User = Depends(get_current_user),
    service: CredentialService = Depends(get_service),
):
    """Get decrypted credentials for a domain."""
    cred = await service.get(user.id, domain)
    if not cred:
        raise HTTPException(status_code=404, detail="Credential not found")
    return cred


@router.delete("/{credential_id}")
async def delete_credential(
    credential_id: uuid.UUID,
    user: User = Depends(get_current_user),
    service: CredentialService = Depends(get_service),
):
    """Soft-delete a credential."""
    success = await service.delete(user.id, credential_id)
    if not success:
        raise HTTPException(status_code=404, detail="Credential not found")
    return {"success": True}
