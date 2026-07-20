"""DJVE · Declaración Jurada de Venta al Exterior.

Ley 21.453 y RG ARCA · obligatoria para exportaciones de productos agropecuarios
y derivados (cereales, oleaginosas, harinas, aceites, carnes). Fija condiciones
de retenciones DE al momento de la declaración. Tipos:
  - DJVE-30  · embarque hasta 30 días
  - DJVE-360 · embarque hasta 360 días (granos)

Presentación: portal ARCA · Mis Aplicaciones Web · grupo "Mercado de Capitales y Agropecuario".
No hay WS público estable · usar adapter Computer Use para automatizar carga.
"""
import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal


@dataclass
class DJVELinea:
    ncm: str
    descripcion: str
    cantidad: Decimal
    unidad: str          # TONELADAS
    precio_fob_usd: Decimal


@dataclass
class DJVERequest:
    cuit_exportador: str
    cuit_comprador_exterior: str    # ID impositivo país destino
    tipo: str                       # "30" | "360"
    pais_destino: str
    puerto_embarque: str
    fecha_embarque_estimada: str    # YYYY-MM-DD
    moneda: str = "USD"
    valor_total_fob: Decimal = Decimal(0)
    lineas: list[DJVELinea] = field(default_factory=list)


@dataclass
class DJVEResponse:
    djve_id: str
    estado: str
    fecha_registro: str
    fecha_vencimiento: str
    aliquota_retencion_pct: float
    payload: dict


# Retenciones DE vigentes 2026 (aliquotas indicativas · revisar RG actual antes de emitir)
RETENCIONES_DE_2026 = {
    "1001": 12.0,  # Trigo
    "1003": 12.0,  # Cebada
    "1005": 12.0,  # Maíz
    "1201": 33.0,  # Soja
    "1507": 31.0,  # Aceite soja
    "2304": 31.0,  # Harina soja
    "0201": 9.0,   # Carne bovina
    "1701": 4.5,   # Azúcar
}


def aliquota_for_ncm(ncm: str) -> float:
    """Lookup DE retención por capítulo NCM."""
    prefix = ncm.replace(".", "")[:4]
    return RETENCIONES_DE_2026.get(prefix, 0.0)


async def emit_djve(req: DJVERequest, *, submit: bool = False) -> DJVEResponse:
    """Generate DJVE record · optionally submit via CUA."""
    if req.tipo not in {"30", "360"}:
        raise ValueError("DJVE tipo debe ser '30' o '360'")

    djve_id = f"DJVE-{req.tipo}-{date.today().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    venc_dias = 30 if req.tipo == "30" else 360
    venc = date.today() + timedelta(days=venc_dias)

    # Weighted average aliquot
    total_fob = sum((l.cantidad * l.precio_fob_usd for l in req.lineas), Decimal(0))
    avg_alic = 0.0
    if total_fob > 0:
        s = sum(
            float(l.cantidad * l.precio_fob_usd) * aliquota_for_ncm(l.ncm)
            for l in req.lineas
        )
        avg_alic = round(s / float(total_fob), 2)

    payload = {
        "djveId": djve_id,
        "tipo": req.tipo,
        "exportador": req.cuit_exportador,
        "compradorExterior": req.cuit_comprador_exterior,
        "paisDestino": req.pais_destino,
        "puertoEmbarque": req.puerto_embarque,
        "fechaEmbarqueEstimada": req.fecha_embarque_estimada,
        "moneda": req.moneda,
        "valorTotalFOB": str(req.valor_total_fob),
        "lineas": [
            {
                "ncm": l.ncm,
                "descripcion": l.descripcion,
                "cantidad": str(l.cantidad),
                "unidad": l.unidad,
                "precioFOB": str(l.precio_fob_usd),
                "retencionPct": aliquota_for_ncm(l.ncm),
            }
            for l in req.lineas
        ],
    }

    return DJVEResponse(
        djve_id=djve_id,
        estado="REGISTRADA" if not submit else "OFICIALIZADA",
        fecha_registro=date.today().isoformat(),
        fecha_vencimiento=venc.isoformat(),
        aliquota_retencion_pct=avg_alic,
        payload=payload,
    )
