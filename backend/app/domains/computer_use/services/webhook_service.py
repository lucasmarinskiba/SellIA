"""Computer Use — Webhook Service

Envía notificaciones webhook cuando ocurren eventos de sesión:
completado, fallido, detenido, CAPTCHA detectado, etc.
Incluye firma HMAC para verificación de integridad.
"""

import hmac
import hashlib
import json
import asyncio
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List

import aiohttp

from app.core.logger import get_logger

logger = get_logger(__name__)


class WebhookService:
    """Servicio de notificaciones webhook para Computer Use."""

    def __init__(self):
        self._delivery_timeout = aiohttp.ClientTimeout(total=10)

    def _sign_payload(self, payload: str, secret: str) -> str:
        """Genera firma HMAC-SHA256 del payload."""
        return hmac.new(
            secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    async def send_webhook(
        self,
        url: str,
        event: str,
        payload: Dict[str, Any],
        secret: Optional[str] = None,
        retry_count: int = 3,
    ) -> tuple[bool, Optional[int], Optional[str]]:
        """Envía un webhook con retry."""
        payload_data = {
            "event": event,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": payload,
        }
        body = json.dumps(payload_data, ensure_ascii=False, default=str)

        headers = {
            "Content-Type": "application/json",
            "X-Computer-Use-Event": event,
            "X-Computer-Use-Timestamp": datetime.now(timezone.utc).isoformat(),
            "User-Agent": "SellIA-Computer-Use/1.0",
        }

        if secret:
            signature = self._sign_payload(body, secret)
            headers["X-Computer-Use-Signature"] = f"sha256={signature}"

        last_error = None
        last_status = None

        for attempt in range(retry_count):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        url,
                        data=body,
                        headers=headers,
                        timeout=self._delivery_timeout,
                    ) as resp:
                        last_status = resp.status
                        if resp.status < 400:
                            logger.info(f"Webhook delivered: {event} → {url} (HTTP {resp.status})")
                            return True, resp.status, None
                        else:
                            resp_text = await resp.text()
                            last_error = f"HTTP {resp.status}: {resp_text[:200]}"
                            logger.warning(f"Webhook failed: {event} → {url} ({last_error})")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Webhook delivery error (attempt {attempt + 1}): {e}")

            if attempt < retry_count - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        logger.error(f"Webhook delivery failed after {retry_count} attempts: {event} → {url}")
        return False, last_status, last_error

    async def notify_session_completed(
        self,
        webhook_url: str,
        session_data: Dict[str, Any],
        secret: Optional[str] = None,
    ) -> tuple[bool, Optional[int], Optional[str]]:
        """Notifica que una sesión se completó."""
        return await self.send_webhook(
            url=webhook_url,
            event="session.completed",
            payload={
                "session_id": str(session_data.get("id")),
                "status": "completed",
                "total_steps": session_data.get("total_steps"),
                "task_description": session_data.get("task_description"),
                "result_summary": session_data.get("result_data", {}).get("summary"),
                "started_at": session_data.get("started_at"),
                "completed_at": session_data.get("completed_at"),
            },
            secret=secret,
        )

    async def notify_session_failed(
        self,
        webhook_url: str,
        session_data: Dict[str, Any],
        error_message: str,
        secret: Optional[str] = None,
    ) -> tuple[bool, Optional[int], Optional[str]]:
        """Notifica que una sesión falló."""
        return await self.send_webhook(
            url=webhook_url,
            event="session.failed",
            payload={
                "session_id": str(session_data.get("id")),
                "status": "failed",
                "error_message": error_message,
                "total_steps": session_data.get("total_steps"),
                "task_description": session_data.get("task_description"),
            },
            secret=secret,
        )

    async def notify_captcha_detected(
        self,
        webhook_url: str,
        session_id: str,
        confidence: float,
        reason: str,
        secret: Optional[str] = None,
    ) -> tuple[bool, Optional[int], Optional[str]]:
        """Notifica detección de CAPTCHA."""
        return await self.send_webhook(
            url=webhook_url,
            event="session.captcha_detected",
            payload={
                "session_id": session_id,
                "confidence": confidence,
                "reason": reason,
                "action": "session_paused",
            },
            secret=secret,
        )

    async def notify_batch_completed(
        self,
        webhook_url: str,
        batch_id: str,
        results: Dict[str, Any],
        secret: Optional[str] = None,
    ) -> tuple[bool, Optional[int], Optional[str]]:
        """Notifica completado de batch job."""
        return await self.send_webhook(
            url=webhook_url,
            event="batch.completed",
            payload={
                "batch_id": batch_id,
                "total": results.get("total", 0),
                "completed": results.get("completed", 0),
                "failed": results.get("failed", 0),
            },
            secret=secret,
        )
