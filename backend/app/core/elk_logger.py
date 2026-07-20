"""
ELK (Elasticsearch, Logstash, Kibana) Integration for SellIA Security Logs.

Provides:
- JSON structured logging compatible with Elasticsearch
- Optional direct push to Elasticsearch index
- File-based logging fallback for Logstash/Filebeat ingestion

Configuration via environment variables:
    ELK_ENABLED=true
    ELK_HOST=https://your-elasticsearch.cloud.es.io:9243
    ELK_INDEX=sellia-security-logs
    ELK_API_KEY=your-api-key
    ELK_USE_FILEBEAT=true  # Write to file instead of direct push
    ELK_LOG_PATH=/var/log/sellia/security.json
"""

import os
import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, Any
from pathlib import Path

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    aiohttp = None
    AIOHTTP_AVAILABLE = False

ELK_ENABLED = os.getenv("ELK_ENABLED", "false").lower() == "true"
ELK_HOST = os.getenv("ELK_HOST", "")
ELK_INDEX = os.getenv("ELK_INDEX", "sellia-security-logs")
ELK_API_KEY = os.getenv("ELK_API_KEY", "")
ELK_USE_FILEBEAT = os.getenv("ELK_USE_FILEBEAT", "true").lower() == "true"
ELK_LOG_PATH = os.getenv("ELK_LOG_PATH", "/var/log/sellia/security.json")

# Ensure log directory exists
if ELK_ENABLED and ELK_USE_FILEBEAT:
    Path(ELK_LOG_PATH).parent.mkdir(parents=True, exist_ok=True)


def format_elk_document(
    event_type: str,
    message: str,
    level: str = "info",
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    ip_address: Optional[str] = None,
    country: Optional[str] = None,
    extra: Optional[dict] = None,
) -> dict:
    """
    Format a security event as an Elasticsearch-compatible JSON document.
    
    Uses ECS (Elastic Common Schema) fields where applicable.
    """
    doc = {
        "@timestamp": datetime.now(timezone.utc).isoformat(),
        "event": {
            "kind": "event",
            "category": ["authentication" if "login" in event_type else "security"],
            "type": [event_type],
            "outcome": "success" if level == "info" else "failure" if level == "error" else "unknown",
        },
        "message": message,
        "log": {
            "level": level,
        },
        "source": {
            "ip": ip_address,
            "geo": {
                "country_iso_code": country,
            } if country else {},
        },
        "user": {
            "id": user_id,
            "email": email,
        } if user_id or email else {},
        "service": {
            "name": "sellia",
            "environment": os.getenv("ENVIRONMENT", "development"),
        },
        "labels": {
            "app": "sellia-security",
        },
    }
    
    # Clean empty fields
    doc["source"] = {k: v for k, v in doc["source"].items() if v}
    doc["user"] = {k: v for k, v in doc["user"].items() if v}
    
    if extra:
        doc["sellia"] = extra
    
    return doc


def write_to_file(document: dict) -> bool:
    """Append a JSON line to the log file (for Filebeat/Logstash ingestion)."""
    try:
        with open(ELK_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(document, ensure_ascii=False) + "\n")
        return True
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Failed to write log file: {e}")
        return False


async def push_to_elasticsearch(document: dict) -> bool:
    """Push a document directly to Elasticsearch."""
    if not AIOHTTP_AVAILABLE or not ELK_HOST or not ELK_API_KEY:
        return False
    
    url = f"{ELK_HOST}/{ELK_INDEX}/_doc"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"ApiKey {ELK_API_KEY}",
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                headers=headers,
                json=document,
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status in (200, 201):
                    return True
                else:
                    body = await resp.text()
                    from app.core.logger import get_logger
                    get_logger(__name__).error(f"Elasticsearch error {resp.status}: {body[:200]}")
                    return False
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Failed to push to Elasticsearch: {e}")
        return False


async def log_security_event(
    event_type: str,
    message: str,
    level: str = "info",
    user_id: Optional[str] = None,
    email: Optional[str] = None,
    ip_address: Optional[str] = None,
    country: Optional[str] = None,
    extra: Optional[dict] = None,
) -> bool:
    """
    Log a security event to ELK.
    
    If ELK_USE_FILEBEAT is true, writes to a JSON line file.
    Otherwise, pushes directly to Elasticsearch.
    """
    if not ELK_ENABLED:
        return False
    
    document = format_elk_document(
        event_type=event_type,
        message=message,
        level=level,
        user_id=user_id,
        email=email,
        ip_address=ip_address,
        country=country,
        extra=extra,
    )
    
    if ELK_USE_FILEBEAT:
        return write_to_file(document)
    else:
        return await push_to_elasticsearch(document)


# Convenience methods for common event types

async def log_login(
    email: str,
    ip: str,
    country: Optional[str] = None,
    success: bool = True,
    user_id: Optional[str] = None,
    extra: Optional[dict] = None,
):
    """Log a login event."""
    await log_security_event(
        event_type="login" if success else "failed_login",
        message=f"{'Successful' if success else 'Failed'} login for {email} from {ip}",
        level="info" if success else "warning",
        user_id=user_id,
        email=email,
        ip_address=ip,
        country=country,
        extra=extra,
    )


async def log_new_device(
    email: str,
    ip: str,
    country: Optional[str] = None,
    user_id: Optional[str] = None,
    device_info: Optional[str] = None,
):
    """Log a new device detection."""
    await log_security_event(
        event_type="new_device",
        message=f"New device detected for {email} from {ip}",
        level="warning",
        user_id=user_id,
        email=email,
        ip_address=ip,
        country=country,
        extra={"device_info": device_info},
    )


async def log_geofence_violation(
    email: str,
    ip: str,
    distance_km: float,
    country: Optional[str] = None,
    user_id: Optional[str] = None,
):
    """Log a geofencing violation."""
    await log_security_event(
        event_type="geofence_violation",
        message=f"Geofence violation for {email}: {distance_km:.0f}km from last login",
        level="warning",
        user_id=user_id,
        email=email,
        ip_address=ip,
        country=country,
        extra={"distance_km": distance_km},
    )


async def log_breach_detected(
    email: str,
    breach_count: int,
    breach_names: list[str],
    user_id: Optional[str] = None,
):
    """Log a HIBP breach detection."""
    await log_security_event(
        event_type="breach_detected",
        message=f"Email {email} found in {breach_count} known breaches",
        level="error",
        user_id=user_id,
        email=email,
        extra={"breach_count": breach_count, "breach_names": breach_names},
    )
