"""
Service Broker — Lógica de negocio para provisionamiento asíncrono de recursos.
Emula el patrón SQS + DynamoDB de Atlassian usando Celery + PostgreSQL.
"""

import json
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.domains.provisioning.models import ResourceRequest, ResourceJob, ResourceEvent
from app.domains.provisioning.schemas import ResourceRequestCreate, ResourceRequestUpdate
from app.core.logger import get_logger

logger = get_logger(__name__)


async def create_request(
    db: AsyncSession,
    data: ResourceRequestCreate,
    user_id: UUID | None,
) -> ResourceRequest:
    """
    Crea una solicitud de provisionamiento, la persiste en PostgreSQL
    (tracking tipo DynamoDB) y encola un worker Celery (cola tipo SQS).
    """
    request = ResourceRequest(
        resource_type=data.resource_type,
        name=data.name,
        parameters=data.parameters,
        status="pending",
        created_by=user_id,
    )
    db.add(request)
    await db.commit()
    await db.refresh(request)

    # Log de evento
    event = ResourceEvent(
        request_id=request.id,
        event_type="created",
        message=f"Solicitud creada: {data.resource_type} / {data.name}",
    )
    db.add(event)
    await db.commit()

    # Encolar worker Celery (emula SQS) — lazy import para evitar circularidad
    from app.tasks.provisioning_tasks import process_resource_request
    process_resource_request.delay(str(request.id))
    logger.info(f"Provisioning request {request.id} queued for {data.resource_type}")

    return request


async def get_request(db: AsyncSession, request_id: UUID) -> ResourceRequest | None:
    result = await db.execute(
        select(ResourceRequest).where(ResourceRequest.id == request_id)
    )
    return result.scalar_one_or_none()


async def get_request_detail(db: AsyncSession, request_id: UUID) -> ResourceRequest | None:
    result = await db.execute(
        select(ResourceRequest)
        .where(ResourceRequest.id == request_id)
    )
    return result.scalar_one_or_none()


async def list_requests(
    db: AsyncSession,
    resource_type: str | None = None,
    status: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> tuple[list[ResourceRequest], int]:
    query = select(ResourceRequest)
    count_query = select(ResourceRequest)

    if resource_type:
        query = query.where(ResourceRequest.resource_type == resource_type)
        count_query = count_query.where(ResourceRequest.resource_type == resource_type)
    if status:
        query = query.where(ResourceRequest.status == status)
        count_query = count_query.where(ResourceRequest.status == status)

    query = query.order_by(desc(ResourceRequest.created_at)).limit(limit).offset(offset)

    result = await db.execute(query)
    count_result = await db.execute(count_query)
    return result.scalars().all(), len(count_result.scalars().all())


async def update_request(
    db: AsyncSession,
    request: ResourceRequest,
    data: ResourceRequestUpdate,
) -> ResourceRequest:
    if data.status:
        request.status = data.status
        if data.status in ("completed", "failed", "cancelled"):
            request.completed_at = datetime.now(timezone.utc)
    if data.error_message is not None:
        request.error_message = data.error_message
    if data.provider_reference is not None:
        request.provider_reference = data.provider_reference

    await db.commit()
    await db.refresh(request)
    return request


async def add_event(
    db: AsyncSession,
    request_id: UUID,
    event_type: str,
    message: str,
    metadata: dict | None = None,
) -> ResourceEvent:
    event = ResourceEvent(
        request_id=request_id,
        event_type=event_type,
        message=message,
        metadata_=metadata or {},
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def create_job(
    db: AsyncSession,
    request_id: UUID,
    job_type: str,
) -> ResourceJob:
    job = ResourceJob(
        request_id=request_id,
        job_type=job_type,
        status="pending",
    )
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job


async def update_job(
    db: AsyncSession,
    job: ResourceJob,
    status: str,
    error_message: str | None = None,
    result: dict | None = None,
) -> ResourceJob:
    job.status = status
    if status == "running" and not job.started_at:
        job.started_at = datetime.now(timezone.utc)
    if status in ("completed", "failed"):
        job.completed_at = datetime.now(timezone.utc)
    if error_message is not None:
        job.error_message = error_message
    if result is not None:
        job.result = result

    await db.commit()
    await db.refresh(job)
    return job
