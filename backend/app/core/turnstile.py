"""
Validación de Cloudflare Turnstile (CAPTCHA invisible).
Docs: https://developers.cloudflare.com/turnstile/
"""

import os
from typing import Optional

import httpx

TURNSTILE_VERIFY_URL = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
TURNSTILE_SECRET_KEY = os.getenv("TURNSTILE_SECRET_KEY", "")


async def verify_turnstile_token(token: str, remote_ip: Optional[str] = None) -> tuple[bool, str]:
    """
    Verifica un token de Cloudflare Turnstile.
    Retorna (success: bool, message: str).
    """
    if not TURNSTILE_SECRET_KEY:
        # En desarrollo sin secret key configurado, permitir
        if os.getenv("ENVIRONMENT", "development") == "development":
            return True, "Turnstile omitido en desarrollo"
        return False, "Turnstile secret key no configurado"

    if not token:
        return False, "Token de Turnstile requerido"

    data = {
        "secret": TURNSTILE_SECRET_KEY,
        "response": token,
    }
    if remote_ip:
        data["remoteip"] = remote_ip

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(TURNSTILE_VERIFY_URL, data=data)
            result = response.json()

        if result.get("success"):
            return True, "Turnstile validado correctamente"

        error_codes = result.get("error-codes", ["unknown"])
        return False, f"Turnstile rechazado: {', '.join(error_codes)}"

    except Exception as e:
        return False, f"Error al verificar Turnstile: {str(e)}"
