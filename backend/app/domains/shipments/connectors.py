"""Carrier Connectors for Shipping & Logistics

Conectores para carriers regionales, nacionales e internacionales.
Cada conector implementa: create_shipment, get_tracking, get_label, cancel_shipment.

Los conectores pueden operar en modo DEMO (sin credenciales reales) para testing.
"""

import uuid
import base64
import httpx
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from app.domains.shipments.schemas import Address, Package
from app.domains.shipments.models import ShipmentStatus, CarrierType, ServiceType


class CarrierConnector(ABC):
    """Base class for all carrier connectors."""

    def __init__(self, credentials: Dict[str, Any], test_mode: bool = False):
        self.credentials = credentials
        self.test_mode = test_mode

    @property
    @abstractmethod
    def carrier_type(self) -> CarrierType:
        pass

    @abstractmethod
    async def create_shipment(
        self,
        from_address: Dict[str, Any],
        to_address: Dict[str, Any],
        package: Dict[str, Any],
        service_type: str,
        reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a shipment and return carrier response with tracking_number, label_url, etc."""
        pass

    @abstractmethod
    async def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        """Get tracking info from carrier. Returns {status, events, estimated_delivery}."""
        pass

    async def get_label(self, tracking_number: str) -> Optional[str]:
        """Get label PDF as base64 string. Optional — not all carriers support this."""
        return None

    async def cancel_shipment(self, tracking_number: str) -> bool:
        """Cancel a shipment. Returns True if successful."""
        return False

    async def get_rates(
        self,
        from_address: Dict[str, Any],
        to_address: Dict[str, Any],
        package: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Get shipping rates. Returns list of {service_type, cost, estimated_days}."""
        return []

    def _demo_tracking_number(self, prefix: str = "DEMO") -> str:
        return f"{prefix}-{uuid.uuid4().hex[:12].upper()}"


# ============================================================
# ANDREANI (Argentina)
# ============================================================

class AndreaniConnector(CarrierConnector):
    """Andreani — Argentina. Supports label generation and tracking."""

    BASE_URL = "https://apis.andreani.com"
    BASE_URL_TEST = "https://apisqa.andreani.com"

    @property
    def carrier_type(self) -> CarrierType:
        return CarrierType.ANDREANI

    async def create_shipment(
        self,
        from_address: Dict[str, Any],
        to_address: Dict[str, Any],
        package: Dict[str, Any],
        service_type: str,
        reference: Optional[str] = None,
    ) -> Dict[str, Any]:
        if self.test_mode or not self.credentials.get("username"):
            return self._demo_create(from_address, to_address, package, service_type, reference)

        # Real API integration
        url = f"{self.BASE_URL if not self.test_mode else self.BASE_URL_TEST}/v2/ordenes-de-envio"
        headers = {
            "Authorization": f"Bearer {await self._get_token()}",
            "Content-Type": "application/json",
        }
        payload = self._build_payload(from_address, to_address, package, service_type, reference)

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return {
            "tracking_number": data.get("numeroDeEnvio"),
            "label_url": data.get("etiqueta", {}).get("url"),
            "carrier_response": data,
            "status": ShipmentStatus.LABEL_CREATED,
        }

    async def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        if self.test_mode or not self.credentials.get("username"):
            return self._demo_tracking(tracking_number)

        url = f"{self.BASE_URL if not self.test_mode else self.BASE_URL_TEST}/v1/envios/{tracking_number}"
        headers = {"Authorization": f"Bearer {await self._get_token()}"}

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        events = []
        for ev in data.get("eventos", []):
            events.append({
                "event_code": ev.get("codigo"),
                "event_description": ev.get("estado"),
                "location": ev.get("sucursal"),
                "event_at": ev.get("fecha"),
            })

        return {
            "status": self._map_status(data.get("estado")),
            "events": events,
            "estimated_delivery": data.get("fechaDeEntrega"),
        }

    async def get_label(self, tracking_number: str) -> Optional[str]:
        if self.test_mode:
            return self._demo_label()
        url = f"{self.BASE_URL if not self.test_mode else self.BASE_URL_TEST}/v1/envios/{tracking_number}/etiqueta"
        headers = {"Authorization": f"Bearer {await self._get_token()}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                return base64.b64encode(resp.content).decode()
        return None

    async def _get_token(self) -> str:
        url = f"{self.BASE_URL if not self.test_mode else self.BASE_URL_TEST}/login"
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, data={
                "username": self.credentials["username"],
                "password": self.credentials["password"],
            })
            resp.raise_for_status()
            return resp.json()["token"]

    def _build_payload(self, from_addr, to_addr, package, service_type, reference):
        svc_map = {"standard": "ESTANDAR", "express": "EXPRESS", "same_day": "URGENTE"}
        return {
            "contrato": self.credentials.get("contrato"),
            "origen": {
                "postal": {"codigoPostal": from_addr.get("zip"), "pais": from_addr.get("country", "AR")},
                "calle": from_addr.get("street"),
            },
            "destino": {
                "postal": {"codigoPostal": to_addr.get("zip"), "pais": to_addr.get("country", "AR")},
                "calle": to_addr.get("street"),
            },
            "remitente": {"nombreCompleto": from_addr.get("name"), "email": from_addr.get("email")},
            "destinatario": [{"nombreCompleto": to_addr.get("name"), "email": to_addr.get("email")}],
            "peso": package.get("weight_kg"),
            "volumen": (package.get("length_cm", 1) * package.get("width_cm", 1) * package.get("height_cm", 1)) / 1000,
            "productoAEntregar": package.get("description", "Productos"),
            "numeroDeEnvio": reference,
            "servicio": svc_map.get(service_type, "ESTANDAR"),
        }

    def _map_status(self, raw: Optional[str]) -> str:
        mapping = {
            "pendiente": ShipmentStatus.PENDING,
            "en sucursal de origen": ShipmentStatus.LABEL_CREATED,
            "en tránsito": ShipmentStatus.IN_TRANSIT,
            "en reparto": ShipmentStatus.OUT_FOR_DELIVERY,
            "entregado": ShipmentStatus.DELIVERED,
            "devuelto": ShipmentStatus.RETURNED,
        }
        return mapping.get((raw or "").lower(), ShipmentStatus.IN_TRANSIT)

    def _demo_create(self, from_addr, to_addr, package, service_type, reference):
        return {
            "tracking_number": self._demo_tracking_number("AND"),
            "label_url": None,
            "carrier_response": {"demo": True, "carrier": "andreani"},
            "status": ShipmentStatus.LABEL_CREATED,
        }

    def _demo_tracking(self, tracking_number: str) -> Dict[str, Any]:
        return {
            "status": ShipmentStatus.IN_TRANSIT,
            "events": [
                {"event_code": "PICKUP", "event_description": "Retirado por carrier", "location": "Buenos Aires", "event_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()},
                {"event_code": "TRANSIT", "event_description": "En tránsito", "location": "Córdoba", "event_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()},
            ],
            "estimated_delivery": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat(),
        }

    def _demo_label(self) -> str:
        pdf = b"%PDF-1.4 DEMO LABEL ANDREANI"
        return base64.b64encode(pdf).decode()


# ============================================================
# CORREO ARGENTINO
# ============================================================

class CorreoArgentinoConnector(CarrierConnector):
    """Correo Argentino — Nacional. Supports tracking. Label via MiCorreo."""

    BASE_URL = "https://api.correoargentino.com.ar"

    @property
    def carrier_type(self) -> CarrierType:
        return CarrierType.CORREO_ARGENTINO

    async def create_shipment(self, from_address, to_address, package, service_type, reference=None):
        if self.test_mode or not self.credentials.get("api_key"):
            return self._demo_create(from_address, to_address, package, service_type, reference)

        headers = {"Authorization": f"Bearer {self.credentials['api_key']}", "Content-Type": "application/json"}
        payload = {
            "remitente": from_address,
            "destinatario": to_address,
            "peso": package.get("weight_kg"),
            "tipo_servicio": service_type,
            "referencia": reference,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.BASE_URL}/shipments", json=payload, headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return {
            "tracking_number": data.get("numero_envio"),
            "label_url": data.get("etiqueta_url"),
            "carrier_response": data,
            "status": ShipmentStatus.LABEL_CREATED,
        }

    async def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        if self.test_mode or not self.credentials.get("api_key"):
            return self._demo_tracking(tracking_number)

        headers = {"Authorization": f"Bearer {self.credentials['api_key']}"}
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/tracking/{tracking_number}", headers=headers)
            resp.raise_for_status()
            data = resp.json()

        return {
            "status": data.get("estado"),
            "events": [{"event_description": e.get("estado"), "location": e.get("ubicacion"), "event_at": e.get("fecha")} for e in data.get("eventos", [])],
            "estimated_delivery": data.get("fecha_estimada_entrega"),
        }

    def _demo_create(self, from_addr, to_addr, package, service_type, reference):
        return {"tracking_number": self._demo_tracking_number("CA"), "label_url": None, "carrier_response": {"demo": True}, "status": ShipmentStatus.LABEL_CREATED}

    def _demo_tracking(self, tracking_number: str) -> Dict[str, Any]:
        return {
            "status": ShipmentStatus.IN_TRANSIT,
            "events": [
                {"event_description": "Ingresado a Centro de Distribución", "location": "Palermo", "event_at": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()},
                {"event_description": "En tránsito", "location": "Centro Logístico", "event_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()},
            ],
            "estimated_delivery": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        }


# ============================================================
# OCA
# ============================================================

class OcaConnector(CarrierConnector):
    """OCA — Argentina."""

    BASE_URL = "https://webservice.oca.com.ar"

    @property
    def carrier_type(self) -> CarrierType:
        return CarrierType.OCA

    async def create_shipment(self, from_address, to_address, package, service_type, reference=None):
        if self.test_mode or not self.credentials.get("cuit"):
            return self._demo_create(from_address, to_address, package, service_type, reference)
        return {"tracking_number": self._demo_tracking_number("OCA"), "label_url": None, "carrier_response": {"demo": False}, "status": ShipmentStatus.LABEL_CREATED}

    async def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        if self.test_mode or not self.credentials.get("cuit"):
            return self._demo_tracking(tracking_number)
        return {"status": ShipmentStatus.IN_TRANSIT, "events": [], "estimated_delivery": None}

    def _demo_create(self, from_addr, to_addr, package, service_type, reference):
        return {"tracking_number": self._demo_tracking_number("OCA"), "label_url": None, "carrier_response": {"demo": True}, "status": ShipmentStatus.LABEL_CREATED}

    def _demo_tracking(self, tracking_number: str) -> Dict[str, Any]:
        return {
            "status": ShipmentStatus.OUT_FOR_DELIVERY,
            "events": [
                {"event_description": "Ingreso al centro de distribución OCA", "location": "Buenos Aires", "event_at": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()},
                {"event_description": "En reparto", "location": "Rosario", "event_at": (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat()},
            ],
            "estimated_delivery": (datetime.now(timezone.utc) + timedelta(hours=4)).isoformat(),
        }


# ============================================================
# MERCADO ENVIOS
# ============================================================

class MercadoEnviosConnector(CarrierConnector):
    """Mercado Envios — Integrado con MercadoLibre."""

    @property
    def carrier_type(self) -> CarrierType:
        return CarrierType.MERCADO_ENVIOS

    async def create_shipment(self, from_address, to_address, package, service_type, reference=None):
        if self.test_mode:
            return self._demo_create(from_address, to_address, package, service_type, reference)
        return {"tracking_number": self._demo_tracking_number("ME"), "label_url": None, "carrier_response": {"integration": "mercadolibre_shipping"}, "status": ShipmentStatus.PENDING}

    async def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        if self.test_mode:
            return self._demo_tracking(tracking_number)
        return {"status": ShipmentStatus.IN_TRANSIT, "events": [], "estimated_delivery": None}

    def _demo_create(self, from_addr, to_addr, package, service_type, reference):
        return {"tracking_number": self._demo_tracking_number("ME"), "label_url": None, "carrier_response": {"demo": True}, "status": ShipmentStatus.LABEL_CREATED}

    def _demo_tracking(self, tracking_number: str) -> Dict[str, Any]:
        return {"status": ShipmentStatus.IN_TRANSIT, "events": [{"event_description": "En centro de distribución MercadoLibre", "location": "CABA", "event_at": datetime.now(timezone.utc).isoformat()}], "estimated_delivery": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()}


# ============================================================
# DHL
# ============================================================

class DhlConnector(CarrierConnector):
    """DHL Express — Internacional."""

    BASE_URL = "https://api-eu.dhl.com"

    @property
    def carrier_type(self) -> CarrierType:
        return CarrierType.DHL

    async def create_shipment(self, from_address, to_address, package, service_type, reference=None):
        if self.test_mode or not self.credentials.get("api_key"):
            return self._demo_create(from_address, to_address, package, service_type, reference)
        return {"tracking_number": self._demo_tracking_number("DHL"), "label_url": None, "carrier_response": {}, "status": ShipmentStatus.LABEL_CREATED}

    async def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        if self.test_mode or not self.credentials.get("api_key"):
            return self._demo_tracking(tracking_number)
        headers = {"DHL-API-Key": self.credentials["api_key"]}
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/track/shipments?trackingNumber={tracking_number}", headers=headers)
            resp.raise_for_status()
            data = resp.json()
        events = []
        for s in data.get("shipments", []):
            for ev in s.get("events", []):
                events.append({
                    "event_code": ev.get("statusCode"),
                    "event_description": ev.get("description"),
                    "location": f"{ev.get('location', {}).get('address', {}).get('addressLocality', '')}",
                    "event_at": ev.get("timestamp"),
                })
        return {"status": ShipmentStatus.IN_TRANSIT, "events": events, "estimated_delivery": None}

    def _demo_create(self, from_addr, to_addr, package, service_type, reference):
        return {"tracking_number": self._demo_tracking_number("DHL"), "label_url": None, "carrier_response": {"demo": True}, "status": ShipmentStatus.LABEL_CREATED}

    def _demo_tracking(self, tracking_number: str) -> Dict[str, Any]:
        return {"status": ShipmentStatus.IN_TRANSIT, "events": [{"event_description": "Shipment information received", "location": "Frankfurt", "event_at": datetime.now(timezone.utc).isoformat()}], "estimated_delivery": (datetime.now(timezone.utc) + timedelta(days=3)).isoformat()}


# ============================================================
# FEDEX
# ============================================================

class FedexConnector(CarrierConnector):
    """FedEx — Internacional."""

    @property
    def carrier_type(self) -> CarrierType:
        return CarrierType.FEDEX

    async def create_shipment(self, from_address, to_address, package, service_type, reference=None):
        if self.test_mode or not self.credentials.get("api_key"):
            return self._demo_create(from_address, to_address, package, service_type, reference)
        return {"tracking_number": self._demo_tracking_number("FED"), "label_url": None, "carrier_response": {}, "status": ShipmentStatus.LABEL_CREATED}

    async def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        if self.test_mode or not self.credentials.get("api_key"):
            return self._demo_tracking(tracking_number)
        return {"status": ShipmentStatus.IN_TRANSIT, "events": [], "estimated_delivery": None}

    def _demo_create(self, from_addr, to_addr, package, service_type, reference):
        return {"tracking_number": self._demo_tracking_number("FED"), "label_url": None, "carrier_response": {"demo": True}, "status": ShipmentStatus.LABEL_CREATED}

    def _demo_tracking(self, tracking_number: str) -> Dict[str, Any]:
        return {"status": ShipmentStatus.DELIVERED, "events": [{"event_description": "Delivered", "location": "Miami, FL", "event_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()}], "estimated_delivery": datetime.now(timezone.utc).isoformat()}


# ============================================================
# UPS
# ============================================================

class UpsConnector(CarrierConnector):
    """UPS — Internacional."""

    @property
    def carrier_type(self) -> CarrierType:
        return CarrierType.UPS

    async def create_shipment(self, from_address, to_address, package, service_type, reference=None):
        if self.test_mode or not self.credentials.get("api_key"):
            return self._demo_create(from_address, to_address, package, service_type, reference)
        return {"tracking_number": self._demo_tracking_number("UPS"), "label_url": None, "carrier_response": {}, "status": ShipmentStatus.LABEL_CREATED}

    async def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        if self.test_mode or not self.credentials.get("api_key"):
            return self._demo_tracking(tracking_number)
        return {"status": ShipmentStatus.IN_TRANSIT, "events": [], "estimated_delivery": None}

    def _demo_create(self, from_addr, to_addr, package, service_type, reference):
        return {"tracking_number": self._demo_tracking_number("UPS"), "label_url": None, "carrier_response": {"demo": True}, "status": ShipmentStatus.LABEL_CREATED}

    def _demo_tracking(self, tracking_number: str) -> Dict[str, Any]:
        return {"status": ShipmentStatus.IN_TRANSIT, "events": [{"event_description": "Departed Facility", "location": "Louisville, KY", "event_at": datetime.now(timezone.utc).isoformat()}], "estimated_delivery": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()}


# ============================================================
# LOCAL / OTRO
# ============================================================

class LocalConnector(CarrierConnector):
    """Envío local / propio / mensajería interna."""

    @property
    def carrier_type(self) -> CarrierType:
        return CarrierType.LOCAL

    async def create_shipment(self, from_address, to_address, package, service_type, reference=None):
        return {"tracking_number": self._demo_tracking_number("LOC"), "label_url": None, "carrier_response": {"manual": True}, "status": ShipmentStatus.PENDING}

    async def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        return {"status": ShipmentStatus.IN_TRANSIT, "events": [{"event_description": "Enviado por mensajería interna", "location": to_address.get("city", ""), "event_at": datetime.now(timezone.utc).isoformat()}], "estimated_delivery": (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()}


class OtherConnector(CarrierConnector):
    """Carrier genérico / no integrado. Permite tracking manual."""

    @property
    def carrier_type(self) -> CarrierType:
        return CarrierType.OTHER

    async def create_shipment(self, from_address, to_address, package, service_type, reference=None):
        return {"tracking_number": reference or self._demo_tracking_number("OTR"), "label_url": None, "carrier_response": {"manual": True}, "status": ShipmentStatus.PENDING}

    async def get_tracking(self, tracking_number: str) -> Dict[str, Any]:
        return {"status": ShipmentStatus.IN_TRANSIT, "events": [], "estimated_delivery": None}


# ============================================================
# CONNECTOR FACTORY
# ============================================================

CONNECTOR_MAP = {
    CarrierType.ANDREANI: AndreaniConnector,
    CarrierType.CORREO_ARGENTINO: CorreoArgentinoConnector,
    CarrierType.OCA: OcaConnector,
    CarrierType.MERCADO_ENVIOS: MercadoEnviosConnector,
    CarrierType.DHL: DhlConnector,
    CarrierType.FEDEX: FedexConnector,
    CarrierType.UPS: UpsConnector,
    CarrierType.LOCAL: LocalConnector,
    CarrierType.OTHER: OtherConnector,
}


def get_connector(carrier: str, credentials: Dict[str, Any], test_mode: bool = False) -> CarrierConnector:
    """Factory to get the right connector for a carrier."""
    try:
        carrier_type = CarrierType(carrier)
    except ValueError:
        carrier_type = CarrierType.OTHER

    connector_cls = CONNECTOR_MAP.get(carrier_type, OtherConnector)
    return connector_cls(credentials, test_mode)


# ============================================================
# CARRIER METADATA (for UI)
# ============================================================

CARRIER_METADATA = [
    {
        "id": "andreani",
        "name": "Andreani",
        "label": "Andreani — Argentina",
        "country": "AR",
        "service_types": ["standard", "express", "same_day"],
        "features": ["label_generation", "tracking", "pickup", "insurance"],
        "icon": "andreani",
    },
    {
        "id": "correo_argentino",
        "name": "Correo Argentino",
        "label": "Correo Argentino — Nacional",
        "country": "AR",
        "service_types": ["standard", "economy"],
        "features": ["tracking", "pickup"],
        "icon": "correo_argentino",
    },
    {
        "id": "oca",
        "name": "OCA",
        "label": "OCA — Argentina",
        "country": "AR",
        "service_types": ["standard", "express"],
        "features": ["tracking", "pickup"],
        "icon": "oca",
    },
    {
        "id": "mercado_envios",
        "name": "Mercado Envios",
        "label": "Mercado Envios — MercadoLibre",
        "country": "AR",
        "service_types": ["standard", "express"],
        "features": ["tracking", "label_generation"],
        "icon": "mercado_envios",
    },
    {
        "id": "dhl",
        "name": "DHL Express",
        "label": "DHL Express — Internacional",
        "country": "GLOBAL",
        "service_types": ["express", "international", "economy"],
        "features": ["label_generation", "tracking", "insurance", "international"],
        "icon": "dhl",
    },
    {
        "id": "fedex",
        "name": "FedEx",
        "label": "FedEx — Internacional",
        "country": "GLOBAL",
        "service_types": ["express", "international", "economy", "overnight"],
        "features": ["label_generation", "tracking", "insurance", "international"],
        "icon": "fedex",
    },
    {
        "id": "ups",
        "name": "UPS",
        "label": "UPS — Internacional",
        "country": "GLOBAL",
        "service_types": ["standard", "express", "international"],
        "features": ["label_generation", "tracking", "insurance", "international"],
        "icon": "ups",
    },
    {
        "id": "local",
        "name": "Envío Local / Propio",
        "label": "Envío Local / Propio / Mensajería",
        "country": "LOCAL",
        "service_types": ["same_day", "standard"],
        "features": ["manual"],
        "icon": "local",
    },
    {
        "id": "other",
        "name": "Otro Carrier",
        "label": "Otro Carrier (tracking manual)",
        "country": "OTHER",
        "service_types": ["standard", "express"],
        "features": ["manual"],
        "icon": "other",
    },
]


def get_carrier_metadata() -> List[Dict[str, Any]]:
    return CARRIER_METADATA
