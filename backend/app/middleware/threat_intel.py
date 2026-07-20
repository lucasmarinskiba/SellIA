from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from datetime import datetime, timezone, timedelta
from sqlalchemy import select

from app.core.threat_intel import assess_client_risk, device_fingerprint
from app.core.cloudflare import (
    get_cloudflare_info,
    validate_cloudflare_origin,
)
from app.core.country_block import get_blocked_countries, is_country_blocked
from app.core.database import AsyncSessionLocal
from app.domains.security.models import BlockedIP


def get_client_ip(request: Request) -> str:
    """Obtiene la IP real del cliente respetando Cloudflare y proxies."""
    headers = {k.lower(): v for k, v in request.headers.items()}

    # Prioridad 1: Cloudflare
    if "cf-connecting-ip" in headers:
        return headers["cf-connecting-ip"]

    # Prioridad 2: X-Forwarded-For
    forwarded = headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()

    # Prioridad 3: X-Real-IP
    real_ip = headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()

    # Prioridad 4: IP directa
    if request.client:
        return request.client.host

    return "unknown"


class ThreatIntelMiddleware(BaseHTTPMiddleware):
    """
    Analiza cada request para detectar:
    - VPN / Proxy / Tor
    - MITM / Inspeccion SSL por antivirus/proxy corporativo
    - User-Agents maliciosos (scanners)
    - Cloudflare WAF headers y validación de origen
    - Genera fingerprint del dispositivo
    """

    async def dispatch(self, request: Request, call_next):
        raw_ip = request.client.host if request.client else "unknown"
        client_ip = get_client_ip(request)
        user_agent = request.headers.get("user-agent")
        accept_lang = request.headers.get("accept-language")
        headers = dict(request.headers)

        # Validar origen Cloudflare
        cf_valid, cf_msg = validate_cloudflare_origin(raw_ip, headers)

        # Info de Cloudflare
        cf_info = get_cloudflare_info(headers)

        # Bloqueo por país
        country = cf_info.get("cf_country")
        blocked_countries = await get_blocked_countries()
        if is_country_blocked(country, blocked_countries):
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=403,
                content={
                    "detail": f"Acceso bloqueado desde {country}. Contacte soporte si cree que es un error."
                },
            )

        risk = assess_client_risk(
            ip=client_ip,
            headers=headers,
            user_agent=user_agent,
        )

        fingerprint = device_fingerprint(client_ip, user_agent, accept_lang)

        # Auto-block IPs with extreme risk score (>= 80)
        if risk["score"] >= 80 and client_ip != "unknown":
            async with AsyncSessionLocal() as db:
                existing = await db.execute(
                    select(BlockedIP).where(BlockedIP.ip_address == client_ip)
                )
                if not existing.scalar_one_or_none():
                    block = BlockedIP(
                        ip_address=client_ip,
                        reason="threat_intel",
                        blocked_until=datetime.now(timezone.utc) + timedelta(hours=24),
                    )
                    db.add(block)
                    await db.commit()

        # Guardar en request.state para uso posterior
        request.state.client_ip = client_ip
        request.state.risk_score = risk["score"]
        request.state.risk_flags = risk
        request.state.device_fingerprint = fingerprint
        request.state.cloudflare_info = cf_info
        request.state.cloudflare_valid = cf_valid
        request.state.cloudflare_msg = cf_msg

        response = await call_next(request)

        # Inyectar headers de cooperación con seguridad del endpoint
        if risk["mitm_detected"]:
            response.headers["X-Security-Warning"] = "MITM_DETECTED"
        if risk["is_vpn"]:
            response.headers["X-Connection-Type"] = "VPN"
        if risk["is_tor"]:
            response.headers["X-Connection-Type"] = "TOR"
        if cf_info["is_cloudflare"]:
            response.headers["X-CDN"] = "Cloudflare"

        return response
