"""
Inteligencia de amenazas básica para detección de:
- VPN / Proxy / Tor exit nodes
- Headers anómalos propios de MITM / inspección SSL
- Device fingerprinting y anomalías de comportamiento
"""

import hashlib
import ipaddress
from typing import Set

# Tor exit nodes públicos (lista estática reducida; en producción se sincroniza periódicamente)
# Fuente: https://check.torproject.org/exit-addresses
KNOWN_TOR_EXITS: Set[str] = set()

# Rangos IP conocidos de proveedores VPN/Hosting populares (muestra representativa)
# En producción se debe integrar con una API como IPHub, IPinfo, o AbuseIPDB.
KNOWN_VPN_RANGES = [
    # NordVPN muestras
    ipaddress.ip_network("10.5.0.0/16"),  # dummy / ejemplo
    # Cloudflare WARP
    ipaddress.ip_network("172.64.0.0/13"),
    # OpenVPN genérico
]

# Headers que indican inspección SSL / MITM por proxies corporativos o antivirus
MITM_INDICATOR_HEADERS = [
    "x-bluecoat-via",
    "x-squid-via",
    "via",
    "x-forwarded-host",
    "x-http-host-override",
]

# User-Agents asociados a scanners / bots maliciosos conocidos
MALICIOUS_UA_PATTERNS = [
    "sqlmap",
    "nikto",
    "nmap",
    "masscan",
    "gobuster",
    "dirbuster",
    "burpsuite",
    "wfuzz",
    "ffuf",
    "zgrab",
    "censys",
    "shodan",
]


def is_tor_exit(ip: str) -> bool:
    return ip in KNOWN_TOR_EXITS


def is_known_vpn_range(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        for network in KNOWN_VPN_RANGES:
            if addr in network:
                return True
    except ValueError:
        pass
    return False


def is_private_ip(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def detect_mitm_headers(headers: dict) -> list[str]:
    found = []
    lower_headers = {k.lower(): v for k, v in headers.items()}
    for h in MITM_INDICATOR_HEADERS:
        if h in lower_headers:
            found.append(h)
    return found


def is_malicious_user_agent(ua: str | None) -> bool:
    if not ua:
        return False
    ua_lower = ua.lower()
    return any(pattern in ua_lower for pattern in MALICIOUS_UA_PATTERNS)


def device_fingerprint(ip: str, user_agent: str | None, accept_lang: str | None) -> str:
    """Genera un hash simple de fingerprint del dispositivo para detectar cambios."""
    raw = f"{ip}|{user_agent or ''}|{accept_lang or ''}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def assess_client_risk(
    ip: str,
    headers: dict,
    user_agent: str | None,
) -> dict:
    """
    Evalúa el riesgo del cliente basado en IP, headers y UA.
    Retorna un dict con flags de seguridad.
    """
    risk = {
        "ip": ip,
        "score": 0,  # 0-100
        "is_tor": False,
        "is_vpn": False,
        "is_private": False,
        "mitm_detected": False,
        "mitm_headers": [],
        "malicious_ua": False,
        "recommendations": [],
    }

    if is_private_ip(ip):
        risk["is_private"] = True
        return risk  # En desarrollo/local no penalizar

    if is_tor_exit(ip):
        risk["is_tor"] = True
        risk["score"] += 40
        risk["recommendations"].append("Conexión desde red Tor detectada. Se requiere verificación adicional.")

    if is_known_vpn_range(ip):
        risk["is_vpn"] = True
        risk["score"] += 15
        risk["recommendations"].append("VPN/Proxy detectado. Verifique que sea una conexión legitima.")

    mitm = detect_mitm_headers(headers)
    if mitm:
        risk["mitm_detected"] = True
        risk["mitm_headers"] = mitm
        risk["score"] += 25
        risk["recommendations"].append("Posible inspección SSL/MITM detectada. Asegurese de usar una conexion segura y verifique su antivirus/VPN.")

    if is_malicious_user_agent(user_agent):
        risk["malicious_ua"] = True
        risk["score"] += 50
        risk["recommendations"].append("User-Agent sospechoso detectado. Posible escaneo automatizado.")

    return risk
