"""Integration marketplace API."""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.integrations.integration_service import IntegrationService

router = APIRouter(prefix="/api/v1", tags=["integrations"])


class CreateConnectionRequest(BaseModel):
    app_id: UUID
    auth_token: str | None = None
    auth_metadata: dict | None = None
    platform_name: str | None = None


class ConnectionResponse(BaseModel):
    id: UUID
    business_id: UUID
    app_id: UUID
    connection_status: str
    created_at: str


@router.get("/apps")
async def list_apps():
    """List available integration apps."""
    return {
        "apps": [
            {"id": "mercado-libre", "name": "Mercado Libre", "category": "ecommerce"},
            {"id": "shopify", "name": "Shopify", "category": "ecommerce"},
            {"id": "instagram", "name": "Instagram", "category": "social"},
            {"id": "tiktok", "name": "TikTok", "category": "social"},
            {"id": "amazon", "name": "Amazon", "category": "ecommerce"},
        ]
    }


@router.post("/businesses/{business_id}/connections", response_model=ConnectionResponse)
async def create_connection(
    business_id: UUID,
    data: CreateConnectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create platform connection + auto-enable SEO config."""
    svc = IntegrationService(db)
    connection = await svc.create_connection(
        business_id=business_id,
        app_id=data.app_id,
        auth_token=data.auth_token,
        auth_metadata=data.auth_metadata,
        platform_name=data.platform_name,
    )

    return {
        "id": connection.id,
        "business_id": connection.business_id,
        "app_id": connection.app_id,
        "connection_status": connection.connection_status,
        "created_at": connection.created_at.isoformat(),
    }


@router.get("/businesses/{business_id}/connections")
async def list_connections(
    business_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all platform connections for a business."""
    svc = IntegrationService(db)
    connections = await svc.list_business_connections(business_id)

    return {
        "connections": [
            {
                "id": str(c.id),
                "app_id": str(c.app_id),
                "status": c.connection_status,
                "created_at": c.created_at.isoformat(),
            }
            for c in connections
        ]
    }


@router.patch("/businesses/{business_id}/connections/{connection_id}")
async def update_connection(
    business_id: UUID,
    connection_id: UUID,
    data: CreateConnectionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update platform connection credentials."""
    svc = IntegrationService(db)
    connection = await svc.update_connection(
        connection_id=connection_id,
        auth_token=data.auth_token,
        auth_metadata=data.auth_metadata,
    )

    if not connection:
        raise HTTPException(status_code=404, detail="Connection not found")

    return {
        "id": connection.id,
        "business_id": connection.business_id,
        "app_id": connection.app_id,
        "connection_status": connection.connection_status,
        "created_at": connection.created_at.isoformat(),
    }
