"""
SellIA Edge Sidecar
===================
Sidecar de autorización centralizada para Envoy (ext_authz).
Reemplaza la lógica repetida de auth, rate-limit y logging que hoy vive
en los middlewares de FastAPI.

En Kubernetes se despliega como contenedor adicional en el pod del backend.
Envoy delega la decisión de acceso a este sidecar vía HTTP POST.
"""

import os
import json
import time
import logging
import re
from datetime import datetime, timezone

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from jose import jwt, JWTError
import redis

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

# Rate limit config
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))      # segundos
RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "100"))           # requests por window
RATE_LIMIT_AUTH_MAX = int(os.getenv("RATE_LIMIT_AUTH_MAX", "10"))  # requests por window para auth

# ---------------------------------------------------------------------------
# Logging JSON (equivalente al security_logger del backend)
# ---------------------------------------------------------------------------
logger = logging.getLogger("sidecar")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


def log_json(level: str, **fields):
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "service": "sidecar",
        **fields,
    }
    logger.info(json.dumps(entry, ensure_ascii=False))


# ---------------------------------------------------------------------------
# Redis
# ---------------------------------------------------------------------------
_redis = redis.from_url(REDIS_URL, decode_responses=True)


def _rate_limit_key(ip: str, path: str) -> str:
    return f"sidecar:rl:{ip}:{path}"


def check_rate_limit(ip: str, path: str) -> tuple[bool, int, int]:
    """
    Sliding-window rate limit con Redis.
    Retorna (allowed, remaining, retry_after).
    """
    window = RATE_LIMIT_WINDOW
    max_req = RATE_LIMIT_AUTH_MAX if path.startswith("/api/v1/auth") else RATE_LIMIT_MAX

    key = _rate_limit_key(ip, path)
    now = time.time()
    window_start = now - window

    pipe = _redis.pipeline()
    pipe.zremrangebyscore(key, 0, window_start)
    pipe.zcard(key)
    pipe.zadd(key, {str(now): now})
    pipe.expire(key, window + 1)
    _, current_count, _, _ = pipe.execute()

    # current_count es el count ANTES de agregar el nuevo request
    if current_count >= max_req:
        # Remover el request que acabamos de agregar (fue rechazado)
        _redis.zrem(key, str(now))
        retry_after = window - int(now - _redis.zrange(key, 0, 0, withscores=True)[0][1])
        return False, 0, max(1, retry_after)

    remaining = max(0, max_req - current_count - 1)
    return True, remaining, 0


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

def decode_token(token: str) -> dict | None:
    if not SECRET_KEY:
        return None
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None


# ---------------------------------------------------------------------------
# FastAPI App
# ---------------------------------------------------------------------------

app = FastAPI(title="SellIA Sidecar", docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/health")
async def health():
    try:
        _redis.ping()
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "redis": str(e)},
        )
    return {"status": "ok", "service": "sidecar"}


@app.post("/ext_authz")
async def ext_authz(request: Request):
    """
    Endpoint compatible con Envoy ext_authz (http_service).
    Envoy reenvía la request original; el sidecar decide permitir o denegar.
    """
    method = request.headers.get("x-forwarded-method", request.method)
    path = request.headers.get("x-forwarded-uri", request.url.path)
    host = request.headers.get("x-forwarded-host", request.headers.get("host", ""))
    ip = request.headers.get("x-forwarded-for", request.client.host if request.client else "unknown")
    ip = ip.split(",")[0].strip() if "," in ip else ip

    user_agent = request.headers.get("user-agent", "")
    auth_header = request.headers.get("authorization", "")
    token = auth_header.removeprefix("Bearer ") if auth_header.startswith("Bearer ") else None

    # --- 1. Rate Limiting ---
    allowed, remaining, retry_after = check_rate_limit(ip, path)
    if not allowed:
        log_json(
            "warning",
            event="rate_limit_exceeded",
            ip=ip,
            method=method,
            path=path,
            user_agent=user_agent,
        )
        return Response(
            status_code=429,
            headers={
                "X-RateLimit-Limit": str(RATE_LIMIT_MAX),
                "X-RateLimit-Remaining": "0",
                "Retry-After": str(retry_after),
                "Content-Type": "application/json",
            },
            content=json.dumps({"detail": "Rate limit exceeded"}),
        )

    # --- 2. JWT Validation (solo para rutas protegidas) ---
    public_paths = re.compile(r"^(/health|/envoy-health|/api/v1/auth/(login|register|refresh|security-status|cloudflare-config)|/metrics)$")
    payload = None

    if not public_paths.match(path):
        if not token:
            log_json(
                "warning",
                event="missing_token",
                ip=ip,
                method=method,
                path=path,
            )
            return Response(
                status_code=401,
                headers={"Content-Type": "application/json"},
                content=json.dumps({"detail": "Missing authentication token"}),
            )

        payload = decode_token(token)
        if not payload:
            log_json(
                "warning",
                event="invalid_token",
                ip=ip,
                method=method,
                path=path,
            )
            return Response(
                status_code=401,
                headers={"Content-Type": "application/json"},
                content=json.dumps({"detail": "Invalid authentication token"}),
            )

    # --- 3. Logging de acceso permitido ---
    log_json(
        "info",
        event="request_allowed",
        ip=ip,
        method=method,
        path=path,
        user_agent=user_agent,
        user_id=payload.get("sub") if payload else None,
        rate_limit_remaining=remaining,
    )

    # --- 4. Headers que se propagan al backend ---
    response_headers = {
        "X-RateLimit-Limit": str(RATE_LIMIT_MAX if not path.startswith("/api/v1/auth") else RATE_LIMIT_AUTH_MAX),
        "X-RateLimit-Remaining": str(remaining),
        "X-Forwarded-For": ip,
        "X-Request-ID": request.headers.get("x-request-id", ""),
    }

    if payload:
        response_headers["X-User-Id"] = str(payload.get("sub", ""))
        response_headers["X-User-Email"] = str(payload.get("email", ""))
        response_headers["X-User-Role"] = str(payload.get("role", ""))
        response_headers["X-Authenticated"] = "true"
    else:
        response_headers["X-Authenticated"] = "false"

    return Response(status_code=200, headers=response_headers)
