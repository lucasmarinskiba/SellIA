"""Computer Use — Browser Logger

Captura logs de consola, errores JS, y network requests del navegador
para debugging avanzado de sesiones.
"""

import json
from typing import List, Dict, Any, Callable, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from app.core.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ConsoleLog:
    level: str  # log, error, warn, info, debug
    text: str
    source: str
    url: str
    timestamp: datetime
    args: List[str]


@dataclass
class NetworkRequest:
    method: str
    url: str
    status: Optional[int]
    duration_ms: Optional[float]
    request_headers: Dict[str, str]
    response_headers: Dict[str, str]
    timestamp: datetime
    error: Optional[str]


class BrowserLogger:
    """Captura logs del navegador durante sesiones de Computer Use."""

    def __init__(self):
        self.console_logs: List[ConsoleLog] = []
        self.network_requests: List[NetworkRequest] = []
        self._console_handler: Optional[Callable] = None
        self._request_handler: Optional[Callable] = None
        self._response_handler: Optional[Callable] = None
        self._page = None

    async def attach(self, page) -> None:
        """Adjunta listeners a la página de Playwright."""
        self._page = page
        self.console_logs = []
        self.network_requests = []

        # Console listener
        self._console_handler = lambda msg: self._on_console(msg)
        page.on("console", self._console_handler)

        # Request listener
        self._request_handler = lambda req: self._on_request(req)
        page.on("request", self._request_handler)

        # Response listener
        self._response_handler = lambda res: self._on_response(res)
        page.on("response", self._response_handler)

        # Page error
        page.on("pageerror", lambda err: self.console_logs.append(ConsoleLog(
            level="pageerror",
            text=str(err),
            source="page",
            url=page.url,
            timestamp=datetime.now(timezone.utc),
            args=[],
        )))

        logger.info("BrowserLogger attached")

    async def detach(self) -> None:
        """Desadjunta listeners."""
        if self._page:
            if self._console_handler:
                self._page.remove_listener("console", self._console_handler)
            if self._request_handler:
                self._page.remove_listener("request", self._request_handler)
            if self._response_handler:
                self._page.remove_listener("response", self._response_handler)
        self._page = None
        logger.info("BrowserLogger detached")

    def _on_console(self, msg) -> None:
        """Procesa mensaje de consola."""
        try:
            args = []
            for arg in msg.args:
                try:
                    val = arg.json_value()
                    args.append(str(val)[:500])
                except Exception:
                    args.append("[object]")

            self.console_logs.append(ConsoleLog(
                level=msg.type,
                text=msg.text[:1000],
                source=msg.location.get("url", "") if msg.location else "",
                url=self._page.url if self._page else "",
                timestamp=datetime.now(timezone.utc),
                args=args,
            ))
        except Exception as e:
            logger.warning(f"Console log processing error: {e}")

    def _on_request(self, request) -> None:
        """Procesa request de red."""
        try:
            self.network_requests.append(NetworkRequest(
                method=request.method,
                url=request.url[:500],
                status=None,
                duration_ms=None,
                request_headers=dict(request.headers),
                response_headers={},
                timestamp=datetime.now(timezone.utc),
                error=None,
            ))
        except Exception as e:
            logger.warning(f"Request processing error: {e}")

    def _on_response(self, response) -> None:
        """Procesa response de red."""
        try:
            # Find matching request
            matching = [r for r in self.network_requests if r.url == response.url[:500] and r.status is None]
            if matching:
                req = matching[-1]
                req.status = response.status
                req.response_headers = dict(response.headers)
                # Try to get timing
                try:
                    timing = response.request.timing
                    if timing and "endTime" in timing and "startTime" in timing:
                        req.duration_ms = timing["endTime"] - timing["startTime"]
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"Response processing error: {e}")

    def get_errors(self) -> List[ConsoleLog]:
        """Obtiene solo errores de consola."""
        return [log for log in self.console_logs if log.level in ("error", "pageerror")]

    def get_failed_requests(self) -> List[NetworkRequest]:
        """Obtiene requests fallidos (4xx, 5xx)."""
        return [r for r in self.network_requests if r.status and r.status >= 400]

    def get_summary(self) -> Dict[str, Any]:
        """Resumen de logs capturados."""
        errors = self.get_errors()
        failed_reqs = self.get_failed_requests()
        return {
            "console_logs_total": len(self.console_logs),
            "console_errors": len(errors),
            "network_requests_total": len(self.network_requests),
            "failed_requests": len(failed_reqs),
            "error_samples": [
                {"level": e.level, "text": e.text[:200], "url": e.url}
                for e in errors[:5]
            ],
            "failed_request_samples": [
                {"url": r.url[:100], "status": r.status}
                for r in failed_reqs[:5]
            ],
        }

    def export_logs(self) -> Dict[str, Any]:
        """Exporta todos los logs serializables."""
        return {
            "console_logs": [
                {
                    "level": log.level,
                    "text": log.text,
                    "source": log.source,
                    "url": log.url,
                    "timestamp": log.timestamp.isoformat(),
                }
                for log in self.console_logs
            ],
            "network_requests": [
                {
                    "method": req.method,
                    "url": req.url,
                    "status": req.status,
                    "duration_ms": req.duration_ms,
                    "timestamp": req.timestamp.isoformat(),
                    "error": req.error,
                }
                for req in self.network_requests
            ],
        }
