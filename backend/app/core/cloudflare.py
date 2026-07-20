"""
Integración con Cloudflare WAF y servicios de seguridad.
Detecta requests que pasan por Cloudflare y extrae información de seguridad.
"""

import ipaddress
from typing import Optional

# Lista de rangos IP de Cloudflare (actualizada 2024)
# Fuente: https://www.cloudflare.com/ips/
CLOUDFLARE_IPV4_RANGES = [
    ipaddress.ip_network("173.245.48.0/20"),
    ipaddress.ip_network("103.21.244.0/22"),
    ipaddress.ip_network("103.22.200.0/22"),
    ipaddress.ip_network("103.31.4.0/22"),
    ipaddress.ip_network("141.101.64.0/18"),
    ipaddress.ip_network("108.162.192.0/18"),
    ipaddress.ip_network("190.93.240.0/20"),
    ipaddress.ip_network("188.114.96.0/20"),
    ipaddress.ip_network("197.234.240.0/22"),
    ipaddress.ip_network("198.41.128.0/17"),
    ipaddress.ip_network("162.158.0.0/15"),
    ipaddress.ip_network("104.16.0.0/13"),
    ipaddress.ip_network("104.24.0.0/14"),
    ipaddress.ip_network("172.64.0.0/13"),
    ipaddress.ip_network("131.0.72.0/22"),
]

CLOUDFLARE_IPV6_RANGES = [
    ipaddress.ip_network("2400:cb00::/32"),
    ipaddress.ip_network("2606:4700::/32"),
    ipaddress.ip_network("2803:f800::/32"),
    ipaddress.ip_network("2405:b500::/32"),
    ipaddress.ip_network("2405:8100::/32"),
    ipaddress.ip_network("2a06:98c0::/29"),
    ipaddress.ip_network("2c0f:f248::/32"),
]

# Países con alto riesgo (ejemplo, ajustable por configuración)
HIGH_RISK_COUNTRIES = {"CN", "RU", "KP", "IR"}


def is_cloudflare_ip(ip: str) -> bool:
    """Verifica si una IP pertenece a los rangos de Cloudflare."""
    try:
        addr = ipaddress.ip_address(ip)
        if isinstance(addr, ipaddress.IPv4Address):
            ranges = CLOUDFLARE_IPV4_RANGES
        else:
            ranges = CLOUDFLARE_IPV6_RANGES

        for network in ranges:
            if addr in network:
                return True
    except ValueError:
        pass
    return False


def get_client_ip_cloudflare(headers: dict, direct_ip: str) -> str:
    """
    Obtiene la IP real del cliente cuando el tráfico pasa por Cloudflare.
    Si no hay headers de Cloudflare, devuelve la IP directa.
    """
    cf_ip = headers.get("cf-connecting-ip")
    if cf_ip:
        return cf_ip

    # Fallback a X-Forwarded-For si no hay CF-Connecting-IP
    xff = headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()

    return direct_ip


def get_cloudflare_info(headers: dict) -> dict:
    """Extrae información de seguridad de los headers de Cloudflare."""
    info = {
        "is_cloudflare": False,
        "cf_ray": None,
        "cf_country": None,
        "cf_city": None,
        "cf_visitor_scheme": None,
        "cf_bot_management": None,
        "cf_threat_score": None,
        "cf_ja3_hash": None,
        "is_high_risk_country": False,
        "is_bot": False,
    }

    if "cf-ray" in headers:
        info["is_cloudflare"] = True
        info["cf_ray"] = headers.get("cf-ray")
        info["cf_country"] = headers.get("cf-ipcountry")
        info["cf_city"] = headers.get("cf-ipcity")
        info["cf_visitor_scheme"] = headers.get("cf-visitor")
        info["cf_bot_management"] = headers.get("cf-bot-management")
        info["cf_threat_score"] = headers.get("cf-threat-score")
        info["cf_ja3_hash"] = headers.get("cf-ja3-hash")

        if info["cf_country"] in HIGH_RISK_COUNTRIES:
            info["is_high_risk_country"] = True

        # Cloudflare Bot Management
        if info["cf_bot_management"]:
            info["is_bot"] = "bot" in info["cf_bot_management"].lower()

    return info


def validate_cloudflare_origin(client_ip: str, headers: dict) -> tuple[bool, str]:
    """
    Valida que el request provenga realmente de Cloudflare.
    En producción con Cloudflare, rechazar requests que no vengan de sus IPs.
    """
    if "cf-ray" not in headers:
        # No hay headers de Cloudflare, puede ser acceso directo
        return True, "Acceso directo (sin Cloudflare)"

    if not is_cloudflare_ip(client_ip):
        return False, f"IP {client_ip} no pertenece a Cloudflare. Posible spoofing de headers."

    return True, "Request validado como proveniente de Cloudflare"
