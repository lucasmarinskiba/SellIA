"""ARCA (ex-AFIP) Argentina · integraciones impositivas y aduaneras.

Sub-módulos:
  - wsaa        · WSAA login (Token + Sign)
  - wsfe        · Factura electrónica doméstica (A/B/C)
  - wsfex       · Factura electrónica de exportación (E)
  - padron      · Padrón A13 · consulta CUIT
  - monotributo · Recategorización + cuota
  - aduana.*    · COVE, DJVE, certificados origen, permisos embarque, manifiestos

ARCA = Agencia de Recaudación y Control Aduanero (rebrand AFIP · Oct 2024).
Endpoints WSAA/WSFE/etc siguen apuntando a *.afip.gov.ar (transición progresiva).
"""
from app.integrations.afip.wsaa import AFIPClient, AFIPTokenAuth
from app.integrations.afip.wsfe import FacturaRequest, FacturaResponse, emit_factura
from app.integrations.afip.wsfex import (
    FacturaExportRequest, FacturaExportResponse, ItemExport, emit_factura_export,
)
from app.integrations.afip.padron import PadronPersona, consultar_padron
from app.integrations.afip.monotributo import (
    RecategorizacionResult, sugerir_categoria, proxima_recategorizacion,
    CATEGORIAS_SERVICIOS, CATEGORIAS_BIENES, CUOTA_MENSUAL,
)

# Alias semántico ARCA = AFIPClient
ARCAClient = AFIPClient

__all__ = [
    "AFIPClient", "ARCAClient", "AFIPTokenAuth",
    "FacturaRequest", "FacturaResponse", "emit_factura",
    "FacturaExportRequest", "FacturaExportResponse", "ItemExport", "emit_factura_export",
    "PadronPersona", "consultar_padron",
    "RecategorizacionResult", "sugerir_categoria", "proxima_recategorizacion",
    "CATEGORIAS_SERVICIOS", "CATEGORIAS_BIENES", "CUOTA_MENSUAL",
]
