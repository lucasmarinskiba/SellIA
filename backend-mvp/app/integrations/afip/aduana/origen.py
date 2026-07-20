"""Certificado de Origen MERCOSUR / ALADI / SGP.

Emisor habilitado: Cámara de Comercio (CAC), Cámara Argentina Importadores y Exportadores,
o ARCA según el régimen. Documento que prueba que mercadería califica para preferencias
arancelarias bilaterales.

Regímenes soportados:
  - MERCOSUR (ACE-18): Brasil, Paraguay, Uruguay, Bolivia, Venezuela suspendida
  - ALADI: México, Cuba, Ecuador, Perú, Colombia, Chile, Venezuela (ACE bilaterales)
  - SGP: USA, UE, Canadá, Japón, Australia · preferencias unilaterales
  - CAN: Bolivia, Ecuador, Colombia, Perú
  - Otros: India (PTA), Israel, Egipto, SACU
"""
import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal


REGIMENES_ORIGEN = {
    "MERCOSUR": {"vigencia_dias": 180, "form": "Form ALADI/ACE-18"},
    "ALADI":    {"vigencia_dias": 180, "form": "Form ALADI"},
    "SGP":      {"vigencia_dias": 365, "form": "Form A"},
    "CAN":      {"vigencia_dias": 180, "form": "Form CAN"},
    "BILATERAL":{"vigencia_dias": 365, "form": "Generic"},
}


@dataclass
class CertificadoOrigen:
    cert_id: str
    regimen: str
    pais_destino: str
    fecha_emision: str
    fecha_vencimiento: str
    exportador: dict
    importador: dict
    consignatario: dict | None
    productor: dict | None
    items: list[dict]
    medios_transporte: str
    factura_e_nro: str
    declaracion_origen: str
    sello_camara_url: str | None = None
    metadata: dict = field(default_factory=dict)


def generate_origin_certificate(
    *,
    regimen: str,
    pais_destino: str,
    exportador: dict,
    importador: dict,
    items: list[dict],
    factura_e_nro: str,
    consignatario: dict | None = None,
    productor: dict | None = None,
    medios_transporte: str = "Marítimo",
) -> CertificadoOrigen:
    """Build a Certificado de Origen ready to print + sellar in CAC."""
    reg = regimen.upper()
    if reg not in REGIMENES_ORIGEN:
        raise ValueError(f"Régimen '{regimen}' no soportado. Opciones: {list(REGIMENES_ORIGEN)}")

    info = REGIMENES_ORIGEN[reg]
    today = date.today()
    vence = today + timedelta(days=info["vigencia_dias"])

    declaracion = (
        f"El que suscribe declara que las mercaderías indicadas en el presente certificado "
        f"son originarias de Argentina y cumplen con las disposiciones del régimen {reg} "
        f"para el país destino {pais_destino}. Factura comercial asociada: {factura_e_nro}."
    )

    return CertificadoOrigen(
        cert_id=f"CO-{reg}-{today.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}",
        regimen=reg,
        pais_destino=pais_destino,
        fecha_emision=today.isoformat(),
        fecha_vencimiento=vence.isoformat(),
        exportador=exportador,
        importador=importador,
        consignatario=consignatario,
        productor=productor,
        items=items,
        medios_transporte=medios_transporte,
        factura_e_nro=factura_e_nro,
        declaracion_origen=declaracion,
        metadata={"form": info["form"], "valido_hasta": vence.isoformat()},
    )
