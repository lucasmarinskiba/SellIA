"""
Celery Tasks para el Service Broker de provisionamiento.
Emula el patrón de workers de Atlassian que consumen de SQS
y actualizan estado en DynamoDB (en nuestro caso: PostgreSQL).
"""

import json
from datetime import datetime, timezone

from celery import shared_task

from app.core.database import AsyncSessionLocal
from app.core.logger import get_logger
from app.domains.provisioning.models import ResourceRequest
from app.domains.provisioning import service as provisioning_service

logger = get_logger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_resource_request(self, request_id: str):
    """
    Worker principal que procesa una solicitud de provisionamiento.
    Consume de la cola Celery (emula SQS) y actualiza PostgreSQL (emula DynamoDB).
    """
    import asyncio
    asyncio.run(_process_resource_request_async(self, request_id))


async def _process_resource_request_async(task_self, request_id: str):
    async with AsyncSessionLocal() as db:
        request = await provisioning_service.get_request(db, request_id)
        if not request:
            logger.error(f"Provisioning request {request_id} not found")
            return

        # Marcar como processing
        request.status = "processing"
        await db.commit()
        await provisioning_service.add_event(
            db, request.id, "started", "Procesamiento iniciado"
        )

        try:
            if request.resource_type == "ssl_certificate":
                await _provision_ssl_certificate(db, request)
            elif request.resource_type == "s3_bucket":
                await _provision_s3_bucket(db, request)
            elif request.resource_type == "dns_record":
                await _provision_dns_record(db, request)
            else:
                raise ValueError(f"Tipo de recurso no soportado: {request.resource_type}")

            request.status = "completed"
            request.completed_at = datetime.now(timezone.utc)
            await db.commit()
            await provisioning_service.add_event(
                db, request.id, "completed", "Provisionamiento completado exitosamente"
            )
            logger.info(f"Provisioning request {request_id} completed")

        except Exception as exc:
            request.status = "failed"
            request.error_message = str(exc)
            request.completed_at = datetime.now(timezone.utc)
            await db.commit()
            await provisioning_service.add_event(
                db, request.id, "failed", f"Error: {str(exc)}"
            )
            logger.exception(f"Provisioning request {request_id} failed")
            raise task_self.retry(exc=exc) from exc


async def _provision_ssl_certificate(db, request: ResourceRequest):
    """Solicita un certificado SSL vía AWS ACM."""
    import boto3

    job = await provisioning_service.create_job(db, request.id, "create")
    await provisioning_service.update_job(db, job, "running")

    domain = request.parameters.get("domain")
    region = request.parameters.get("region", "us-east-1")
    if not domain:
        raise ValueError("El parámetro 'domain' es requerido")

    try:
        acm = boto3.client("acm", region_name=region)
        response = acm.request_certificate(
            DomainName=domain,
            ValidationMethod="DNS",
            SubjectAlternativeNames=[f"*.{domain}"] if not domain.startswith("*.") else [],
            Tags=[{"Key": "Name", "Value": request.name}, {"Key": "ManagedBy", "Value": "sellia-service-broker"}],
        )
        cert_arn = response["CertificateArn"]
        request.provider_reference = cert_arn

        await provisioning_service.update_job(
            db, job, "completed", result={"domain": domain, "arn": cert_arn, "region": region}
        )
        await provisioning_service.add_event(
            db, request.id, "step_completed", f"Certificado SSL solicitado en ACM para {domain}",
            {"domain": domain, "arn": cert_arn, "region": region}
        )
    except Exception as exc:
        await provisioning_service.update_job(db, job, "failed", error_message=str(exc))
        raise


async def _provision_s3_bucket(db, request: ResourceRequest):
    """Crea un bucket S3 usando boto3."""
    import boto3

    job = await provisioning_service.create_job(db, request.id, "create")
    await provisioning_service.update_job(db, job, "running")

    bucket_name = request.parameters.get("bucket_name")
    region = request.parameters.get("region", "us-east-1")
    if not bucket_name:
        raise ValueError("El parámetro 'bucket_name' es requerido")

    try:
        s3 = boto3.client("s3", region_name=region)

        create_params = {"Bucket": bucket_name}
        if region != "us-east-1":
            create_params["CreateBucketConfiguration"] = {"LocationConstraint": region}

        s3.create_bucket(**create_params)

        # Aplicar configuraciones de seguridad por defecto
        s3.put_public_access_block(
            Bucket=bucket_name,
            PublicAccessBlockConfiguration={
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        )

        # Habilitar versioning
        s3.put_bucket_versioning(
            Bucket=bucket_name,
            VersioningConfiguration={"Status": "Enabled"},
        )

        # Encriptación por defecto
        s3.put_bucket_encryption(
            Bucket=bucket_name,
            ServerSideEncryptionConfiguration={
                "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
            },
        )

        request.provider_reference = f"arn:aws:s3:::{bucket_name}"

        await provisioning_service.update_job(
            db, job, "completed", result={"bucket": bucket_name, "region": region}
        )
        await provisioning_service.add_event(
            db, request.id, "step_completed", f"Bucket S3 creado: {bucket_name}",
            {"bucket": bucket_name, "region": region}
        )
    except Exception as exc:
        await provisioning_service.update_job(db, job, "failed", error_message=str(exc))
        raise


async def _provision_dns_record(db, request: ResourceRequest):
    """Crea un registro DNS en Route53."""
    import boto3

    job = await provisioning_service.create_job(db, request.id, "create")
    await provisioning_service.update_job(db, job, "running")

    zone_id = request.parameters.get("zone_id")
    record_name = request.parameters.get("record_name")
    record_type = request.parameters.get("record_type", "A")
    record_value = request.parameters.get("record_value")
    ttl = request.parameters.get("ttl", 300)

    if not all([zone_id, record_name, record_value]):
        raise ValueError("Los parámetros 'zone_id', 'record_name' y 'record_value' son requeridos")

    try:
        route53 = boto3.client("route53")
        change_batch = {
            "Changes": [
                {
                    "Action": "CREATE",
                    "ResourceRecordSet": {
                        "Name": record_name,
                        "Type": record_type,
                        "TTL": ttl,
                        "ResourceRecords": [{"Value": record_value}],
                    },
                }
            ]
        }

        response = route53.change_resource_record_sets(
            HostedZoneId=zone_id,
            ChangeBatch=change_batch,
        )
        change_id = response["ChangeInfo"]["Id"]
        request.provider_reference = change_id

        await provisioning_service.update_job(
            db, job, "completed", result={
                "zone_id": zone_id,
                "name": record_name,
                "type": record_type,
                "value": record_value,
                "change_id": change_id,
            }
        )
        await provisioning_service.add_event(
            db, request.id, "step_completed", f"Registro DNS creado: {record_name}",
            {"zone_id": zone_id, "name": record_name, "type": record_type, "change_id": change_id}
        )
    except Exception as exc:
        await provisioning_service.update_job(db, job, "failed", error_message=str(exc))
        raise
