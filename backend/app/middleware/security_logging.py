import json
import re
import logging
import hmac
import secrets
from datetime import datetime, timezone
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Logger dedicado de seguridad
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)

# Handler a consola (en producción se redirige a archivo o SIEM)
if not security_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    security_logger.addHandler(handler)


# Patrones sospechosos de ataque
SUSPICIOUS_PATTERNS = [
    re.compile(r"(union\s+select|insert\s+into|delete\s+from|drop\s+table)", re.IGNORECASE),
    re.compile(r"(<script|javascript:|on\w+\s*=)", re.IGNORECASE),
    re.compile(r"(\.\./|\.\.\\|%2e%2e%2f)", re.IGNORECASE),
    re.compile(r"(eval\s*\(|expression\s*\(|url\s*\()")
]

# IPs privadas / loopback (no analizar como VPN)
PRIVATE_IPS = re.compile(
    r"^(127\.\d+\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2[0-9]|3[01])\.\d+\.\d+|192\.168\.\d+\.\d+|::1|fc00:|fe80:)"
)

# Dummy hash estático para mitigación de timing attacks
# bcrypt hash de "dummy" precomputado
_TIMING_ATTACK_DUMMY_HASH = "$2b$12$dummy.hash.for.timing.attack.mitigation.123456789012"


def _is_trusted_proxy(ip: str) -> bool:
    """Verifica si la IP es un proxy interno confiable (privada/loopback)."""
    if not ip or ip == "unknown":
        return False
    return bool(PRIVATE_IPS.match(ip))


def get_client_ip(request: Request) -> str:
    """Obtiene la IP real del cliente validando proxies confiables.
    
    Solo confía en X-Forwarded-For si la conexión directa proviene
    de una IP privada (proxy interno). Esto previene spoofing.
    """
    direct_ip = request.client.host if request.client else "unknown"
    
    # Solo leer headers de proxy si la conexión directa es confiable
    if _is_trusted_proxy(direct_ip):
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # El primer elemento es el cliente original
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip.strip()
    
    return direct_ip


async def _get_body_without_consuming(request: Request) -> bytes:
    """Lee el body del request sin consumirlo para downstream handlers.
    
    Reemplaza el receive del request con uno que cachea el body,
    permitiendo que los endpoints lo lean posteriormente.
    """
    body = await request.body()
    
    async def receive():
        return {"type": "http.request", "body": body}
    
    request._receive = receive
    return body


def is_suspicious_payload(request: Request, body: bytes) -> list[str]:
    """Escanea el payload en busca de patrones de ataque conocidos."""
    triggers = []
    text = body.decode("utf-8", errors="ignore")
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern.search(text):
            triggers.append(pattern.pattern[:60])
    return triggers


class SecurityAuditMiddleware(BaseHTTPMiddleware):
    """
    Middleware de auditoría de seguridad (IDS ligero).
    Registra todos los requests y alerta sobre actividad sospechosa.
    """

    async def dispatch(self, request: Request, call_next):
        start_time = datetime.now(timezone.utc)
        client_ip = get_client_ip(request)
        user_id = None
        suspicious_triggers: list[str] = []

        # Leer body para análisis (solo si no es un file upload grande)
        body = b""
        content_length = request.headers.get("content-length")
        try:
            cl = int(content_length) if content_length else 0
            if 0 < cl <= 10_000:
                body = await _get_body_without_consuming(request)
                suspicious_triggers = is_suspicious_payload(request, body)
        except ValueError:
            pass

        response = await call_next(request)

        # Intentar extraer user_id del scope si ya fue autenticado
        if hasattr(request.state, "user") and request.state.user:
            user_id = str(request.state.user.id)

        duration_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        # Info de Cloudflare si está disponible
        cf_info = getattr(request.state, "cloudflare_info", {})
        cf_valid = getattr(request.state, "cloudflare_valid", True)

        log_entry = {
            "timestamp": start_time.isoformat(),
            "level": "info",
            "ip": client_ip,
            "method": request.method,
            "path": request.url.path,
            "query": str(request.query_params),
            "status_code": response.status_code,
            "user_agent": request.headers.get("user-agent", ""),
            "user_id": user_id,
            "duration_ms": round(duration_ms, 2),
            "suspicious": len(suspicious_triggers) > 0,
            "suspicious_triggers": suspicious_triggers,
            "cloudflare": {
                "is_cloudflare": cf_info.get("is_cloudflare", False),
                "cf_ray": cf_info.get("cf_ray"),
                "cf_country": cf_info.get("cf_country"),
                "cf_valid_origin": cf_valid,
            } if cf_info else None,
        }

        # Alertas específicas de seguridad
        if response.status_code in (401, 403):
            log_entry["level"] = "warning"
            security_logger.warning(json.dumps(log_entry, ensure_ascii=False))
        elif suspicious_triggers:
            log_entry["level"] = "warning"
            security_logger.warning(json.dumps(log_entry, ensure_ascii=False))
        elif request.url.path in ("/docs", "/redoc", "/openapi.json"):
            log_entry["level"] = "warning"
            log_entry["alert"] = "reconnaissance"
            security_logger.warning(json.dumps(log_entry, ensure_ascii=False))
        else:
            security_logger.info(json.dumps(log_entry, ensure_ascii=False))

        # Añadir header de correlación para trazabilidad
        response.headers["X-Request-ID"] = getattr(request.state, "request_id", "unknown")

        return response
