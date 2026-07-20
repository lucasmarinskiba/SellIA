"""
Servicio de geolocalización IP y geofencing.

Usa la API gratuita ip-api.com para obtener coordenadas de una IP.
Para producción, se recomienda MaxMind GeoIP2.
"""

import os
import math
import aiohttp
from typing import Optional, Tuple
from fastapi import HTTPException

GEO_API_URL = "http://ip-api.com/json/{ip}?fields=status,country,countryCode,region,city,lat,lon,query"

# IPs privadas (no geolocalizables)
_PRIVATE_IPS = {"127.0.0.1", "localhost", "::1", "0:0:0:0:0:0:0:1"}


def _is_private_ip(ip: str) -> bool:
    if not ip:
        return True
    ip = ip.strip()
    if ip in _PRIVATE_IPS:
        return True
    # IPv4 privadas
    parts = ip.split(".")
    if len(parts) == 4:
        try:
            first, second = int(parts[0]), int(parts[1])
            if first == 10:
                return True
            if first == 172 and 16 <= second <= 31:
                return True
            if first == 192 and second == 168:
                return True
            if first == 127:
                return True
        except ValueError:
            pass
    return False


async def get_ip_geolocation(ip: str) -> Optional[dict]:
    """
    Obtiene datos de geolocalización de una IP.
    
    Retorna dict con:
      country, country_code, region, city, latitude, longitude, ip
    
    Para IPs privadas retorna None (no se puede geolocalizar).
    """
    if _is_private_ip(ip):
        return None

    url = GEO_API_URL.format(ip=ip)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=3)) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                if data.get("status") != "success":
                    return None
                return {
                    "country": data.get("country"),
                    "country_code": data.get("countryCode"),
                    "region": data.get("region"),
                    "city": data.get("city"),
                    "latitude": data.get("lat"),
                    "longitude": data.get("lon"),
                    "ip": data.get("query") or ip,
                }
    except Exception as e:
        from app.core.logger import get_logger
        get_logger(__name__).warning(f"Error geolocalizando IP: {e}")
        return None


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calcula distancia en kilómetros entre dos coordenadas usando la fórmula de Haversine.
    """
    R = 6371.0  # Radio de la Tierra en km
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad)
        * math.cos(lat2_rad)
        * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return R * c


def is_geofence_violation(
    last_lat: Optional[float],
    last_lon: Optional[float],
    current_lat: Optional[float],
    current_lon: Optional[float],
    max_distance_km: float,
) -> Tuple[bool, float]:
    """
    Verifica si la distancia entre dos coordenadas excede el límite.
    
    Returns:
        (violation: bool, distance_km: float)
    """
    if not all([last_lat, last_lon, current_lat, current_lon]):
        # Sin datos de ubicación, no podemos determinar violación
        return False, 0.0
    
    distance = haversine_distance(last_lat, last_lon, current_lat, current_lon)
    
    if max_distance_km <= 0:
        # 0 o negativo = geofencing desactivado
        return False, distance
    
    return distance > max_distance_km, distance
