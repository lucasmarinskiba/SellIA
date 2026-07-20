"""ARCA (ex-AFIP) · WSFEX · Factura electrónica de exportación.

Service: wsfex (separate from wsfev1). Supports:
  - Cbte tipo 19 (Factura E)  · venta de bienes/servicios al exterior
  - Cbte tipo 20 (Nota Débito E)
  - Cbte tipo 21 (Nota Crédito E)

Required fields beyond domestic factura:
  - Idioma_cbte (1=es, 2=en, 3=pt)
  - Cliente país destino (Dst_cmp · ISO numeric ARCA code)
  - Cliente Razón Social + ID impositivo
  - Permiso de embarque (PE) numbers (one per item) when concepto=1 (productos)
  - Incoterms (FOB, CIF, EXW, CFR, etc.)
  - Detalle de mercadería con código y unidad de medida

Endpoint:
  homo · https://wswhomo.afip.gov.ar/wsfexv1/service.asmx
  prod · https://servicios1.afip.gov.ar/wsfexv1/service.asmx
"""
import logging
from dataclasses import dataclass, field
from decimal import Decimal

import httpx

from app.integrations.afip.wsaa import AFIPClient


logger = logging.getLogger(__name__)


WSFEX_URL_HOMO = "https://wswhomo.afip.gov.ar/wsfexv1/service.asmx"
WSFEX_URL_PROD = "https://servicios1.afip.gov.ar/wsfexv1/service.asmx"


@dataclass
class ItemExport:
    codigo: str
    descripcion: str
    cantidad: Decimal
    umed: int                # Unidad de medida (7=unidades, 1=kg, 3=mt, ...)
    precio_unit: Decimal
    bonif: Decimal = Decimal(0)
    total_item: Decimal = Decimal(0)


@dataclass
class FacturaExportRequest:
    pto_vta: int
    cbte_tipo: int = 19              # 19=Fact E, 20=ND E, 21=NC E
    fecha: str = ""                  # YYYYMMDD
    concepto: int = 1                # 1=Productos, 2=Servicios, 4=Otros
    dst_cmp: int = 0                 # Código país destino (ARCA Codes · 200=USA, 203=Brasil, 212=Chile)
    cliente_razon_social: str = ""
    cliente_domicilio: str = ""
    cliente_id_impositivo: str = ""  # Tax ID extranjero
    moneda_id: str = "DOL"           # DOL · EUR · BRL · etc.
    moneda_cotiz: Decimal = Decimal(1)
    incoterms: str = "FOB"           # FOB · CIF · EXW · CFR · CPT · DAP
    incoterms_dsc: str = ""
    idioma_cbte: int = 2             # 1=es, 2=en, 3=pt
    imp_total: Decimal = Decimal(0)
    permisos: list[str] = field(default_factory=list)  # ['25001IC04000001U']
    items: list[ItemExport] = field(default_factory=list)
    obs_comerciales: str = ""
    cbtes_asoc: list[dict] = field(default_factory=list)  # [{cbte_tipo, pto_vta, cbte_nro, cuit}]


@dataclass
class FacturaExportResponse:
    cae: str
    cae_fch_vto: str
    cbte_nro: int
    resultado: str
    observaciones: list[str]


async def emit_factura_export(
    afip: AFIPClient,
    fact: FacturaExportRequest,
    *,
    production: bool = False,
) -> FacturaExportResponse:
    """Emit factura E (export) via WSFEX · obtains CAE."""
    if afip.service != "wsfex":
        raise ValueError("AFIPClient.service must be 'wsfex' for export invoicing")

    auth = await afip.get_auth()
    url = WSFEX_URL_PROD if production else WSFEX_URL_HOMO

    # Get next id if not provided
    last_id = await _wsfex_last_id(url, auth, fact.pto_vta, fact.cbte_tipo)
    cbte_id = last_id + 1

    envelope = _build_authorize_envelope(auth, fact, cbte_id)
    async with httpx.AsyncClient(timeout=45.0) as c:
        r = await c.post(
            url,
            content=envelope,
            headers={
                "Content-Type": "text/xml; charset=UTF-8",
                "SOAPAction": "http://ar.gov.afip.dif.fexv1/FEXAuthorize",
            },
        )
        r.raise_for_status()

    return _parse_authorize_response(r.text, cbte_id)


async def _wsfex_last_id(url: str, auth, pto_vta: int, cbte_tipo: int) -> int:
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:fex="http://ar.gov.afip.dif.fexv1/">
  <soap:Body>
    <fex:FEXGetLast_ID>
      <fex:Auth>
        <fex:Token>{auth.token}</fex:Token>
        <fex:Sign>{auth.sign}</fex:Sign>
        <fex:Cuit>{auth.cuit}</fex:Cuit>
        <fex:Pto_venta>{pto_vta}</fex:Pto_venta>
        <fex:Cbte_Tipo>{cbte_tipo}</fex:Cbte_Tipo>
      </fex:Auth>
    </fex:FEXGetLast_ID>
  </soap:Body>
</soap:Envelope>"""
    async with httpx.AsyncClient(timeout=15.0) as c:
        r = await c.post(url, content=body, headers={"Content-Type": "text/xml; charset=UTF-8", "SOAPAction": "http://ar.gov.afip.dif.fexv1/FEXGetLast_ID"})
        r.raise_for_status()
    import re
    m = re.search(r"<Id_ultimo>(\d+)</Id_ultimo>", r.text)
    return int(m.group(1)) if m else 0


def _build_authorize_envelope(auth, f: FacturaExportRequest, cbte_id: int) -> str:
    items_xml = "".join(
        f"""<fex:Item>
              <fex:Pro_codigo>{it.codigo}</fex:Pro_codigo>
              <fex:Pro_ds>{_xml_escape(it.descripcion)}</fex:Pro_ds>
              <fex:Pro_qty>{it.cantidad}</fex:Pro_qty>
              <fex:Pro_umed>{it.umed}</fex:Pro_umed>
              <fex:Pro_precio_uni>{it.precio_unit}</fex:Pro_precio_uni>
              <fex:Pro_bonificacion>{it.bonif}</fex:Pro_bonificacion>
              <fex:Pro_total_item>{it.total_item or (it.cantidad * it.precio_unit - it.bonif)}</fex:Pro_total_item>
            </fex:Item>"""
        for it in f.items
    )
    permisos_xml = "".join(
        f"<fex:Permiso><fex:Id_permiso>{p}</fex:Id_permiso><fex:Dst_merc>{f.dst_cmp}</fex:Dst_merc></fex:Permiso>"
        for p in f.permisos
    )
    asoc_xml = "".join(
        f"""<fex:Cmp_asoc>
              <fex:Cbte_tipo>{a.get('cbte_tipo')}</fex:Cbte_tipo>
              <fex:Cbte_punto_vta>{a.get('pto_vta')}</fex:Cbte_punto_vta>
              <fex:Cbte_nro>{a.get('cbte_nro')}</fex:Cbte_nro>
              <fex:Cbte_cuit>{a.get('cuit')}</fex:Cbte_cuit>
            </fex:Cmp_asoc>"""
        for a in f.cbtes_asoc
    )

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:fex="http://ar.gov.afip.dif.fexv1/">
  <soap:Body>
    <fex:FEXAuthorize>
      <fex:Auth>
        <fex:Token>{auth.token}</fex:Token>
        <fex:Sign>{auth.sign}</fex:Sign>
        <fex:Cuit>{auth.cuit}</fex:Cuit>
      </fex:Auth>
      <fex:Cmp>
        <fex:Id>{cbte_id}</fex:Id>
        <fex:Fecha_cbte>{f.fecha}</fex:Fecha_cbte>
        <fex:Cbte_Tipo>{f.cbte_tipo}</fex:Cbte_Tipo>
        <fex:Punto_vta>{f.pto_vta}</fex:Punto_vta>
        <fex:Cbte_nro>{cbte_id}</fex:Cbte_nro>
        <fex:Tipo_expo>{f.concepto}</fex:Tipo_expo>
        <fex:Permiso_existente>{'S' if f.permisos else 'N'}</fex:Permiso_existente>
        <fex:Dst_cmp>{f.dst_cmp}</fex:Dst_cmp>
        <fex:Cliente>{_xml_escape(f.cliente_razon_social)}</fex:Cliente>
        <fex:Cuit_pais_cliente>0</fex:Cuit_pais_cliente>
        <fex:Domicilio_cliente>{_xml_escape(f.cliente_domicilio)}</fex:Domicilio_cliente>
        <fex:Id_impositivo>{_xml_escape(f.cliente_id_impositivo)}</fex:Id_impositivo>
        <fex:Moneda_Id>{f.moneda_id}</fex:Moneda_Id>
        <fex:Moneda_ctz>{f.moneda_cotiz}</fex:Moneda_ctz>
        <fex:Obs_comerciales>{_xml_escape(f.obs_comerciales)}</fex:Obs_comerciales>
        <fex:Imp_total>{f.imp_total}</fex:Imp_total>
        <fex:Obs></fex:Obs>
        <fex:Idioma_cbte>{f.idioma_cbte}</fex:Idioma_cbte>
        <fex:Incoterms>{f.incoterms}</fex:Incoterms>
        <fex:Incoterms_Ds>{_xml_escape(f.incoterms_dsc)}</fex:Incoterms_Ds>
        <fex:Items>{items_xml}</fex:Items>
        <fex:Permisos>{permisos_xml}</fex:Permisos>
        <fex:Cmps_asoc>{asoc_xml}</fex:Cmps_asoc>
      </fex:Cmp>
    </fex:FEXAuthorize>
  </soap:Body>
</soap:Envelope>"""


def _parse_authorize_response(soap_xml: str, cbte_nro: int) -> FacturaExportResponse:
    import re
    cae_m = re.search(r"<Cae>(\d+)</Cae>", soap_xml)
    vto_m = re.search(r"<Fch_venc_Cae>(\d+)</Fch_venc_Cae>", soap_xml)
    res_m = re.search(r"<Resultado>([AR])</Resultado>", soap_xml)
    obs = re.findall(r"<Obs>([^<]+)</Obs>", soap_xml)
    return FacturaExportResponse(
        cae=cae_m.group(1) if cae_m else "",
        cae_fch_vto=vto_m.group(1) if vto_m else "",
        cbte_nro=cbte_nro,
        resultado=res_m.group(1) if res_m else "?",
        observaciones=obs,
    )


def _xml_escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"", "&quot;")
