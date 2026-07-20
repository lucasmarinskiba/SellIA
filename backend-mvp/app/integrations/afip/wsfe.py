"""AFIP WSFE · Factura electrónica.

Uses AFIPClient.get_auth() to obtain Token+Sign · POSTs FECAESolicitar to WSFE endpoint.

For full SOAP coverage, integrate `pyafipws` or `afip.py` in prod.
This is a minimal happy-path implementation.
"""
import logging
from dataclasses import dataclass
from decimal import Decimal

import httpx

from app.integrations.afip.wsaa import AFIPClient


logger = logging.getLogger(__name__)


WSFE_URL_HOMO = "https://wswhomo.afip.gov.ar/wsfev1/service.asmx"
WSFE_URL_PROD = "https://servicios1.afip.gov.ar/wsfev1/service.asmx"


@dataclass
class FacturaRequest:
    pto_vta: int                # Punto de venta (e.g. 1, 2 ...)
    cbte_tipo: int              # 1=A, 6=B, 11=C, 51=E export, etc.
    concepto: int = 1           # 1=Productos, 2=Servicios, 3=Both
    doc_tipo: int = 80          # 80=CUIT, 86=CUIL, 96=DNI, 99=Consumidor Final
    doc_nro: int = 0            # 0 for CF < $$
    cbte_desde: int = 0         # AFIP returns next number if 0 (we query first)
    cbte_hasta: int = 0
    cbte_fch: str = ""          # YYYYMMDD
    imp_total: Decimal = Decimal(0)
    imp_neto: Decimal = Decimal(0)
    imp_iva: Decimal = Decimal(0)
    imp_trib: Decimal = Decimal(0)
    moneda_id: str = "PES"      # PES, DOL
    moneda_cotiz: Decimal = Decimal(1)


@dataclass
class FacturaResponse:
    cae: str
    cae_fch_vto: str            # YYYYMMDD
    cbte_nro: int
    resultado: str              # 'A'=approved, 'R'=rejected
    observaciones: list[str]


async def emit_factura(
    afip: AFIPClient,
    factura: FacturaRequest,
    *,
    production: bool = False,
) -> FacturaResponse:
    """Emit a factura · auto-fetches CAE."""
    auth = await afip.get_auth()
    url = WSFE_URL_PROD if production else WSFE_URL_HOMO

    # If cbte_desde=0 · query last consumed number
    if factura.cbte_desde == 0:
        last = await _last_cbte_nro(url, auth, factura.pto_vta, factura.cbte_tipo)
        factura.cbte_desde = last + 1
        factura.cbte_hasta = factura.cbte_desde

    body = _build_fecae_envelope(auth, factura)
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            url,
            content=body,
            headers={"Content-Type": "text/xml; charset=UTF-8", "SOAPAction": "http://ar.gov.afip.dif.FEV1/FECAESolicitar"},
        )
        r.raise_for_status()

    return _parse_fecae_response(r.text, factura.cbte_desde)


async def _last_cbte_nro(url: str, auth, pto_vta: int, cbte_tipo: int) -> int:
    """FECompUltimoAutorizado · returns last consumed number for (PtoVta, CbteTipo)."""
    body = f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ar="http://ar.gov.afip.dif.FEV1/">
  <soap:Body>
    <ar:FECompUltimoAutorizado>
      <ar:Auth>
        <ar:Token>{auth.token}</ar:Token>
        <ar:Sign>{auth.sign}</ar:Sign>
        <ar:Cuit>{auth.cuit}</ar:Cuit>
      </ar:Auth>
      <ar:PtoVta>{pto_vta}</ar:PtoVta>
      <ar:CbteTipo>{cbte_tipo}</ar:CbteTipo>
    </ar:FECompUltimoAutorizado>
  </soap:Body>
</soap:Envelope>"""

    async with httpx.AsyncClient(timeout=15.0) as client:
        r = await client.post(url, content=body, headers={"Content-Type": "text/xml; charset=UTF-8", "SOAPAction": "http://ar.gov.afip.dif.FEV1/FECompUltimoAutorizado"})
        r.raise_for_status()
    # Extract CbteNro from response (minimal regex parse)
    import re
    m = re.search(r"<CbteNro>(\d+)</CbteNro>", r.text)
    return int(m.group(1)) if m else 0


def _build_fecae_envelope(auth, f: FacturaRequest) -> str:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ar="http://ar.gov.afip.dif.FEV1/">
  <soap:Body>
    <ar:FECAESolicitar>
      <ar:Auth>
        <ar:Token>{auth.token}</ar:Token>
        <ar:Sign>{auth.sign}</ar:Sign>
        <ar:Cuit>{auth.cuit}</ar:Cuit>
      </ar:Auth>
      <ar:FeCAEReq>
        <ar:FeCabReq>
          <ar:CantReg>1</ar:CantReg>
          <ar:PtoVta>{f.pto_vta}</ar:PtoVta>
          <ar:CbteTipo>{f.cbte_tipo}</ar:CbteTipo>
        </ar:FeCabReq>
        <ar:FeDetReq>
          <ar:FECAEDetRequest>
            <ar:Concepto>{f.concepto}</ar:Concepto>
            <ar:DocTipo>{f.doc_tipo}</ar:DocTipo>
            <ar:DocNro>{f.doc_nro}</ar:DocNro>
            <ar:CbteDesde>{f.cbte_desde}</ar:CbteDesde>
            <ar:CbteHasta>{f.cbte_hasta}</ar:CbteHasta>
            <ar:CbteFch>{f.cbte_fch}</ar:CbteFch>
            <ar:ImpTotal>{f.imp_total}</ar:ImpTotal>
            <ar:ImpTotConc>0</ar:ImpTotConc>
            <ar:ImpNeto>{f.imp_neto}</ar:ImpNeto>
            <ar:ImpOpEx>0</ar:ImpOpEx>
            <ar:ImpIVA>{f.imp_iva}</ar:ImpIVA>
            <ar:ImpTrib>{f.imp_trib}</ar:ImpTrib>
            <ar:MonId>{f.moneda_id}</ar:MonId>
            <ar:MonCotiz>{f.moneda_cotiz}</ar:MonCotiz>
          </ar:FECAEDetRequest>
        </ar:FeDetReq>
      </ar:FeCAEReq>
    </ar:FECAESolicitar>
  </soap:Body>
</soap:Envelope>"""


def _parse_fecae_response(soap_xml: str, cbte_nro: int) -> FacturaResponse:
    """Minimal parsing · production should use xmltodict/lxml."""
    import re
    cae_m = re.search(r"<CAE>(\d+)</CAE>", soap_xml)
    vto_m = re.search(r"<CAEFchVto>(\d+)</CAEFchVto>", soap_xml)
    res_m = re.search(r"<Resultado>([AR])</Resultado>", soap_xml)
    obs = re.findall(r"<Msg>([^<]+)</Msg>", soap_xml)
    return FacturaResponse(
        cae=cae_m.group(1) if cae_m else "",
        cae_fch_vto=vto_m.group(1) if vto_m else "",
        cbte_nro=cbte_nro,
        resultado=res_m.group(1) if res_m else "?",
        observaciones=obs,
    )
