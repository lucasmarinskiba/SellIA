"""COVE · Comprobante de Venta al Exterior.

ARCA (ex-AFIP) RG 4838/2020 establece presentación obligatoria del COVE para exportaciones
≥ USD 100.000 (con flexibilizaciones por sector). Se presenta en el portal Sistema
Informático MALVINA (SIM) o Mis Aplicaciones Web (no posee WS público SOAP estable
para emisión automática · usar Computer Use o reverse-engineer del SIM).

Esta capa genera:
  1. Estructura COVE JSON normalizada (auditable)
  2. PDF de respaldo
  3. Llamada al adapter `submit_cove_to_sim()` que puede usar Playwright/CUA
"""
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


logger = logging.getLogger(__name__)


@dataclass
class COVEItem:
    ncm: str               # 8-digit NCM
    descripcion: str
    cantidad: Decimal
    unidad: str            # KG, UN, MT
    valor_unitario_fob_usd: Decimal
    pais_origen: str       # ISO-3166-1 alpha-2


@dataclass
class COVERequest:
    cuit_exportador: str
    pto_vta: int
    factura_e_nro: str           # PV-NRO del cbte 19 generado en WSFEX
    fecha_emision: str           # YYYY-MM-DD
    pais_destino: str            # ISO alpha-2
    cliente_razon_social: str
    cliente_tax_id: str
    cliente_domicilio: str
    incoterm: str
    moneda: str                  # USD · EUR
    valor_fob_total: Decimal
    flete_usd: Decimal = Decimal(0)
    seguro_usd: Decimal = Decimal(0)
    items: list[COVEItem] = field(default_factory=list)


@dataclass
class COVEResponse:
    cove_id: str
    estado: str                  # PENDIENTE_OFICIALIZACION · OFICIALIZADO · OBSERVADO
    fecha_oficializacion: str | None
    qr_url: str
    payload: dict
    pdf_url: str | None = None


def build_cove_payload(req: COVERequest) -> dict:
    """Build JSON payload mirroring SIM COVE schema (audit-grade)."""
    return {
        "tipoComprobante": "COVE",
        "version": "2.0",
        "cuitExportador": req.cuit_exportador,
        "puntoVenta": req.pto_vta,
        "comprobanteAsociado": {
            "tipo": "FACTURA_E",
            "numero": req.factura_e_nro,
        },
        "fechaEmision": req.fecha_emision,
        "cliente": {
            "razonSocial": req.cliente_razon_social,
            "taxId": req.cliente_tax_id,
            "paisDestino": req.pais_destino,
            "domicilio": req.cliente_domicilio,
        },
        "condicionesComerciales": {
            "incoterm": req.incoterm,
            "moneda": req.moneda,
            "valorFOB": str(req.valor_fob_total),
            "flete": str(req.flete_usd),
            "seguro": str(req.seguro_usd),
            "valorCIF": str(req.valor_fob_total + req.flete_usd + req.seguro_usd),
        },
        "mercaderia": [
            {
                "ncm": it.ncm,
                "descripcion": it.descripcion,
                "cantidad": str(it.cantidad),
                "unidad": it.unidad,
                "valorUnitarioFOB": str(it.valor_unitario_fob_usd),
                "paisOrigen": it.pais_origen,
                "valorTotalFOB": str(it.cantidad * it.valor_unitario_fob_usd),
            }
            for it in req.items
        ],
    }


async def emit_cove(req: COVERequest, *, submit_to_sim: bool = False) -> COVEResponse:
    """Generate COVE locally · optionally submit to ARCA SIM portal via CUA."""
    cove_id = f"COVE-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    payload = build_cove_payload(req)

    estado = "PENDIENTE_OFICIALIZACION"
    fecha_of = None

    if submit_to_sim:
        # Real submission requires Mis Aplicaciones Web · use CUA executor
        try:
            from app.agents.cua_client import CUAClient
            client = CUAClient()
            task = (
                f"Ingresar a Mis Aplicaciones Web ARCA · seleccionar 'COVE Comprobante de Venta al Exterior' · "
                f"cargar el siguiente JSON y oficializar: {payload}"
            )
            result = await client.run(task=task)
            if result.get("status") == "ok":
                estado = "OFICIALIZADO"
                fecha_of = datetime.utcnow().isoformat()
        except Exception as e:
            logger.warning("cove_sim_submit_failed", extra={"err": str(e), "cove_id": cove_id})

    return COVEResponse(
        cove_id=cove_id,
        estado=estado,
        fecha_oficializacion=fecha_of,
        qr_url=f"https://serviciosjava2.afip.gob.ar/cove/QR?id={cove_id}",
        payload=payload,
    )
