"""
API Router para el Service Broker de provisionamiento de recursos.
"""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.deps import get_current_user
from app.domains.users.models import User
from app.domains.provisioning import service as provisioning_service
from app.domains.provisioning.schemas import (
    ResourceRequestCreate,
    ResourceRequestUpdate,
    ResourceRequestOut,
    ResourceRequestDetailOut,
)

router = APIRouter(prefix="/provisioning", tags=["provisioning"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.post(
    "/resources",
    response_model=ResourceRequestOut,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Solicitar un nuevo recurso",
)
async def create_resource_request(
    data: ResourceRequestCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """
    Crea una solicitud de provisionamiento de recurso (SSL, S3, DNS).
    La solicitud se encola asíncronamente y se procesa vía Celery workers.
    """
    request = await provisioning_service.create_request(
        db=db,
        data=data,
        user_id=current_user.id,
    )
    return request


@router.get(
    "/resources",
    response_model=list[ResourceRequestOut],
    summary="Listar solicitudes de recursos",
)
async def list_resource_requests(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    resource_type: str | None = Query(None, pattern="^(ssl_certificate|s3_bucket|dns_record)$"),
    status: str | None = Query(None, pattern="^(pending|processing|completed|failed|cancelled)$"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    requests, _ = await provisioning_service.list_requests(
        db=db,
        resource_type=resource_type,
        status=status,
        limit=limit,
        offset=offset,
    )
    return requests


@router.get(
    "/resources/{request_id}",
    response_model=ResourceRequestDetailOut,
    summary="Obtener detalle de una solicitud",
)
async def get_resource_request(
    request_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    request = await provisioning_service.get_request_detail(db, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return request


@router.patch(
    "/resources/{request_id}",
    response_model=ResourceRequestOut,
    summary="Actualizar estado de una solicitud (admin)",
)
async def update_resource_request(
    request_id: UUID,
    data: ResourceRequestUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    # Solo admins pueden actualizar manualmente
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden actualizar solicitudes")

    request = await provisioning_service.get_request(db, request_id)
    if not request:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    updated = await provisioning_service.update_request(db, request, data)
    return updated
