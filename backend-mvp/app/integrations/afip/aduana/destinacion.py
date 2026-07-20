"""Destinación de Exportación · Permiso de Embarque (PE).

El despacho de exportación pasa por:
  1. COVE / DJVE registrado
  2. Solicitud de Destinación (PE) en SIM MALVINA por el despachante
  3. Asignación de canal (verde, naranja, rojo)
  4. Cumplido de embarque · cumplido aduanero
  5. Estampillado y liquidación de derechos / reintegros

No existe WS público SOAP estable para emisión de PE · se interactúa con SIM mediante
clave fiscal nivel 3 + despachante de aduana. Este módulo prepara el dossier completo
y opcionalmente automatiza la carga vía Computer Use.
"""
import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


CANALES = ("VERDE", "NARANJA", "ROJO", "PENDIENTE")


@dataclass
class PermisoEmbarque:
    pe_numero: str        # Estructura: AABBCCDDDDDDDDD · ej 25001IC04000001U
    estado: str
    canal: str
    fecha_oficializacion: str
    fecha_cumplido: str | None
    aduana_registro: str
    aduana_salida: str
    medio_transporte: str
    documento_transporte: str    # BL · AWB · CRT · TIF
    cuit_exportador: str
    cuit_consignatario: str | None
    pais_destino: str
    valor_fob_total_usd: Decimal
    items: list[dict]
    derechos_export_usd: Decimal
    reintegros_usd: Decimal
    cove_id: str | None
    djve_id: str | None
    factura_e: str
    metadata: dict = field(default_factory=dict)


def _pe_serial() -> str:
    """Format approx PE number · real numbering is assigned by ARCA SIM."""
    today = date.today()
    return f"{str(today.year)[2:]}001IC{today.month:02d}{uuid.uuid4().hex[:7].upper()}U"


async def request_permiso_embarque(
    *,
    cuit_exportador: str,
    pais_destino: str,
    aduana_registro: str = "001",        # Ezeiza · 001 default
    aduana_salida: str = "001",
    medio_transporte: str = "Aéreo",
    documento_transporte: str = "",
    valor_fob_total_usd: Decimal = Decimal(0),
    items: list[dict] | None = None,
    factura_e: str = "",
    cove_id: str | None = None,
    djve_id: str | None = None,
    submit_to_sim: bool = False,
    derechos_export_pct: float = 0.0,
    reintegros_pct: float = 0.0,
) -> PermisoEmbarque:
    """Build PE record · optionally automate carga in SIM MALVINA via CUA."""
    items = items or []
    derechos = (valor_fob_total_usd * Decimal(derechos_export_pct) / Decimal(100)).quantize(Decimal("0.01"))
    reintegros = (valor_fob_total_usd * Decimal(reintegros_pct) / Decimal(100)).quantize(Decimal("0.01"))

    pe = PermisoEmbarque(
        pe_numero=_pe_serial(),
        estado="PENDIENTE_OFICIALIZACION",
        canal="PENDIENTE",
        fecha_oficializacion=date.today().isoformat(),
        fecha_cumplido=None,
        aduana_registro=aduana_registro,
        aduana_salida=aduana_salida,
        medio_transporte=medio_transporte,
        documento_transporte=documento_transporte,
        cuit_exportador=cuit_exportador,
        cuit_consignatario=None,
        pais_destino=pais_destino,
        valor_fob_total_usd=valor_fob_total_usd,
        items=items,
        derechos_export_usd=derechos,
        reintegros_usd=reintegros,
        cove_id=cove_id,
        djve_id=djve_id,
        factura_e=factura_e,
    )

    if submit_to_sim:
        try:
            from app.agents.cua_client import CUAClient
            client = CUAClient()
            task = (
                f"Ingresar al SIM MALVINA · módulo Destinaciones · Nueva PE Exportación · "
                f"cargar exportador CUIT {cuit_exportador} · destino {pais_destino} · "
                f"medio {medio_transporte} · COVE {cove_id} · DJVE {djve_id} · "
                f"items: {items} · valor FOB USD {valor_fob_total_usd} · oficializar."
            )
            result = await client.run(task=task)
            if result.get("status") == "ok":
                pe.estado = "OFICIALIZADO"
                pe.canal = result.get("canal", "VERDE")
        except Exception:
            pass

    return pe
