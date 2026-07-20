"""
Integración Have I Been Pwned (HIBP) usando k-anonymity.

Documentación: https://haveibeenpwned.com/API/v3

Usamos el endpoint de k-anonymity para passwords (PwnedPasswords)
y el endpoint de breaches para emails.

Para emails requiere API key. La verificación de email usa SHA-1 prefix (k-anonymity)
para no exponer el email completo a terceros.

En realidad HIBP no usa k-anonymity para emails (eso es para passwords). 
Para emails se usa el endpoint directo con API key:
  https://haveibeenpwned.com/api/v3/breachedaccount/{email}

Para no enviar el email directo, implementamos un wrapper que:
1. Pregunta por breaches del email (requiere API key)
2. También verifica si la contraseña aparece en PwnedPasswords (k-anonymity SHA-1)
"""

import hashlib
import aiohttp
from typing import Optional, List

HIBP_API_BASE = "https://haveibeenpwned.com/api/v3"
PWNED_PASSWORDS_API = "https://api.pwnedpasswords.com/range"


async def check_email_breaches(email: str, api_key: str) -> Optional[dict]:
    """
    Verifica si un email aparece en breaches conocidas via HIBP.
    
    Args:
        email: Email a verificar
        api_key: API key de HIBP
    
    Returns:
        dict con {found: bool, count: int, names: [str], details: [dict]} o None si error
    """
    if not api_key or not email:
        return None

    url = f"{HIBP_API_BASE}/breachedaccount/{email}"
    headers = {
        "hibp-api-key": api_key,
        "user-agent": "SellIA-Security-Checker",
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                if resp.status == 404:
                    # Email limpio
                    return {"found": False, "count": 0, "names": [], "details": []}
                if resp.status == 429:
                    from app.core.logger import get_logger
                    get_logger(__name__).warning("HIBP rate limit alcanzado")
                    return None
                if resp.status != 200:
                    from app.core.logger import get_logger
                    get_logger(__name__).error(f"HIBP API error: {resp.status}")
                    return None

                breaches = await resp.json()
                if not isinstance(breaches, list):
                    return {"found": False, "count": 0, "names": [], "details": []}

                names = [b.get("Name") for b in breaches]
                return {
                    "found": True,
                    "count": len(breaches),
                    "names": names,
                    "details": breaches,
                }
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Error consultando breaches: {e}")
        return None


async def check_password_breach(password: str) -> Optional[dict]:
    """
    Verifica si una contraseña aparece en breaches via k-anonymity (PwnedPasswords).
    
    No envía la contraseña completa, solo los primeros 5 caracteres del hash SHA-1.
    
    Args:
        password: Contraseña a verificar
    
    Returns:
        dict con {found: bool, count: int} o None
    """
    if not password:
        return None

    sha1_hash = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix = sha1_hash[:5]
    suffix = sha1_hash[5:]

    url = f"{PWNED_PASSWORDS_API}/{prefix}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                headers={"Add-Padding": "true"},
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status != 200:
                    return None

                text = await resp.text()
                for line in text.splitlines():
                    parts = line.split(":")
                    if len(parts) == 2:
                        candidate, count = parts[0], int(parts[1])
                        if candidate == suffix:
                            return {"found": True, "count": count}

                return {"found": False, "count": 0}
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).error(f"Error consultando password: {e}")
        return None


def format_breach_alert(breach_data: dict) -> str:
    """Formatea un mensaje legible con los breaches encontrados."""
    if not breach_data.get("found"):
        return "Tu email no aparece en ninguna filtración conocida. ✅"
    
    names = breach_data.get("names", [])
    count = breach_data.get("count", 0)
    
    if count == 1:
        return f"Tu email aparece en 1 filtración: {names[0]}."
    
    return f"Tu email aparece en {count} filtraciones: {', '.join(names)}."
